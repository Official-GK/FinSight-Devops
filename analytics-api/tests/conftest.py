"""
Analytics API — conftest.py
Shared pytest fixtures used across all test modules.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


# ── Mock Risk Engine Response Factories ──────────────────────────────────────
def make_engine_response(
    risk_score: float = 45.5,
    transaction_id: str = "test-txn-001",
    transaction_amount: float = 10000.0,
    transaction_type: str = "TRADE",
    market_volatility_factor: float = 0.0035,
) -> dict:
    """
    Factory that produces a well-formed Risk Engine response dict.
    Mirrors the shape of RiskCalculationResponse from the Risk Engine.
    """
    return {
        "transaction_id": transaction_id,
        "risk_score": risk_score,
        "raw_score": risk_score * 350.0,
        "market_volatility_factor": market_volatility_factor,
        "transaction_type": transaction_type,
        "transaction_amount": transaction_amount,
        "computation_time_ms": 12.4,
        "calculated_at": "2024-01-01T00:00:00",
    }


# ── Valid Payload Factories ──────────────────────────────────────────────────
def make_transaction_payload(
    amount: float = 10000.0,
    transaction_type: str = "TRADE",
    currency: str = "USD",
    transaction_id: str | None = None,
) -> dict:
    payload = {
        "amount": amount,
        "transaction_type": transaction_type,
        "currency": currency,
    }
    if transaction_id:
        payload["transaction_id"] = transaction_id
    return payload


# ── Application Fixtures ──────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def async_client():
    """
    Async HTTPX client connected to the Analytics API via ASGI transport.

    The risk engine HTTP client pool is patched during lifespan startup
    so tests never make real network calls.
    """
    from app.main import app

    # Patch the HTTP client pool init so lifespan doesn't try to connect
    # to a real Risk Engine on startup
    with patch("app.main.get_http_client", new_callable=AsyncMock) as mock_pool, \
         patch("app.main.close_http_client", new_callable=AsyncMock):
        mock_pool.return_value = AsyncMock()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client


@pytest.fixture
def mock_engine_success(mocker):
    """
    Fixture that patches RiskEngineClient.calculate_risk to return a
    successful response with a known risk score of 45.5.
    Used in endpoint tests where we don't want to test the client itself.
    """
    mock = mocker.patch(
        "app.routers.transactions.RiskEngineClient",
        autospec=True,
    )
    instance = mock.return_value
    instance.calculate_risk = AsyncMock(
        return_value=make_engine_response(risk_score=45.5)
    )
    return instance


@pytest.fixture
def mock_engine_timeout(mocker):
    """Fixture that makes the Risk Engine client raise TimeoutException."""
    import httpx
    mock = mocker.patch(
        "app.routers.transactions.RiskEngineClient",
        autospec=True,
    )
    instance = mock.return_value
    instance.calculate_risk = AsyncMock(
        side_effect=httpx.TimeoutException("Risk engine timed out")
    )
    return instance


@pytest.fixture
def mock_engine_unavailable(mocker):
    """Fixture that makes the Risk Engine client raise a connection error."""
    import httpx
    mock = mocker.patch(
        "app.routers.transactions.RiskEngineClient",
        autospec=True,
    )
    instance = mock.return_value
    instance.calculate_risk = AsyncMock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    return instance
