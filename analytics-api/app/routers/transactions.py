"""
Analytics API - Transactions Router
Core business logic endpoint for transaction risk analysis.
"""
import time
import uuid
import structlog
from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse

import httpx

from app.models import (
    TransactionRequest,
    AnalysisResponse,
    ErrorResponse,
    RiskLevel,
)
from app.risk_engine_client import RiskEngineClient
from app.metrics import (
    TRANSACTIONS_ANALYZED,
    RISK_SCORE_HISTOGRAM,
    TRANSACTION_AMOUNT_HISTOGRAM,
)
from app.config import get_settings, Settings

router = APIRouter(prefix="/api/v1", tags=["Transactions"])
logger = structlog.get_logger(__name__)


def _classify_risk(score: float) -> RiskLevel:
    """Classify a numerical risk score into a risk level bucket."""
    if score < 20:
        return RiskLevel.LOW
    elif score < 50:
        return RiskLevel.MEDIUM
    elif score < 80:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Transaction Risk",
    description=(
        "Accepts a financial transaction payload, forwards it to the Risk Engine, "
        "and returns a calculated risk score along with a risk classification."
    ),
    responses={
        200: {"description": "Risk analysis completed successfully"},
        422: {"description": "Validation error in the request payload"},
        503: {"description": "Risk Engine is unavailable"},
        504: {"description": "Risk Engine timed out"},
    },
)
async def analyze_transaction(
    request: Request,
    payload: TransactionRequest,
    settings: Settings = Depends(get_settings),
) -> AnalysisResponse:
    """
    Main transaction analysis endpoint.

    Flow:
    1. Validate incoming payload (Pydantic handles this automatically)
    2. Attach a unique transaction ID for distributed tracing
    3. Forward payload to Risk Engine via resilient HTTP client
    4. Classify the returned risk score
    5. Record all metrics and return structured response
    """
    from app.in_memory_db import db
    seq = db.get_next_transaction_id()
    transaction_id = payload.transaction_id or f"TXN-{seq:06d}"

    # Bind context variables for structured logging throughout this request
    structlog.contextvars.bind_contextvars(
        transaction_id=transaction_id,
        amount=payload.amount,
        transaction_type=payload.transaction_type.value,
        currency=payload.currency,
    )

    log = logger.bind(transaction_id=transaction_id)
    log.info("transaction_analysis_started")

    # Record transaction amount in histogram
    TRANSACTION_AMOUNT_HISTOGRAM.observe(payload.amount)

    # Call Risk Engine
    client = RiskEngineClient()
    engine_start = time.perf_counter()

    try:
        engine_response = await client.calculate_risk(
            transaction_id=transaction_id,
            amount=payload.amount,
            transaction_type=payload.transaction_type.value,
            currency=payload.currency,
        )
    except httpx.TimeoutException:
        log.error("risk_engine_timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error": "Risk Engine timeout",
                "transaction_id": transaction_id,
                "message": "The Risk Engine did not respond within the allowed window.",
            },
        )
    except httpx.RequestError as exc:
        log.error("risk_engine_unavailable", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Risk Engine unavailable",
                "transaction_id": transaction_id,
                "message": "Unable to reach the Risk Engine. Please try again later.",
            },
        )

    engine_latency_ms = (time.perf_counter() - engine_start) * 1000

    # Parse score from Risk Engine response
    risk_score: float = engine_response.get("risk_score", 0.0)
    risk_level = _classify_risk(risk_score)

    # Record business metrics
    TRANSACTIONS_ANALYZED.labels(
        transaction_type=payload.transaction_type.value,
        risk_level=risk_level.value,
    ).inc()
    RISK_SCORE_HISTOGRAM.observe(risk_score)

    log.info(
        "transaction_analysis_completed",
        risk_score=risk_score,
        risk_level=risk_level.value,
        engine_latency_ms=round(engine_latency_ms, 2),
    )

    structlog.contextvars.unbind_contextvars(
        "transaction_id", "amount", "transaction_type", "currency"
    )

    from app.in_memory_db import db
    from app.database import save_transaction
    
    response = AnalysisResponse(
        transaction_id=transaction_id,
        risk_score=round(risk_score, 4),
        risk_level=risk_level,
        amount=payload.amount,
        transaction_type=payload.transaction_type,
        currency=payload.currency,
        engine_latency_ms=round(engine_latency_ms, 2),
        message=f"Transaction analyzed. Risk level: {risk_level.value}",
    )
    
    db.record_transaction(response)
    
    # Persist to database
    await save_transaction(
        tx_id=transaction_id,
        amount=payload.amount,
        currency=payload.currency,
        tx_type=payload.transaction_type.value,
        risk_score=risk_score,
        risk_level=risk_level.value
    )
    
    return response
