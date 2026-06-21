"""
Risk Engine - Prometheus Metrics
"""
from prometheus_client import Counter, Histogram, Gauge

CALCULATIONS_TOTAL = Counter(
    "risk_engine_calculations_total",
    "Total number of risk score calculations performed",
    ["transaction_type"],
)

CALCULATION_DURATION = Histogram(
    "risk_engine_calculation_duration_seconds",
    "Time taken to compute a risk score",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

RISK_SCORE_OUTPUT = Histogram(
    "risk_engine_score_output_distribution",
    "Distribution of raw risk scores produced",
    buckets=[0, 10, 25, 50, 75, 100, 150, 200, 500],
)

VOLATILITY_FACTOR_GAUGE = Gauge(
    "risk_engine_market_volatility_factor",
    "Current market volatility factor being applied",
)

ACTIVE_CALCULATIONS = Gauge(
    "risk_engine_active_calculations",
    "Number of risk calculations currently in progress",
)

CALCULATION_ERRORS = Counter(
    "risk_engine_calculation_errors_total",
    "Total number of risk calculation errors",
    ["error_type"],
)
