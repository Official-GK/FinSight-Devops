"""
Risk Engine - Main Application Entry Point
"""
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.config import get_settings
from app.logging_config import configure_logging, get_logger
from app.models import RiskCalculationRequest, RiskCalculationResponse, HealthResponse
from app.engine.calculator import calculate_risk_score
from app.metrics import (
    CALCULATIONS_TOTAL,
    CALCULATION_DURATION,
    RISK_SCORE_OUTPUT,
    ACTIVE_CALCULATIONS,
    CALCULATION_ERRORS,
    VOLATILITY_FACTOR_GAUGE,
)

configure_logging()

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "risk_engine_starting",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        market_volatility_factor=settings.MARKET_VOLATILITY_FACTOR,
    )
    VOLATILITY_FACTOR_GAUGE.set(settings.MARKET_VOLATILITY_FACTOR)
    yield
    logger.info("risk_engine_shutdown_complete")


app = FastAPI(
    title="Financial Risk Engine",
    description=(
        "Internal microservice that performs CPU-intensive risk score calculations "
        "for financial transactions using market volatility factors."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)

    start = time.perf_counter()
    response: Response = await call_next(request)
    duration = time.perf_counter() - start

    logger.info(
        "request_processed",
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.post(
    "/calculate",
    response_model=RiskCalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate Risk Score",
    description="Computes a risk score for a given transaction using market volatility data.",
    tags=["Risk Calculation"],
)
async def calculate_risk(
    request: Request,
    payload: RiskCalculationRequest,
) -> RiskCalculationResponse:
    """
    Core risk calculation endpoint.

    Algorithm:
        raw_score  = amount × market_volatility_factor × type_amplifier
        risk_score = (raw_score / normalization_divisor) × 100
    """
    structlog.contextvars.bind_contextvars(
        transaction_id=payload.transaction_id,
        amount=payload.transaction_amount,
        transaction_type=payload.transaction_type,
    )

    log = logger.bind(transaction_id=payload.transaction_id)
    log.info("risk_calculation_started")

    ACTIVE_CALCULATIONS.inc()
    calc_start = time.perf_counter()

    try:
        result = await calculate_risk_score(
            transaction_id=payload.transaction_id,
            transaction_amount=payload.transaction_amount,
            transaction_type=payload.transaction_type,
        )
    except Exception as exc:
        CALCULATION_ERRORS.labels(error_type=type(exc).__name__).inc()
        log.error("risk_calculation_failed", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Calculation failed", "detail": "An internal calculation error occurred."},
        )
    finally:
        ACTIVE_CALCULATIONS.dec()

    calc_duration = time.perf_counter() - calc_start

    # Record metrics
    CALCULATIONS_TOTAL.labels(transaction_type=payload.transaction_type).inc()
    CALCULATION_DURATION.observe(calc_duration)
    RISK_SCORE_OUTPUT.observe(result["risk_score"])
    VOLATILITY_FACTOR_GAUGE.set(result["market_volatility_factor"])

    log.info(
        "risk_calculation_completed",
        risk_score=result["risk_score"],
        computation_time_ms=result["computation_time_ms"],
    )

    return RiskCalculationResponse(**result)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Operations"],
    summary="Health Check",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/", include_in_schema=False)
async def root():
    return {"service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )
