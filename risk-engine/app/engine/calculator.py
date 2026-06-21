"""
Risk Engine - Core Calculation Engine
Simulates a heavy analytics workload computing:
    risk_score = transactionAmount * marketVolatilityFactor * typeAmplifier

The market volatility factor includes controlled jitter to simulate
real-world market data fluctuations.
"""
import asyncio
import random
import time
import numpy as np
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _get_live_volatility_factor() -> float:
    """
    Simulate fetching market volatility from a real-time data feed.

    In production this would:
      - Read from a Vault-managed dynamic secret
      - Fetch from a market data API (Bloomberg, Reuters, etc.)
      - Read from a Redis cache updated by a separate market-feed service

    Here we apply Gaussian jitter to the configured base factor to simulate
    realistic variation.
    """
    base = settings.MARKET_VOLATILITY_FACTOR
    jitter_range = base * settings.VOLATILITY_JITTER_PCT
    # Use numpy's normal distribution for realistic market-like noise
    noise = np.random.normal(loc=0, scale=jitter_range / 3)
    factor = max(0.001, base + noise)
    return round(factor, 6)


def _get_type_amplifier(transaction_type: str) -> float:
    """Return the risk amplifier for the given transaction type."""
    amplifiers = settings.TYPE_RISK_AMPLIFIERS
    return amplifiers.get(transaction_type.upper(), 1.0)


async def calculate_risk_score(
    transaction_id: str,
    transaction_amount: float,
    transaction_type: str,
) -> dict:
    """
    Core async risk calculation function.

    Algorithm:
        raw_score   = transaction_amount × market_volatility_factor × type_amplifier
        risk_score  = (raw_score / normalization_divisor) × 100  [0–100 scale]

    The computation is intentionally run in a thread pool executor to
    simulate CPU-bound workload without blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        _compute_score_sync,
        transaction_id,
        transaction_amount,
        transaction_type,
    )
    return result


def _compute_score_sync(
    transaction_id: str,
    transaction_amount: float,
    transaction_type: str,
) -> dict:
    """
    Synchronous (CPU-bound) risk score computation.
    Runs inside a thread pool to avoid blocking the async event loop.
    """
    start = time.perf_counter()

    volatility_factor = _get_live_volatility_factor()
    type_amplifier = _get_type_amplifier(transaction_type)

    # ── Core formula ──────────────────────────────────────────────────────────
    raw_score = transaction_amount * volatility_factor * type_amplifier

    # Normalize to 0-100 scale; scores can exceed 100 for very high-risk txns
    normalized_score = (raw_score / settings.SCORE_NORMALIZATION_DIVISOR) * 100

    # Simulate additional analytics workload (matrix ops, statistical analysis)
    _simulate_analytics_workload(transaction_amount)

    elapsed_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "risk_score_computed",
        transaction_id=transaction_id,
        transaction_amount=transaction_amount,
        transaction_type=transaction_type,
        volatility_factor=volatility_factor,
        type_amplifier=type_amplifier,
        raw_score=round(raw_score, 4),
        risk_score=round(normalized_score, 4),
        computation_time_ms=round(elapsed_ms, 2),
    )

    return {
        "transaction_id": transaction_id,
        "risk_score": round(normalized_score, 4),
        "raw_score": round(raw_score, 4),
        "market_volatility_factor": volatility_factor,
        "transaction_type": transaction_type,
        "transaction_amount": transaction_amount,
        "computation_time_ms": round(elapsed_ms, 2),
    }


def _simulate_analytics_workload(amount: float) -> None:
    """
    Simulate CPU-intensive analytics operations.

    In a real engine this would be:
      - Historical transaction pattern matching
      - ML model inference (fraud scoring, anomaly detection)
      - Graph traversal for counterparty risk
      - Monte Carlo simulations for VaR calculations
    """
    # Generate a random-sized correlation matrix based on amount magnitude
    matrix_size = min(int(amount / 1000) + 5, 50)  # Cap at 50×50
    matrix = np.random.rand(matrix_size, matrix_size)

    # Compute eigenvalues — simulates covariance matrix analysis
    _ = np.linalg.eigvals(matrix @ matrix.T)

    # Simulate statistical percentile computations
    sample = np.random.normal(amount, amount * 0.1, 1000)
    _ = np.percentile(sample, [5, 25, 50, 75, 95])
