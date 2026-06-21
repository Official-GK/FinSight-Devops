"""
Risk Engine — test_calculator.py

Tests for app/engine/calculator.py

This is the core business logic test file. We test:
  1. The risk formula: raw_score = amount × volatility × amplifier
  2. All transaction type amplifiers apply their correct multipliers
  3. Score normalization to the 0-100 scale
  4. Edge cases: near-zero amounts, very large amounts, extreme volatility
  5. The async wrapper correctly delegates to the sync computation
  6. The volatility jitter stays within configured bounds
  7. The NumPy matrix simulation doesn't crash on any valid input

All formula-critical tests use the `fixed_volatility` fixture to eliminate
randomness and produce 100% deterministic assertions.
"""
import asyncio
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from app.engine.calculator import (
    calculate_risk_score,
    _compute_score_sync,
    _get_live_volatility_factor,
    _get_type_amplifier,
    _simulate_analytics_workload,
)
from app.config import get_settings

settings = get_settings()

# Pre-computed expected values based on FIXED_VOLATILITY_FACTOR = 0.0035
# and SCORE_NORMALIZATION_DIVISOR = 35000.0
FIXED_VOL = 0.0035
NORM_DIV = settings.SCORE_NORMALIZATION_DIVISOR


def expected_risk_score(amount: float, tx_type: str, vol: float = FIXED_VOL) -> float:
    """Compute the expected risk score with the same formula as the engine."""
    amplifier = settings.TYPE_RISK_AMPLIFIERS.get(tx_type.upper(), 1.0)
    raw = amount * vol * amplifier
    return (raw / NORM_DIV) * 100


# ════════════════════════════════════════════════════════════════════════════════
# Transaction Type Amplifiers
# ════════════════════════════════════════════════════════════════════════════════

class TestTransactionTypeAmplifiers:
    """
    Verify that each transaction type applies the correct risk amplifier.
    These tests directly call _get_type_amplifier() to unit-test the mapping.
    """

    @pytest.mark.unit
    def test_trade_amplifier_is_1_8(self):
        assert _get_type_amplifier("TRADE") == pytest.approx(1.8)

    @pytest.mark.unit
    def test_transfer_amplifier_is_1_4(self):
        assert _get_type_amplifier("TRANSFER") == pytest.approx(1.4)

    @pytest.mark.unit
    def test_withdrawal_amplifier_is_1_2(self):
        assert _get_type_amplifier("WITHDRAWAL") == pytest.approx(1.2)

    @pytest.mark.unit
    def test_payment_amplifier_is_1_0(self):
        assert _get_type_amplifier("PAYMENT") == pytest.approx(1.0)

    @pytest.mark.unit
    def test_deposit_amplifier_is_0_8(self):
        assert _get_type_amplifier("DEPOSIT") == pytest.approx(0.8)

    @pytest.mark.unit
    def test_refund_amplifier_is_0_6(self):
        assert _get_type_amplifier("REFUND") == pytest.approx(0.6)

    @pytest.mark.unit
    def test_unknown_type_defaults_to_1_0(self):
        """Unknown transaction types must not crash — default to neutral 1.0."""
        assert _get_type_amplifier("UNKNOWN_TYPE") == pytest.approx(1.0)

    @pytest.mark.unit
    def test_amplifier_is_case_insensitive(self):
        """Type names should be uppercased before lookup."""
        assert _get_type_amplifier("trade") == _get_type_amplifier("TRADE")
        assert _get_type_amplifier("payment") == _get_type_amplifier("PAYMENT")

    @pytest.mark.unit
    def test_trade_has_highest_amplifier(self):
        """TRADE must always produce the highest risk score (most amplified)."""
        amplifiers = {
            t: _get_type_amplifier(t)
            for t in ["TRADE", "TRANSFER", "WITHDRAWAL", "PAYMENT", "DEPOSIT", "REFUND"]
        }
        assert amplifiers["TRADE"] == max(amplifiers.values())

    @pytest.mark.unit
    def test_refund_has_lowest_amplifier(self):
        """REFUND must always produce the lowest risk score."""
        amplifiers = {
            t: _get_type_amplifier(t)
            for t in ["TRADE", "TRANSFER", "WITHDRAWAL", "PAYMENT", "DEPOSIT", "REFUND"]
        }
        assert amplifiers["REFUND"] == min(amplifiers.values())


# ════════════════════════════════════════════════════════════════════════════════
# Core Formula Verification — _compute_score_sync()
# ════════════════════════════════════════════════════════════════════════════════

class TestRiskScoreFormula:
    """
    Tests the core formula:
        raw_score  = amount × volatility × type_amplifier
        risk_score = (raw_score / NORMALIZATION_DIVISOR) × 100

    All tests use fixed_volatility to eliminate jitter.
    """

    @pytest.mark.unit
    def test_formula_for_trade_transaction(self, fixed_volatility):
        result = _compute_score_sync(
            transaction_id="txn-formula-trade",
            transaction_amount=10_000.0,
            transaction_type="TRADE",
        )
        # raw = 10000 * 0.0035 * 1.8 = 63.0
        assert result["raw_score"] == pytest.approx(63.0, abs=0.001)

    @pytest.mark.unit
    def test_formula_for_payment_transaction(self, fixed_volatility):
        result = _compute_score_sync(
            transaction_id="txn-formula-payment",
            transaction_amount=10_000.0,
            transaction_type="PAYMENT",
        )
        # raw = 10000 * 0.0035 * 1.0 = 35.0
        assert result["raw_score"] == pytest.approx(35.0, abs=0.001)

    @pytest.mark.unit
    def test_formula_for_refund_transaction(self, fixed_volatility):
        result = _compute_score_sync(
            transaction_id="txn-formula-refund",
            transaction_amount=10_000.0,
            transaction_type="REFUND",
        )
        # raw = 10000 * 0.0035 * 0.6 = 21.0
        assert result["raw_score"] == pytest.approx(21.0, abs=0.001)

    @pytest.mark.unit
    def test_normalization_produces_correct_risk_score(self, fixed_volatility):
        """risk_score = (raw / 35000) * 100"""
        result = _compute_score_sync(
            transaction_id="txn-norm",
            transaction_amount=10_000.0,
            transaction_type="PAYMENT",
        )
        # raw = 35.0 → risk_score = (35.0 / 35000) * 100 = 0.1
        assert result["risk_score"] == pytest.approx(0.1, abs=0.01)

    @pytest.mark.unit
    @pytest.mark.parametrize("tx_type", [
        "TRADE", "TRANSFER", "WITHDRAWAL", "PAYMENT", "DEPOSIT", "REFUND"
    ])
    def test_all_transaction_types_produce_positive_score(self, fixed_volatility, tx_type):
        """Every transaction type must produce a positive (>= 0) risk score."""
        result = _compute_score_sync("txn-pos", 5000.0, tx_type)
        assert result["risk_score"] >= 0.0

    @pytest.mark.unit
    def test_trade_score_higher_than_refund_same_amount(self, fixed_volatility):
        """TRADE must always produce a higher score than REFUND for the same amount."""
        trade = _compute_score_sync("txn-trade", 10000.0, "TRADE")
        refund = _compute_score_sync("txn-refund", 10000.0, "REFUND")
        assert trade["risk_score"] > refund["risk_score"]

    @pytest.mark.unit
    def test_higher_amount_produces_higher_score(self, fixed_volatility):
        """Score must scale proportionally with transaction amount."""
        small = _compute_score_sync("txn-small", 1_000.0, "TRADE")
        large = _compute_score_sync("txn-large", 100_000.0, "TRADE")
        assert large["risk_score"] > small["risk_score"]
        # Score should scale ~100x for 100x the amount (linear relationship)
        ratio = large["risk_score"] / small["risk_score"]
        assert ratio == pytest.approx(100.0, rel=0.01)

    @pytest.mark.unit
    def test_result_contains_all_required_fields(self, fixed_volatility):
        result = _compute_score_sync("txn-fields", 5000.0, "TRADE")
        required = [
            "transaction_id", "risk_score", "raw_score",
            "market_volatility_factor", "transaction_type",
            "transaction_amount", "computation_time_ms",
        ]
        for field in required:
            assert field in result, f"Missing field: '{field}'"

    @pytest.mark.unit
    def test_result_preserves_transaction_id(self, fixed_volatility):
        result = _compute_score_sync("my-unique-txn-id", 5000.0, "TRADE")
        assert result["transaction_id"] == "my-unique-txn-id"

    @pytest.mark.unit
    def test_result_preserves_transaction_amount(self, fixed_volatility):
        result = _compute_score_sync("txn-amt", 12345.67, "PAYMENT")
        assert result["transaction_amount"] == 12345.67

    @pytest.mark.unit
    def test_computation_time_is_positive(self, fixed_volatility):
        result = _compute_score_sync("txn-time", 5000.0, "TRADE")
        assert result["computation_time_ms"] >= 0.0

    @pytest.mark.unit
    def test_volatility_factor_is_recorded_in_result(self, fixed_volatility):
        """The exact volatility factor used must be recorded for auditability."""
        result = _compute_score_sync("txn-vol", 5000.0, "TRADE")
        assert result["market_volatility_factor"] == pytest.approx(FIXED_VOL, rel=0.01)


# ════════════════════════════════════════════════════════════════════════════════
# Edge Cases
# ════════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """
    Tests for boundary conditions and extreme inputs.
    These ensure the engine never crashes or produces nonsensical output.
    """

    @pytest.mark.edge_case
    def test_very_small_amount(self, fixed_volatility):
        """Smallest allowed amount (0.01 USD) must not crash."""
        result = _compute_score_sync("txn-tiny", 0.01, "TRADE")
        assert result["risk_score"] >= 0.0
        assert result["raw_score"] >= 0.0

    @pytest.mark.edge_case
    def test_very_large_amount(self, fixed_volatility):
        """Maximum amount (10M USD) must produce a valid score."""
        result = _compute_score_sync("txn-huge", 10_000_000.0, "TRADE")
        # raw = 10M * 0.0035 * 1.8 = 63,000 → score = (63000/35000)*100 = 180
        assert result["risk_score"] > 100.0  # Exceeds 100 — valid for large transactions
        assert result["risk_score"] == pytest.approx(180.0, abs=0.1)

    @pytest.mark.edge_case
    def test_large_amount_score_exceeds_100(self, fixed_volatility):
        """The scale allows scores > 100 for very high-risk/high-amount transactions."""
        result = _compute_score_sync("txn-over-100", 10_000_000.0, "TRADE")
        assert result["risk_score"] > 100.0

    @pytest.mark.edge_case
    @pytest.mark.slow
    def test_matrix_simulation_with_large_amount(self, fixed_volatility):
        """
        The NumPy matrix simulation size scales with amount (capped at 50×50).
        Very large amounts must not cause OOM or crash.
        """
        # This should not raise any exception
        _simulate_analytics_workload(1_000_000.0)

    @pytest.mark.edge_case
    @pytest.mark.slow
    def test_matrix_simulation_with_tiny_amount(self, fixed_volatility):
        """Tiny amounts produce a very small matrix (5×5) — must not crash."""
        _simulate_analytics_workload(0.01)

    @pytest.mark.edge_case
    def test_repeated_calls_produce_consistent_relative_ordering(self, fixed_volatility):
        """
        With fixed volatility, two calls with different amounts must produce
        scores that are in the same relative order (larger amount → larger score).
        This is a monotonicity test.
        """
        amounts = [100, 1000, 10_000, 100_000, 1_000_000]
        scores = [
            _compute_score_sync(f"txn-{a}", float(a), "TRADE")["risk_score"]
            for a in amounts
        ]
        # Scores must be strictly increasing
        for i in range(len(scores) - 1):
            assert scores[i] < scores[i + 1], (
                f"Score {scores[i]} (amount {amounts[i]}) should be less than "
                f"score {scores[i+1]} (amount {amounts[i+1]})"
            )


# ════════════════════════════════════════════════════════════════════════════════
# Volatility Factor Tests
# ════════════════════════════════════════════════════════════════════════════════

class TestVolatilityFactor:
    """
    Tests for _get_live_volatility_factor() — the market data simulation.
    These tests run WITHOUT the fixed_volatility fixture to test real behavior.
    """

    @pytest.mark.unit
    def test_volatility_factor_is_positive(self):
        """Volatility factor must always be positive (negative volatility is nonsense)."""
        for _ in range(20):  # Run multiple times to test random variation
            factor = _get_live_volatility_factor()
            assert factor > 0.0, f"Got non-positive volatility factor: {factor}"

    @pytest.mark.unit
    def test_volatility_factor_is_near_base_value(self):
        """
        Factor must stay within a reasonable range of the base value.
        We use a wide tolerance to accommodate Gaussian noise.
        Base = 0.0035, Jitter = 15% → expected range ≈ [0.001, 0.007]
        """
        base = settings.MARKET_VOLATILITY_FACTOR
        tolerance = base * 0.5  # 50% tolerance to handle 3σ Gaussian extremes
        for _ in range(50):
            factor = _get_live_volatility_factor()
            assert abs(factor - base) < tolerance, (
                f"Volatility factor {factor} is too far from base {base}"
            )

    @pytest.mark.unit
    def test_volatility_factor_has_variation_across_calls(self):
        """
        Factor must NOT be the same on every call (it has Gaussian jitter).
        The probability that 10 calls produce the exact same value is astronomically low.
        """
        factors = {_get_live_volatility_factor() for _ in range(10)}
        assert len(factors) > 1, "Volatility factor shows no variation — jitter is broken"


# ════════════════════════════════════════════════════════════════════════════════
# Async Wrapper — calculate_risk_score()
# ════════════════════════════════════════════════════════════════════════════════

class TestAsyncCalculateRiskScore:
    """
    Tests for the async wrapper that runs the CPU-bound computation
    in a thread pool executor.
    """

    @pytest.mark.unit
    async def test_async_function_returns_dict(self, fixed_volatility):
        result = await calculate_risk_score(
            transaction_id="async-txn-001",
            transaction_amount=10_000.0,
            transaction_type="TRADE",
        )
        assert isinstance(result, dict)

    @pytest.mark.unit
    async def test_async_result_matches_sync_computation(self, fixed_volatility):
        """The async wrapper must produce the same result as the sync function."""
        async_result = await calculate_risk_score(
            transaction_id="compare-txn",
            transaction_amount=5_000.0,
            transaction_type="PAYMENT",
        )
        sync_result = _compute_score_sync(
            transaction_id="compare-txn",
            transaction_amount=5_000.0,
            transaction_type="PAYMENT",
        )
        # Core fields must match exactly
        assert async_result["risk_score"] == sync_result["risk_score"]
        assert async_result["raw_score"] == sync_result["raw_score"]
        assert async_result["transaction_type"] == sync_result["transaction_type"]

    @pytest.mark.unit
    async def test_async_function_does_not_block_event_loop(self, fixed_volatility):
        """
        Heavy NumPy computation runs in a thread pool executor.
        We verify the event loop remains responsive by running a coroutine
        concurrently with the calculation.
        """
        async def dummy_coroutine():
            await asyncio.sleep(0)
            return "event_loop_responsive"

        calc_task = asyncio.create_task(
            calculate_risk_score("txn-concurrent", 500_000.0, "TRADE")
        )
        dummy_task = asyncio.create_task(dummy_coroutine())

        dummy_result = await dummy_task
        calc_result = await calc_task

        # Both must complete successfully
        assert dummy_result == "event_loop_responsive"
        assert "risk_score" in calc_result

    @pytest.mark.unit
    async def test_concurrent_calculations_are_independent(self, fixed_volatility):
        """
        Multiple concurrent calculations must not interfere with each other.
        Each must return results for its own transaction.
        """
        tasks = [
            asyncio.create_task(
                calculate_risk_score(f"concurrent-txn-{i}", float(i * 1000), "TRADE")
            )
            for i in range(1, 6)
        ]
        results = await asyncio.gather(*tasks)

        for i, result in enumerate(results, start=1):
            assert result["transaction_id"] == f"concurrent-txn-{i}"
            assert result["transaction_amount"] == float(i * 1000)
