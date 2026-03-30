from finance.risk_profile import classify_risk_tier, generate_risk_summary


class TestClassifyRiskTier:
    def test_conservative(self):
        tier = classify_risk_tier(volatility=0.05, max_drawdown=-0.05, beta=0.4)
        assert tier == "Conservative"

    def test_moderate(self):
        tier = classify_risk_tier(volatility=0.15, max_drawdown=-0.15, beta=0.9)
        assert tier == "Moderate"

    def test_aggressive(self):
        tier = classify_risk_tier(volatility=0.28, max_drawdown=-0.30, beta=1.3)
        assert tier == "Aggressive"

    def test_speculative(self):
        tier = classify_risk_tier(volatility=0.60, max_drawdown=-0.70, beta=2.5)
        assert tier == "Speculative"


class TestGenerateRiskSummary:
    def test_returns_non_empty_string(self):
        summary = generate_risk_summary({
            "ticker": "AAPL",
            "risk_tier": "Moderate",
            "annualized_volatility": 0.20,
            "max_drawdown": -0.25,
            "sharpe_ratio": 0.9,
            "beta": 1.1,
        })
        assert isinstance(summary, str)
        assert len(summary) > 50
        assert "AAPL" in summary
        assert "Moderate" in summary
