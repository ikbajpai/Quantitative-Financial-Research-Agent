import numpy as np
import pandas as pd
import pytest

from finance.metrics import (
    align_returns,
    annualized_return,
    annualized_volatility,
    beta,
    alpha,
    calmar_ratio,
    conditional_var,
    correlation_matrix,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
    value_at_risk,
)


class TestAnnualizedReturn:
    def test_positive_returns(self, sample_returns):
        result = annualized_return(sample_returns)
        assert isinstance(result, float)
        assert -1.0 < result < 5.0

    def test_zero_returns(self):
        returns = pd.Series([0.0] * 100)
        assert annualized_return(returns) == pytest.approx(0.0, abs=1e-6)

    def test_empty_returns(self):
        assert annualized_return(pd.Series([], dtype=float)) == 0.0


class TestAnnualizedVolatility:
    def test_positive_returns(self, sample_returns):
        result = annualized_volatility(sample_returns)
        assert isinstance(result, float)
        assert 0.0 < result < 2.0

    def test_constant_returns(self):
        returns = pd.Series([0.001] * 100)
        assert annualized_volatility(returns) == pytest.approx(0.0, abs=1e-6)


class TestSharpeRatio:
    def test_positive_sharpe(self, sample_returns):
        result = sharpe_ratio(sample_returns, risk_free_rate=0.0)
        assert result is not None
        assert isinstance(result, float)

    def test_zero_volatility(self):
        returns = pd.Series([0.001] * 100)
        result = sharpe_ratio(returns)
        assert result is None


class TestSortinoRatio:
    def test_returns_float_or_none(self, sample_returns):
        result = sortino_ratio(sample_returns)
        assert result is None or isinstance(result, float)


class TestMaxDrawdown:
    def test_negative_value(self, sample_returns):
        result = max_drawdown(sample_returns)
        assert result <= 0.0

    def test_always_declining_series(self):
        returns = pd.Series([-0.01] * 50)
        result = max_drawdown(returns)
        assert result < -0.3

    def test_always_rising_series(self):
        returns = pd.Series([0.01] * 50)
        result = max_drawdown(returns)
        assert result == pytest.approx(0.0, abs=1e-6)

    def test_empty(self):
        assert max_drawdown(pd.Series([], dtype=float)) == 0.0


class TestBeta:
    def test_identical_series_has_beta_one(self, sample_returns):
        result = beta(sample_returns, sample_returns)
        assert result == pytest.approx(1.0, abs=0.01)

    def test_returns_float(self, sample_returns, benchmark_returns):
        result = beta(sample_returns, benchmark_returns)
        assert isinstance(result, float)


class TestAlpha:
    def test_returns_float(self, sample_returns, benchmark_returns):
        result = alpha(sample_returns, benchmark_returns)
        assert isinstance(result, float)

    def test_identical_series_near_zero_alpha(self, sample_returns):
        result = alpha(sample_returns, sample_returns)
        assert abs(result) < 0.5


class TestVaR:
    def test_var_is_negative(self, sample_returns):
        result = value_at_risk(sample_returns)
        assert result < 0

    def test_cvar_lte_var(self, sample_returns):
        var = value_at_risk(sample_returns)
        cvar = conditional_var(sample_returns)
        assert cvar <= var


class TestCorrelationMatrix:
    def test_symmetric(self, sample_returns, benchmark_returns):
        result = correlation_matrix({"A": sample_returns, "B": benchmark_returns})
        assert result.loc["A", "A"] == pytest.approx(1.0, abs=1e-6)
        assert result.loc["B", "B"] == pytest.approx(1.0, abs=1e-6)
        assert result.loc["A", "B"] == pytest.approx(result.loc["B", "A"], abs=1e-10)

    def test_diagonal_ones(self, sample_returns):
        result = correlation_matrix({"X": sample_returns})
        assert result.loc["X", "X"] == pytest.approx(1.0, abs=1e-6)


class TestAlignReturns:
    def test_alignment(self):
        a = pd.Series([1, 2, 3], index=pd.date_range("2020-01-01", periods=3))
        b = pd.Series([4, 5], index=pd.date_range("2020-01-02", periods=2))
        a_aligned, b_aligned = align_returns(a, b)
        assert len(a_aligned) == 2
        assert len(b_aligned) == 2
