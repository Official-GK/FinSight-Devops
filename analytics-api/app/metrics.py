"""
Analytics API - Prometheus Metrics
Centralized metrics registry for the Analytics API service.
"""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, REGISTRY

# ── Request Metrics ──────────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "analytics_api_requests_total",
    "Total number of HTTP requests received",
    ["method", "endpoint", "http_status"],
)

REQUEST_LATENCY = Histogram(
    "analytics_api_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ── Business Metrics ─────────────────────────────────────────────────────────
TRANSACTIONS_ANALYZED = Counter(
    "analytics_api_transactions_analyzed_total",
    "Total number of transactions analyzed",
    ["transaction_type", "risk_level"],
)

RISK_SCORE_HISTOGRAM = Histogram(
    "analytics_api_risk_score_distribution",
    "Distribution of risk scores calculated",
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200],
)

TRANSACTION_AMOUNT_HISTOGRAM = Histogram(
    "analytics_api_transaction_amount_usd",
    "Distribution of transaction amounts in USD",
    buckets=[100, 1_000, 5_000, 10_000, 50_000, 100_000, 500_000, 1_000_000],
)

# ── Risk Engine Client Metrics ───────────────────────────────────────────────
RISK_ENGINE_CALL_DURATION = Histogram(
    "analytics_api_risk_engine_call_duration_seconds",
    "Latency of calls to the Risk Engine service",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

RISK_ENGINE_ERRORS = Counter(
    "analytics_api_risk_engine_errors_total",
    "Total number of errors calling the Risk Engine",
    ["error_type"],
)

RISK_ENGINE_RETRIES = Counter(
    "analytics_api_risk_engine_retries_total",
    "Total number of retries to the Risk Engine",
)

# ── System Metrics ───────────────────────────────────────────────────────────
ACTIVE_REQUESTS = Gauge(
    "analytics_api_active_requests",
    "Number of currently active HTTP requests",
)
