"""
Risk Engine — conftest.py
Shared fixtures for the Risk Engine test suite.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock


# ── Known volatility factor for deterministic tests ───────────────────────────
# By patching _get_live_volatility_factor(), we remove all randomness
# and make every test assertion 100% deterministic.
FIXED_VOLATILITY_FACTOR = 0.0035


@pytest_asyncio.fixture
async def async_client():
    """
    Async HTTPX test client against the Risk Engine FastAPI app.
    The lifespan is handled automatically by the ASGITransport context.
    """
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def fixed_volatility(mocker):
    """
    Patches the volatility factor to a fixed value, eliminating
    random Gaussian jitter from all calculation tests.
    """
    return mocker.patch(
        "app.engine.calculator._get_live_volatility_factor",
        return_value=FIXED_VOLATILITY_FACTOR,
    )


@pytest.fixture
def known_calculation_params():
    """
    Returns a dict of input parameters whose expected output can be
    computed precisely given FIXED_VOLATILITY_FACTOR = 0.0035.
    """
    return {
        "transaction_id": "test-calc-001",
        "transaction_amount": 10_000.0,
        "transaction_type": "TRADE",  # amplifier = 1.8
        # Expected:
        # raw_score   = 10000 * 0.0035 * 1.8 = 63.0
        # risk_score  = (63.0 / 35000.0) * 100 = 0.18  → 0.18
        # Wait: SCORE_NORMALIZATION_DIVISOR = 35000.0
        # risk_score = (63.0 / 35000.0) * 100 = 0.18
        "expected_raw_score": 63.0,
        "expected_risk_score": pytest.approx(0.18, abs=0.01),
    }
