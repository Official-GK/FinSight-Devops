"""
Analytics API - Risk Engine HTTP Client
Resilient async HTTP client with retry logic, circuit-breaking awareness,
connection pooling, and full observability integration.
"""
import asyncio
import time
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging
from app.config import get_settings
from app.logging_config import get_logger
from app.metrics import (
    RISK_ENGINE_CALL_DURATION,
    RISK_ENGINE_ERRORS,
    RISK_ENGINE_RETRIES,
)

logger = get_logger(__name__)
settings = get_settings()

# Shared async client — reused across requests for connection pooling
_http_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url=settings.RISK_ENGINE_URL,
            timeout=httpx.Timeout(
                connect=5.0,
                read=settings.RISK_ENGINE_TIMEOUT,
                write=5.0,
                pool=5.0,
            ),
            limits=httpx.Limits(
                max_connections=settings.HTTP_MAX_CONNECTIONS,
                max_keepalive_connections=settings.HTTP_MAX_KEEPALIVE,
                keepalive_expiry=30,
            ),
            headers={
                "Content-Type": "application/json",
                "X-Service-Name": "analytics-api",
            },
        )
    return _http_client


async def close_http_client() -> None:
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None
        logger.info("risk_engine_client_closed")


class RiskEngineClient:
    """
    Async client for the Risk Engine service.
    Implements retry with exponential backoff and full metrics instrumentation.
    """

    def __init__(self):
        self.settings = settings
        self.logger = get_logger(self.__class__.__name__)

    async def calculate_risk(
        self,
        transaction_id: str,
        amount: float,
        transaction_type: str,
        currency: str,
    ) -> dict:
        """
        Call the Risk Engine /calculate endpoint with retry + backoff.
        Returns the engine's parsed JSON response dict.
        """
        client = await get_http_client()
        payload = {
            "transaction_id": transaction_id,
            "transaction_amount": amount,
            "transaction_type": transaction_type,
            "currency": currency,
        }

        self.logger.info(
            "calling_risk_engine",
            transaction_id=transaction_id,
            amount=amount,
            transaction_type=transaction_type,
        )

        attempt = 0
        last_exc = None
        start_total = time.perf_counter()

        for attempt in range(1, self.settings.RISK_ENGINE_MAX_RETRIES + 1):
            try:
                start = time.perf_counter()
                response = await client.post("/calculate", json=payload)
                elapsed = time.perf_counter() - start

                RISK_ENGINE_CALL_DURATION.observe(elapsed)

                response.raise_for_status()
                result = response.json()

                self.logger.info(
                    "risk_engine_success",
                    transaction_id=transaction_id,
                    attempt=attempt,
                    latency_ms=round(elapsed * 1000, 2),
                )
                return result

            except httpx.TimeoutException as exc:
                last_exc = exc
                RISK_ENGINE_ERRORS.labels(error_type="timeout").inc()
                if attempt < self.settings.RISK_ENGINE_MAX_RETRIES:
                    RISK_ENGINE_RETRIES.inc()
                    wait = self.settings.RISK_ENGINE_RETRY_WAIT * (2 ** (attempt - 1))
                    self.logger.warning(
                        "risk_engine_timeout_retrying",
                        transaction_id=transaction_id,
                        attempt=attempt,
                        retry_in_seconds=wait,
                    )
                    await asyncio.sleep(wait)

            except httpx.HTTPStatusError as exc:
                last_exc = exc
                RISK_ENGINE_ERRORS.labels(error_type=f"http_{exc.response.status_code}").inc()
                self.logger.error(
                    "risk_engine_http_error",
                    transaction_id=transaction_id,
                    status_code=exc.response.status_code,
                    detail=exc.response.text,
                )
                # Don't retry 4xx errors — they are client errors
                if 400 <= exc.response.status_code < 500:
                    raise
                if attempt < self.settings.RISK_ENGINE_MAX_RETRIES:
                    RISK_ENGINE_RETRIES.inc()
                    await asyncio.sleep(self.settings.RISK_ENGINE_RETRY_WAIT)

            except httpx.RequestError as exc:
                last_exc = exc
                RISK_ENGINE_ERRORS.labels(error_type="connection_error").inc()
                self.logger.error(
                    "risk_engine_connection_error",
                    transaction_id=transaction_id,
                    error=str(exc),
                    attempt=attempt,
                )
                if attempt < self.settings.RISK_ENGINE_MAX_RETRIES:
                    RISK_ENGINE_RETRIES.inc()
                    await asyncio.sleep(self.settings.RISK_ENGINE_RETRY_WAIT)

        total_elapsed = time.perf_counter() - start_total
        self.logger.error(
            "risk_engine_all_retries_exhausted",
            transaction_id=transaction_id,
            attempts=attempt,
            total_elapsed_seconds=round(total_elapsed, 3),
        )
        raise last_exc
