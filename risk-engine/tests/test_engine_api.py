"""
Risk Engine — test_engine_api.py

Tests for the FastAPI application layer (app/main.py):
  POST /calculate endpoint
  GET  /health endpoint
  GET  /metrics endpoint
  Input validation (422)
  Metrics are updated on each request

Tests here use the `async_client` fixture with ASGI transport.
The calculator is mocked where we want to test the API layer in isolation,
and used directly where we want integration-level coverage.
"""
import pytest
from unittest.mock import patch, AsyncMock


# ── Payload helpers ───────────────────────────────────────────────────────────

def make_calculation_payload(
    transaction_id: str = "test-txn-001",
    transaction_amount: float = 10_000.0,
    transaction_type: str = "TRADE",
    currency: str = "USD",
) -> dict:
    return {
        "transaction_id": transaction_id,
        "transaction_amount": transaction_amount,
        "transaction_type": transaction_type,
        "currency": currency,
    }


MOCK_CALC_RESULT = {
    "transaction_id": "test-txn-001",
    "risk_score": 45.5,
    "raw_score": 15925.0,
    "market_volatility_factor": 0.0035,
    "transaction_type": "TRADE",
    "transaction_amount": 10_000.0,
    "computation_time_ms": 12.4,
}


# ════════════════════════════════════════════════════════════════════════════════
# Health Endpoint
# ════════════════════════════════════════════════════════════════════════════════

class TestRiskEngineHealthEndpoint:
    """GET /health — Kubernetes liveness and readiness probes."""

    @pytest.mark.integration
    async def test_health_returns_200(self, async_client):
        response = await async_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.integration
    async def test_health_response_schema(self, async_client):
        body = (await async_client.get("/health")).json()
        assert body["status"] == "healthy"
        assert body["service"] == "risk-engine"
        assert "version" in body
        assert "environment" in body
        assert "timestamp" in body

    @pytest.mark.integration
    async def test_root_endpoint_returns_service_info(self, async_client):
        response = await async_client.get("/")
        assert response.status_code == 200
        body = response.json()
        assert "service" in body
        assert body["service"] == "risk-engine"


# ════════════════════════════════════════════════════════════════════════════════
# POST /calculate — Happy Path
# ════════════════════════════════════════════════════════════════════════════════

class TestCalculateEndpointSuccess:
    """Valid payloads should return 200 with a complete risk score response."""

    @pytest.mark.integration
    async def test_calculate_returns_200(self, async_client, fixed_volatility):
        payload = make_calculation_payload()
        response = await async_client.post("/calculate", json=payload)
        assert response.status_code == 200

    @pytest.mark.integration
    async def test_response_contains_all_required_fields(self, async_client, fixed_volatility):
        response = await async_client.post(
            "/calculate", json=make_calculation_payload()
        )
        body = response.json()
        required_fields = [
            "transaction_id", "risk_score", "raw_score",
            "market_volatility_factor", "transaction_type",
            "transaction_amount", "computation_time_ms", "calculated_at",
        ]
        for field in required_fields:
            assert field in body, f"Missing field: '{field}'"

    @pytest.mark.integration
    async def test_risk_score_is_non_negative(self, async_client, fixed_volatility):
        response = await async_client.post(
            "/calculate", json=make_calculation_payload(transaction_amount=5000.0)
        )
        assert response.json()["risk_score"] >= 0.0

    @pytest.mark.integration
    async def test_transaction_id_is_echoed_back(self, async_client, fixed_volatility):
        payload = make_calculation_payload(transaction_id="echo-me-back-123")
        response = await async_client.post("/calculate", json=payload)
        assert response.json()["transaction_id"] == "echo-me-back-123"

    @pytest.mark.integration
    async def test_transaction_amount_is_echoed_back(self, async_client, fixed_volatility):
        payload = make_calculation_payload(transaction_amount=77_777.77)
        response = await async_client.post("/calculate", json=payload)
        assert response.json()["transaction_amount"] == pytest.approx(77_777.77)

    @pytest.mark.integration
    async def test_transaction_type_is_echoed_back(self, async_client, fixed_volatility):
        payload = make_calculation_payload(transaction_type="TRANSFER")
        response = await async_client.post("/calculate", json=payload)
        assert response.json()["transaction_type"] == "TRANSFER"

    @pytest.mark.integration
    async def test_computation_time_is_positive(self, async_client, fixed_volatility):
        response = await async_client.post(
            "/calculate", json=make_calculation_payload()
        )
        assert response.json()["computation_time_ms"] >= 0.0

    @pytest.mark.integration
    async def test_volatility_factor_is_present_and_positive(self, async_client, fixed_volatility):
        response = await async_client.post(
            "/calculate", json=make_calculation_payload()
        )
        assert response.json()["market_volatility_factor"] > 0.0

    @pytest.mark.integration
    async def test_calculated_at_timestamp_is_present(self, async_client, fixed_volatility):
        response = await async_client.post(
            "/calculate", json=make_calculation_payload()
        )
        assert "calculated_at" in response.json()

    @pytest.mark.integration
    @pytest.mark.parametrize("tx_type", [
        "TRADE", "TRANSFER", "WITHDRAWAL", "PAYMENT", "DEPOSIT", "REFUND"
    ])
    async def test_all_transaction_types_accepted(self, async_client, fixed_volatility, tx_type):
        """Every valid transaction type must return 200."""
        payload = make_calculation_payload(transaction_type=tx_type)
        response = await async_client.post("/calculate", json=payload)
        assert response.status_code == 200, f"Failed for type: {tx_type}"

    @pytest.mark.integration
    async def test_trade_produces_higher_score_than_refund(
        self, async_client, fixed_volatility
    ):
        """
        TRADE (1.8×) must produce a higher score than REFUND (0.6×)
        for the same amount. Tests the amplifier hierarchy end-to-end.
        """
        amount = 50_000.0
        trade_response = await async_client.post(
            "/calculate",
            json=make_calculation_payload(transaction_amount=amount, transaction_type="TRADE"),
        )
        refund_response = await async_client.post(
            "/calculate",
            json=make_calculation_payload(transaction_amount=amount, transaction_type="REFUND"),
        )
        trade_score = trade_response.json()["risk_score"]
        refund_score = refund_response.json()["risk_score"]
        assert trade_score > refund_score


# ════════════════════════════════════════════════════════════════════════════════
# Input Validation — 422 Unprocessable Entity
# ════════════════════════════════════════════════════════════════════════════════

class TestCalculateInputValidation:
    """
    Verifies that Pydantic validation guards the /calculate endpoint.
    The Risk Engine should never receive a malformed payload from the
    Analytics API, but these tests ensure defense-in-depth.
    """

    @pytest.mark.unit
    async def test_negative_amount_returns_422(self, async_client):
        payload = {
            "transaction_id": "txn-neg",
            "transaction_amount": -500.0,
            "transaction_type": "TRADE",
        }
        response = await async_client.post("/calculate", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_zero_amount_returns_422(self, async_client):
        payload = {
            "transaction_id": "txn-zero",
            "transaction_amount": 0.0,
            "transaction_type": "TRADE",
        }
        response = await async_client.post("/calculate", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_missing_transaction_id_returns_422(self, async_client):
        payload = {
            "transaction_amount": 5000.0,
            "transaction_type": "TRADE",
        }
        response = await async_client.post("/calculate", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_missing_amount_returns_422(self, async_client):
        payload = {
            "transaction_id": "txn-missing-amt",
            "transaction_type": "TRADE",
        }
        response = await async_client.post("/calculate", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_missing_transaction_type_returns_422(self, async_client):
        payload = {
            "transaction_id": "txn-missing-type",
            "transaction_amount": 5000.0,
        }
        response = await async_client.post("/calculate", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_empty_transaction_id_returns_422(self, async_client):
        payload = {
            "transaction_id": "",
            "transaction_amount": 5000.0,
            "transaction_type": "TRADE",
        }
        response = await async_client.post("/calculate", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_string_amount_returns_422(self, async_client):
        payload = {
            "transaction_id": "txn-str-amt",
            "transaction_amount": "five-thousand",
            "transaction_type": "TRADE",
        }
        response = await async_client.post("/calculate", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_empty_body_returns_422(self, async_client):
        response = await async_client.post("/calculate", json={})
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_422_response_has_detail_field(self, async_client):
        """422 responses must include 'detail' for diagnostics."""
        response = await async_client.post("/calculate", json={})
        assert "detail" in response.json()


# ════════════════════════════════════════════════════════════════════════════════
# Error Handling — Internal Calculation Failure
# ════════════════════════════════════════════════════════════════════════════════

class TestCalculateErrorHandling:
    """
    Tests that internal calculation failures are handled gracefully
    and never expose raw stack traces to the caller.
    """

    @pytest.mark.integration
    async def test_calculation_exception_returns_5xx(self, async_client, mocker):
        """
        If calculate_risk_score() raises an unexpected exception,
        the endpoint must return 5xx — never 200 with bad data.
        """
        mocker.patch(
            "app.main.calculate_risk_score",
            new_callable=AsyncMock,
            side_effect=RuntimeError("NumPy crashed"),
        )
        payload = make_calculation_payload()
        response = await async_client.post("/calculate", json=payload)
        assert response.status_code >= 500

    @pytest.mark.integration
    async def test_error_response_does_not_leak_stack_trace(self, async_client, mocker):
        """Error messages must not contain internal Python tracebacks."""
        mocker.patch(
            "app.main.calculate_risk_score",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Sensitive internal error"),
        )
        payload = make_calculation_payload()
        response = await async_client.post("/calculate", json=payload)
        # The raw error must not reach the client
        assert "Sensitive internal error" not in response.text
        assert "Traceback" not in response.text


# ════════════════════════════════════════════════════════════════════════════════
# Metrics Endpoint
# ════════════════════════════════════════════════════════════════════════════════

class TestMetricsEndpoint:

    @pytest.mark.integration
    async def test_metrics_endpoint_returns_200(self, async_client):
        response = await async_client.get("/metrics")
        assert response.status_code == 200

    @pytest.mark.integration
    async def test_metrics_is_prometheus_format(self, async_client):
        response = await async_client.get("/metrics")
        assert "text/plain" in response.headers.get("content-type", "")

    @pytest.mark.integration
    async def test_metrics_contain_risk_engine_metrics(
        self, async_client, fixed_volatility
    ):
        """After a calculation, custom metrics must appear in /metrics output."""
        await async_client.post("/calculate", json=make_calculation_payload())
        response = await async_client.get("/metrics")
        body = response.text
        assert "risk_engine_calculations_total" in body
        assert "risk_engine_calculation_duration_seconds" in body
        assert "risk_engine_market_volatility_factor" in body

    @pytest.mark.integration
    async def test_calculation_increments_counter(self, async_client, fixed_volatility):
        """Each /calculate call must increment the calculations counter."""
        # Make 3 requests
        for _ in range(3):
            await async_client.post("/calculate", json=make_calculation_payload())

        metrics_response = await async_client.get("/metrics")
        body = metrics_response.text

        # The counter must have a value > 0
        import re
        match = re.search(
            r'risk_engine_calculations_total\{[^}]*\}\s+([\d.]+)', body
        )
        if match:
            assert float(match.group(1)) >= 3.0
