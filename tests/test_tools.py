import json
import pytest

from tools.data_fetcher import _fetch_price_data
from tools.risk_calculator import _calculate_risk_metrics
from tools.correlation_analyzer import _analyze_correlation
from tools.report_builder import _build_final_report


class TestFetchPriceData:
    def test_returns_valid_json(self, mock_yfinance):
        result = _fetch_price_data("AAPL", period="1y")
        data = json.loads(result)
        assert "ticker" in data
        assert data["ticker"] == "AAPL"

    def test_contains_required_keys(self, mock_yfinance):
        result = _fetch_price_data("MSFT")
        data = json.loads(result)
        assert "price_stats" in data
        assert "return_stats" in data
        assert "trading_days" in data

    def test_numeric_values_in_range(self, mock_yfinance):
        result = _fetch_price_data("SPY")
        data = json.loads(result)
        assert data["trading_days"] > 0
        assert data["price_stats"]["start_price"] > 0


class TestCalculateRiskMetrics:
    def test_returns_valid_json(self, mock_yfinance):
        result = _calculate_risk_metrics("AAPL")
        data = json.loads(result)
        assert "ticker" in data
        assert "sharpe_ratio" in data

    def test_risk_tier_valid(self, mock_yfinance):
        result = _calculate_risk_metrics("AAPL")
        data = json.loads(result)
        assert data["risk_tier"] in ["Conservative", "Moderate", "Aggressive", "Speculative"]

    def test_max_drawdown_is_negative(self, mock_yfinance):
        result = _calculate_risk_metrics("AAPL")
        data = json.loads(result)
        assert data["max_drawdown"] <= 0


class TestAnalyzeCorrelation:
    def test_returns_valid_json(self, mock_yfinance):
        result = _analyze_correlation(["AAPL", "MSFT"])
        data = json.loads(result)
        assert "correlation_matrix" in data

    def test_diagonal_is_one(self, mock_yfinance):
        result = _analyze_correlation(["AAPL", "MSFT"])
        data = json.loads(result)
        matrix = data["correlation_matrix"]
        for ticker in matrix:
            assert matrix[ticker][ticker] == pytest.approx(1.0, abs=0.01)

    def test_single_ticker_returns_error(self, mock_yfinance):
        result = _analyze_correlation(["AAPL"])
        data = json.loads(result)
        assert "error" in data


class TestBuildFinalReport:
    def test_comparison_report_structure(self):
        metrics = [
            {"ticker": "AAPL", "sharpe_ratio": 1.2, "annualized_volatility": 0.2,
             "annualized_return": 0.15, "risk_tier": "Moderate"},
            {"ticker": "GOOGL", "sharpe_ratio": 0.9, "annualized_volatility": 0.25,
             "annualized_return": 0.12, "risk_tier": "Aggressive"},
        ]
        result = _build_final_report(
            query="Compare AAPL and GOOGL",
            report_type="comparison",
            metrics_json=json.dumps(metrics),
            tickers=["AAPL", "GOOGL"],
            period="5y",
        )
        data = json.loads(result)
        assert data["report_type"] == "comparison"
        assert "recommendation" in data
        assert "generated_at" in data

    def test_portfolio_report_structure(self):
        portfolio_data = {
            "portfolio_metrics": {
                "ticker": "PORTFOLIO",
                "sharpe_ratio": 1.1,
                "annualized_return": 0.13,
                "annualized_volatility": 0.12,
                "risk_tier": "Moderate",
                "max_drawdown": -0.15,
            },
            "individual_metrics": [],
            "weights": [0.5, 0.5],
        }
        result = _build_final_report(
            query="Analyze my portfolio",
            report_type="portfolio",
            metrics_json=json.dumps(portfolio_data),
            tickers=["AAPL", "MSFT"],
            period="3y",
        )
        data = json.loads(result)
        assert data["report_type"] == "portfolio"
        assert "portfolio_metrics" in data
        assert "recommendation" in data
