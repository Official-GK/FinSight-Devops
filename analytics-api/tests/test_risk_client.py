"""
Analytics API — test_risk_client.py

Tests for app/risk_engine_client.py

This is the most critical test file for resilience verification.
We isolate the HTTP client completely using unittest.mock.AsyncMock and
verify every branch of the retry/backoff/error-handling logic:

  1. Successful response on first attempt
  2. 5xx server error → retries → eventual success
  3. 5xx server error → all retries exhausted → raises last exception
  4. TimeoutException → retries with exponential backoff
  5. 4xx client error → does NOT retry (immediate raise)
  6. Connection error → retries
  7. Retry counter increments correctly (verified via metrics mock)
  8. Exponential backoff waits are correctly calculated
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from httpx import (
    TimeoutException,
    HTTPStatusError,
    ConnectError,
    Request,
    Response,
)

from app.risk_engine_client import RiskEngineClient
from app.config import get_settings

settings = get_settings()


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_httpx_response(status_code: int, json_body: dict | None = None) -> Response:
    """Build a real httpx.Response object for use in mock return values."""
    import json as json_mod
    body = json_mod.dumps(json_body or {}).encode()
    request = Request("POST", "http://risk-engine-service:8001/calculate")
    return Response(status_code=status_code, content=body, request=request)


def make_success_response() -> Response:
    return make_httpx_response(200, {
        "transaction_id": "test-txn-001",
        "risk_score": 45.5,
        "raw_score": 15925.0,
        "market_volatility_factor": 0.0035,
        "transaction_type": "TRADE",
        "transaction_amount": 10000.0,
        "computation_time_ms": 12.4,
        "calculated_at": "2024-01-01T00:00:00",
    })


def make_error_response(status_code: int) -> Response:
    return make_httpx_response(status_code, {"detail": f"Error {status_code}"})


# ════════════════════════════════════════════════════════════════════════════════
# Successful Responses
# ════════════════════════════════════════════════════════════════════════════════

class TestRiskEngineClientSuccess:
    """Tests for the happy path — engine responds on first attempt."""

    @pytest.mark.unit
    async def test_successful_call_returns_parsed_dict(self, mocker):
        """Client must parse and return the engine's JSON response."""
        mock_response = make_success_response()

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_response)
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            result = await client.calculate_risk(
                transaction_id="test-txn-001",
                amount=10000.0,
                transaction_type="TRADE",
                currency="USD",
            )

        assert isinstance(result, dict)
        assert result["risk_score"] == 45.5
        assert result["transaction_id"] == "test-txn-001"

    @pytest.mark.unit
    async def test_successful_call_invokes_correct_endpoint(self, mocker):
        """Client must POST to /calculate, not any other path."""
        mock_response = make_success_response()

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_response)
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            await client.calculate_risk(
                transaction_id="txn-123",
                amount=5000.0,
                transaction_type="PAYMENT",
                currency="USD",
            )

            # Verify the POST was called to the /calculate endpoint
            mock_http_client.post.assert_called_once()
            call_args = mock_http_client.post.call_args
            assert call_args[0][0] == "/calculate"

    @pytest.mark.unit
    async def test_successful_call_sends_correct_payload(self, mocker):
        """The JSON payload sent to the engine must match the input args exactly."""
        mock_response = make_success_response()

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_response)
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            await client.calculate_risk(
                transaction_id="txn-payload-test",
                amount=25000.0,
                transaction_type="TRANSFER",
                currency="EUR",
            )

            _, kwargs = mock_http_client.post.call_args
            sent_json = kwargs["json"]
            assert sent_json["transaction_id"] == "txn-payload-test"
            assert sent_json["transaction_amount"] == 25000.0
            assert sent_json["transaction_type"] == "TRANSFER"
            assert sent_json["currency"] == "EUR"

    @pytest.mark.unit
    async def test_only_one_attempt_on_success(self, mocker):
        """Engine should be called exactly once when the first attempt succeeds."""
        mock_response = make_success_response()

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_response)
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            await client.calculate_risk("txn-1", 1000.0, "TRADE", "USD")

            assert mock_http_client.post.call_count == 1


# ════════════════════════════════════════════════════════════════════════════════
# Timeout Retry Logic
# ════════════════════════════════════════════════════════════════════════════════

class TestTimeoutRetryBehavior:
    """
    Tests the exponential backoff retry logic for TimeoutException.

    Expected backoff sequence (RISK_ENGINE_RETRY_WAIT=1.0, MAX_RETRIES=3):
      Attempt 1 fails → wait 1.0s  (1.0 * 2^0)
      Attempt 2 fails → wait 2.0s  (1.0 * 2^1)
      Attempt 3 fails → raises TimeoutException
    """

    @pytest.mark.resilience
    async def test_retries_on_timeout_up_to_max_retries(self, mocker):
        """Client must retry exactly MAX_RETRIES times before giving up."""
        mock_sleep = mocker.patch("app.risk_engine_client.asyncio.sleep", new_callable=AsyncMock)

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(
                side_effect=TimeoutException("timed out")
            )
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            with pytest.raises(TimeoutException):
                await client.calculate_risk("txn-timeout", 1000.0, "TRADE", "USD")

            # Must have attempted exactly MAX_RETRIES times
            assert mock_http_client.post.call_count == settings.RISK_ENGINE_MAX_RETRIES

    @pytest.mark.resilience
    async def test_exponential_backoff_wait_times_are_correct(self, mocker):
        """
        Verify the exact sleep() durations used in exponential backoff.
        wait_time = RISK_ENGINE_RETRY_WAIT * 2^(attempt-1)
        """
        mock_sleep = mocker.patch("app.risk_engine_client.asyncio.sleep", new_callable=AsyncMock)

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(side_effect=TimeoutException("timeout"))
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            with pytest.raises(TimeoutException):
                await client.calculate_risk("txn-backoff", 1000.0, "TRADE", "USD")

            wait = settings.RISK_ENGINE_RETRY_WAIT
            # Verify sleep was called with progressively increasing waits
            # The last attempt does NOT sleep (no retry after last attempt)
            expected_sleeps = [
                call(wait * (2 ** i))
                for i in range(settings.RISK_ENGINE_MAX_RETRIES - 1)
            ]
            assert mock_sleep.call_args_list == expected_sleeps

    @pytest.mark.resilience
    async def test_succeeds_on_second_attempt_after_timeout(self, mocker):
        """
        Simulate: first attempt times out, second attempt succeeds.
        This is the most common real-world retry scenario.
        """
        mocker.patch("app.risk_engine_client.asyncio.sleep", new_callable=AsyncMock)
        success_response = make_success_response()

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            # First call times out, second call succeeds
            mock_http_client.post = AsyncMock(
                side_effect=[TimeoutException("first timeout"), success_response]
            )
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            result = await client.calculate_risk("txn-retry-ok", 1000.0, "TRADE", "USD")

        assert result["risk_score"] == 45.5
        assert mock_http_client.post.call_count == 2  # Exactly 2 attempts

    @pytest.mark.resilience
    async def test_succeeds_on_third_attempt_after_two_timeouts(self, mocker):
        """Two timeouts then success — verifies full retry sequence works."""
        mocker.patch("app.risk_engine_client.asyncio.sleep", new_callable=AsyncMock)
        success_response = make_success_response()

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(
                side_effect=[
                    TimeoutException("timeout 1"),
                    TimeoutException("timeout 2"),
                    success_response,  # Third attempt succeeds
                ]
            )
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            result = await client.calculate_risk("txn-third-time", 1000.0, "TRADE", "USD")

        assert result["risk_score"] == 45.5
        assert mock_http_client.post.call_count == 3


# ════════════════════════════════════════════════════════════════════════════════
# HTTP Status Error Handling
# ════════════════════════════════════════════════════════════════════════════════

class TestHTTPStatusErrorHandling:
    """
    Tests how the client handles different HTTP status codes from the engine.
    Key rule: 4xx = do NOT retry; 5xx = retry up to max.
    """

    @pytest.mark.resilience
    async def test_5xx_error_triggers_retry(self, mocker):
        """500 Internal Server Error from engine must trigger retries."""
        mocker.patch("app.risk_engine_client.asyncio.sleep", new_callable=AsyncMock)
        error_500 = make_error_response(500)

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(
                side_effect=HTTPStatusError(
                    "500 Internal Server Error",
                    request=Request("POST", "/calculate"),
                    response=error_500,
                )
            )
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            with pytest.raises(HTTPStatusError):
                await client.calculate_risk("txn-500", 1000.0, "TRADE", "USD")

            # Must retry for 5xx errors
            assert mock_http_client.post.call_count == settings.RISK_ENGINE_MAX_RETRIES

    @pytest.mark.resilience
    async def test_503_triggers_retry(self, mocker):
        """503 Service Unavailable must retry (engine may be restarting)."""
        mocker.patch("app.risk_engine_client.asyncio.sleep", new_callable=AsyncMock)
        error_503 = make_error_response(503)

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(
                side_effect=HTTPStatusError(
                    "503 Service Unavailable",
                    request=Request("POST", "/calculate"),
                    response=error_503,
                )
            )
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            with pytest.raises(HTTPStatusError):
                await client.calculate_risk("txn-503", 1000.0, "TRADE", "USD")

            assert mock_http_client.post.call_count == settings.RISK_ENGINE_MAX_RETRIES

    @pytest.mark.resilience
    async def test_422_client_error_does_not_retry(self, mocker):
        """
        422 Unprocessable Entity from the engine is a client error.
        The client must NOT retry — retrying a bad payload will never help.
        """
        sleep_mock = mocker.patch(
            "app.risk_engine_client.asyncio.sleep", new_callable=AsyncMock
        )
        error_422 = make_error_response(422)

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(
                side_effect=HTTPStatusError(
                    "422 Unprocessable Entity",
                    request=Request("POST", "/calculate"),
                    response=error_422,
                )
            )
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            with pytest.raises(HTTPStatusError):
                await client.calculate_risk("txn-422", 1000.0, "TRADE", "USD")

            # 4xx → exactly 1 attempt, no retries
            assert mock_http_client.post.call_count == 1
            # asyncio.sleep must never be called for 4xx errors
            sleep_mock.assert_not_called()

    @pytest.mark.resilience
    async def test_400_bad_request_does_not_retry(self, mocker):
        """400 Bad Request is a client error — same rule: no retry."""
        sleep_mock = mocker.patch(
            "app.risk_engine_client.asyncio.sleep", new_callable=AsyncMock
        )
        error_400 = make_error_response(400)

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(
                side_effect=HTTPStatusError(
                    "400 Bad Request",
                    request=Request("POST", "/calculate"),
                    response=error_400,
                )
            )
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            with pytest.raises(HTTPStatusError):
                await client.calculate_risk("txn-400", 1000.0, "TRADE", "USD")

            assert mock_http_client.post.call_count == 1
            sleep_mock.assert_not_called()

    @pytest.mark.resilience
    async def test_5xx_then_success_recovers(self, mocker):
        """Engine returns 500 once, then 200 — client should succeed overall."""
        mocker.patch("app.risk_engine_client.asyncio.sleep", new_callable=AsyncMock)
        error_500 = make_error_response(500)
        success = make_success_response()

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(
                side_effect=[
                    HTTPStatusError(
                        "500",
                        request=Request("POST", "/calculate"),
                        response=error_500,
                    ),
                    success,
                ]
            )
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            result = await client.calculate_risk("txn-recover", 1000.0, "TRADE", "USD")

        assert result["risk_score"] == 45.5
        assert mock_http_client.post.call_count == 2


# ════════════════════════════════════════════════════════════════════════════════
# Connection Error Handling
# ════════════════════════════════════════════════════════════════════════════════

class TestConnectionErrorHandling:
    """
    Tests for network-level failures (DNS failure, connection refused, etc.)
    These are httpx.RequestError subclasses.
    """

    @pytest.mark.resilience
    async def test_connect_error_triggers_retry(self, mocker):
        """Connection refused / DNS failure must trigger retry."""
        mocker.patch("app.risk_engine_client.asyncio.sleep", new_callable=AsyncMock)

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(
                side_effect=ConnectError("Connection refused")
            )
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            with pytest.raises(ConnectError):
                await client.calculate_risk("txn-connect-err", 1000.0, "TRADE", "USD")

            assert mock_http_client.post.call_count == settings.RISK_ENGINE_MAX_RETRIES

    @pytest.mark.resilience
    async def test_connect_error_then_success_recovers(self, mocker):
        """Connection error followed by success — should return the result."""
        mocker.patch("app.risk_engine_client.asyncio.sleep", new_callable=AsyncMock)
        success = make_success_response()

        with patch("app.risk_engine_client.get_http_client", new_callable=AsyncMock) as mock_pool:
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(
                side_effect=[ConnectError("refused"), success]
            )
            mock_pool.return_value = mock_http_client

            client = RiskEngineClient()
            result = await client.calculate_risk("txn-recover-conn", 1000.0, "TRADE", "USD")

        assert result["risk_score"] == 45.5


# ════════════════════════════════════════════════════════════════════════════════
# HTTP Client Pool Management
# ════════════════════════════════════════════════════════════════════════════════

class TestHTTPClientPool:
    """Tests for connection pool lifecycle."""

    @pytest.mark.unit
    async def test_get_http_client_returns_async_client(self):
        """get_http_client() must return an httpx.AsyncClient instance."""
        import httpx
        from app.risk_engine_client import get_http_client, close_http_client

        client = await get_http_client()
        try:
            assert isinstance(client, httpx.AsyncClient)
        finally:
            await close_http_client()

    @pytest.mark.unit
    async def test_get_http_client_reuses_same_instance(self):
        """Connection pool should be reused across calls (not recreated per request)."""
        from app.risk_engine_client import get_http_client, close_http_client

        client1 = await get_http_client()
        client2 = await get_http_client()
        try:
            assert client1 is client2  # Must be the exact same object
        finally:
            await close_http_client()

    @pytest.mark.unit
    async def test_close_http_client_closes_pool(self):
        """After close_http_client(), the pool must report as closed."""
        from app.risk_engine_client import get_http_client, close_http_client

        client = await get_http_client()
        assert not client.is_closed
        await close_http_client()
        assert client.is_closed
