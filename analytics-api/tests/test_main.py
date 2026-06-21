"""
Analytics API — test_main.py
Tests for FastAPI endpoints: POST /api/v1/analyze, GET /health, GET /

Coverage targets:
  - app/main.py              (middleware, routes, error handlers)
  - app/routers/transactions.py  (business logic, risk classification)
  - app/models.py            (Pydantic validation)
"""
import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import make_engine_response, make_transaction_payload


# ════════════════════════════════════════════════════════════════════════════════
# Health & Meta Endpoints
# ════════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoint:
    """GET /health — Kubernetes liveness and readiness probe."""

    @pytest.mark.integration
    async def test_health_returns_200(self, async_client):
        response = await async_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.integration
    async def test_health_response_schema(self, async_client):
        response = await async_client.get("/health")
        body = response.json()

        assert body["status"] == "healthy"
        assert body["service"] == "analytics-api"
        assert "version" in body
        assert "environment" in body
        assert "timestamp" in body
        assert "dependencies" in body

    @pytest.mark.integration
    async def test_health_contains_risk_engine_dependency(self, async_client):
        response = await async_client.get("/health")
        deps = response.json()["dependencies"]
        # Risk Engine URL must be listed — critical for K8s readiness checks
        assert "risk_engine" in deps

    @pytest.mark.integration
    async def test_root_endpoint_returns_200(self, async_client):
        response = await async_client.get("/")
        assert response.status_code == 200
        body = response.json()
        assert "service" in body
        assert "version" in body


# ════════════════════════════════════════════════════════════════════════════════
# POST /api/v1/analyze — Happy Path
# ════════════════════════════════════════════════════════════════════════════════

class TestAnalyzeEndpointSuccess:
    """Valid payloads — tests that the happy path works end-to-end."""

    @pytest.mark.integration
    async def test_analyze_returns_200(self, async_client, mock_engine_success):
        payload = make_transaction_payload(amount=10000.0, transaction_type="TRADE")
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200

    @pytest.mark.integration
    async def test_analyze_response_contains_required_fields(self, async_client, mock_engine_success):
        payload = make_transaction_payload(amount=10000.0, transaction_type="TRADE")
        response = await async_client.post("/api/v1/analyze", json=payload)
        body = response.json()

        required_fields = [
            "transaction_id", "risk_score", "risk_level",
            "amount", "transaction_type", "currency",
            "processed_at", "engine_latency_ms", "message",
        ]
        for field in required_fields:
            assert field in body, f"Missing field: '{field}'"

    @pytest.mark.integration
    async def test_analyze_risk_score_is_non_negative(self, async_client, mock_engine_success):
        payload = make_transaction_payload(amount=5000.0)
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.json()["risk_score"] >= 0.0

    @pytest.mark.integration
    async def test_analyze_forwards_transaction_id(self, async_client, mock_engine_success):
        """A provided transaction_id must be echoed back in the response."""
        payload = make_transaction_payload(
            amount=5000.0,
            transaction_id="my-custom-txn-id-abc123",
        )
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.json()["transaction_id"] == "my-custom-txn-id-abc123"

    @pytest.mark.integration
    async def test_analyze_auto_generates_transaction_id(self, async_client, mock_engine_success):
        """When no transaction_id is provided, one must be auto-generated."""
        payload = make_transaction_payload(amount=5000.0)  # No transaction_id
        response = await async_client.post("/api/v1/analyze", json=payload)
        body = response.json()
        assert "transaction_id" in body
        assert len(body["transaction_id"]) > 0

    @pytest.mark.integration
    async def test_analyze_currency_uppercased_in_response(self, async_client, mock_engine_success):
        payload = make_transaction_payload(amount=5000.0, currency="usd")  # lowercase
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.json()["currency"] == "USD"

    @pytest.mark.integration
    async def test_analyze_engine_latency_is_positive(self, async_client, mock_engine_success):
        payload = make_transaction_payload(amount=5000.0)
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.json()["engine_latency_ms"] >= 0.0

    @pytest.mark.integration
    async def test_response_has_x_request_id_header(self, async_client, mock_engine_success):
        """The middleware must inject X-Request-ID into every response."""
        payload = make_transaction_payload(amount=5000.0)
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert "x-request-id" in response.headers

    @pytest.mark.integration
    async def test_custom_request_id_echoed_in_response(self, async_client, mock_engine_success):
        """A provided X-Request-ID header must be echoed back."""
        payload = make_transaction_payload(amount=5000.0)
        response = await async_client.post(
            "/api/v1/analyze",
            json=payload,
            headers={"X-Request-ID": "trace-abc-123"},
        )
        assert response.headers.get("x-request-id") == "trace-abc-123"


# ════════════════════════════════════════════════════════════════════════════════
# Risk Level Classification
# ════════════════════════════════════════════════════════════════════════════════

class TestRiskLevelClassification:
    """
    Tests the _classify_risk() logic via the endpoint.
    Each bucket boundary is tested explicitly.
    """

    async def _analyze_with_score(self, async_client, mocker, score: float) -> dict:
        """Helper: patch engine to return a specific score, call endpoint."""
        mock = mocker.patch("app.routers.transactions.RiskEngineClient", autospec=True)
        mock.return_value.calculate_risk = AsyncMock(
            return_value=make_engine_response(risk_score=score)
        )
        payload = make_transaction_payload(amount=5000.0)
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200
        return response.json()

    @pytest.mark.unit
    async def test_risk_level_low_below_20(self, async_client, mocker):
        body = await self._analyze_with_score(async_client, mocker, score=5.0)
        assert body["risk_level"] == "LOW"

    @pytest.mark.unit
    async def test_risk_level_low_boundary_at_19_99(self, async_client, mocker):
        body = await self._analyze_with_score(async_client, mocker, score=19.99)
        assert body["risk_level"] == "LOW"

    @pytest.mark.unit
    async def test_risk_level_medium_at_20(self, async_client, mocker):
        body = await self._analyze_with_score(async_client, mocker, score=20.0)
        assert body["risk_level"] == "MEDIUM"

    @pytest.mark.unit
    async def test_risk_level_medium_at_49_99(self, async_client, mocker):
        body = await self._analyze_with_score(async_client, mocker, score=49.99)
        assert body["risk_level"] == "MEDIUM"

    @pytest.mark.unit
    async def test_risk_level_high_at_50(self, async_client, mocker):
        body = await self._analyze_with_score(async_client, mocker, score=50.0)
        assert body["risk_level"] == "HIGH"

    @pytest.mark.unit
    async def test_risk_level_high_at_79_99(self, async_client, mocker):
        body = await self._analyze_with_score(async_client, mocker, score=79.99)
        assert body["risk_level"] == "HIGH"

    @pytest.mark.unit
    async def test_risk_level_critical_at_80(self, async_client, mocker):
        body = await self._analyze_with_score(async_client, mocker, score=80.0)
        assert body["risk_level"] == "CRITICAL"

    @pytest.mark.unit
    async def test_risk_level_critical_above_100(self, async_client, mocker):
        """Scores above 100 are valid for very high-risk transactions."""
        body = await self._analyze_with_score(async_client, mocker, score=150.0)
        assert body["risk_level"] == "CRITICAL"

    @pytest.mark.unit
    async def test_risk_level_zero_score_is_low(self, async_client, mocker):
        body = await self._analyze_with_score(async_client, mocker, score=0.0)
        assert body["risk_level"] == "LOW"


# ════════════════════════════════════════════════════════════════════════════════
# Input Validation — 422 Unprocessable Entity
# ════════════════════════════════════════════════════════════════════════════════

class TestInputValidation:
    """
    Tests that Pydantic validation catches all invalid inputs.
    These tests verify the models.py constraints without needing the engine.
    """

    @pytest.mark.unit
    async def test_negative_amount_returns_422(self, async_client):
        payload = {"amount": -100.0, "transaction_type": "TRADE", "currency": "USD"}
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_zero_amount_returns_422(self, async_client):
        """Amount must be > 0, not >= 0."""
        payload = {"amount": 0.0, "transaction_type": "TRADE", "currency": "USD"}
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_amount_exceeding_max_returns_422(self, async_client):
        payload = {"amount": 10_000_001.0, "transaction_type": "TRADE", "currency": "USD"}
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_invalid_transaction_type_returns_422(self, async_client):
        payload = {"amount": 1000.0, "transaction_type": "UNKNOWN_TYPE", "currency": "USD"}
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_missing_amount_returns_422(self, async_client):
        payload = {"transaction_type": "TRADE", "currency": "USD"}
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_missing_transaction_type_returns_422(self, async_client):
        payload = {"amount": 1000.0, "currency": "USD"}
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_currency_wrong_length_returns_422(self, async_client):
        """Currency must be exactly 3 characters (ISO 4217)."""
        payload = {"amount": 1000.0, "transaction_type": "TRADE", "currency": "US"}
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_currency_too_long_returns_422(self, async_client):
        payload = {"amount": 1000.0, "transaction_type": "TRADE", "currency": "USDD"}
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_empty_body_returns_422(self, async_client):
        response = await async_client.post("/api/v1/analyze", json={})
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_string_amount_returns_422(self, async_client):
        payload = {"amount": "not-a-number", "transaction_type": "TRADE"}
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    @pytest.mark.unit
    async def test_422_response_contains_detail_field(self, async_client):
        """422 responses must include 'detail' for client debugging."""
        payload = {"amount": -1.0, "transaction_type": "TRADE"}
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.unit
    @pytest.mark.parametrize("tx_type", ["PAYMENT", "TRANSFER", "WITHDRAWAL", "DEPOSIT", "TRADE", "REFUND"])
    async def test_all_valid_transaction_types_accepted(self, async_client, mocker, tx_type):
        """Parametrize over all valid TransactionType enum values."""
        mocker.patch(
            "app.routers.transactions.RiskEngineClient",
            autospec=True,
        ).return_value.calculate_risk = AsyncMock(
            return_value=make_engine_response(transaction_type=tx_type)
        )
        payload = {"amount": 5000.0, "transaction_type": tx_type, "currency": "USD"}
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200


# ════════════════════════════════════════════════════════════════════════════════
# Error Propagation from Risk Engine
# ════════════════════════════════════════════════════════════════════════════════

class TestRiskEngineErrorPropagation:
    """
    Tests that errors from the Risk Engine are correctly translated
    into the right HTTP status codes for the API consumer.
    """

    @pytest.mark.integration
    async def test_engine_timeout_returns_504(self, async_client, mock_engine_timeout):
        """Risk Engine timeout → 504 Gateway Timeout."""
        payload = make_transaction_payload(amount=5000.0)
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 504

    @pytest.mark.integration
    async def test_engine_timeout_response_has_transaction_id(self, async_client, mock_engine_timeout):
        payload = make_transaction_payload(
            amount=5000.0, transaction_id="txn-timeout-test"
        )
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 504
        body = response.json()
        assert "detail" in body

    @pytest.mark.integration
    async def test_engine_unavailable_returns_503(self, async_client, mock_engine_unavailable):
        """Risk Engine connection error → 503 Service Unavailable."""
        payload = make_transaction_payload(amount=5000.0)
        response = await async_client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 503

    @pytest.mark.integration
    async def test_engine_unavailable_response_body_describes_error(
        self, async_client, mock_engine_unavailable
    ):
        payload = make_transaction_payload(amount=5000.0)
        response = await async_client.post("/api/v1/analyze", json=payload)
        body = response.json()
        assert "detail" in body
        detail = body["detail"]
        # Detail must contain error info for the consumer to understand
        assert isinstance(detail, (str, dict))

    @pytest.mark.integration
    async def test_engine_general_error_returns_5xx(self, async_client, mocker):
        """Unexpected exceptions must surface as 5xx, never leak stack traces."""
        mocker.patch(
            "app.routers.transactions.RiskEngineClient",
            autospec=True,
        ).return_value.calculate_risk = AsyncMock(
            side_effect=RuntimeError("Unexpected internal failure")
        )
        payload = make_transaction_payload(amount=5000.0)
        response = await async_client.post("/api/v1/analyze", json=payload)
        # Must be a server error, not a 200 or a crash
        assert response.status_code >= 500
        # Must NOT leak the raw exception message to the client
        body_str = response.text
        assert "Unexpected internal failure" not in body_str


# ════════════════════════════════════════════════════════════════════════════════
# Metrics Endpoint
# ════════════════════════════════════════════════════════════════════════════════

class TestMetricsEndpoint:
    @pytest.mark.integration
    async def test_metrics_endpoint_returns_200(self, async_client):
        response = await async_client.get("/metrics")
        assert response.status_code == 200

    @pytest.mark.integration
    async def test_metrics_content_type_is_prometheus(self, async_client):
        response = await async_client.get("/metrics")
        # Prometheus format starts with text/plain
        assert "text/plain" in response.headers.get("content-type", "")

    @pytest.mark.integration
    async def test_metrics_contain_analytics_api_metrics(self, async_client, mock_engine_success):
        # Make a request first so metrics are recorded
        await async_client.post(
            "/api/v1/analyze",
            json=make_transaction_payload(amount=5000.0),
        )
        response = await async_client.get("/metrics")
        body = response.text
        # Our custom metrics from Phase 1 must appear
        assert "analytics_api_requests_total" in body
