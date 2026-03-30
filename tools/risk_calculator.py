import json
import logging

from langchain_core.tools import StructuredTool

from finance.fetcher import fetch_price_history, DataFetchError
from finance import metrics as m
from finance.risk_profile import classify_risk_tier, generate_risk_summary
from schemas.inputs import RiskCalculationInput

logger = logging.getLogger(__name__)


def _calculate_risk_metrics(
    ticker: str,
    period: str = "5y",
    benchmark: str = "^GSPC",
    risk_free_rate: float = 0.0425,
) -> str:
    """
    Computes a comprehensive risk metric profile for a single ticker.
    """
    try:
        df = fetch_price_history(ticker, period=period)
        bm_df = fetch_price_history(benchmark, period=period)
    except DataFetchError as e:
        return json.dumps({"error": str(e), "ticker": ticker})

    returns = df["returns"]
    bm_returns = bm_df["returns"]

    ann_ret = m.annualized_return(returns)
    ann_vol = m.annualized_volatility(returns)
    sharpe = m.sharpe_ratio(returns, risk_free_rate)
    sortino = m.sortino_ratio(returns, risk_free_rate)
    mdd = m.max_drawdown(returns)
    calmar = m.calmar_ratio(returns, risk_free_rate)
    b = m.beta(returns, bm_returns)
    a = m.alpha(returns, bm_returns, risk_free_rate)
    var95 = m.value_at_risk(returns)
    cvar95 = m.conditional_var(returns)
    risk_tier = classify_risk_tier(ann_vol, mdd, b)

    result = {
        "ticker": ticker.upper(),
        "period": period,
        "benchmark": benchmark,
        "annualized_return": round(ann_ret, 6),
        "annualized_volatility": round(ann_vol, 6),
        "sharpe_ratio": round(sharpe, 4) if sharpe is not None else None,
        "sortino_ratio": round(sortino, 4) if sortino is not None else None,
        "max_drawdown": round(mdd, 6),
        "calmar_ratio": round(calmar, 4) if calmar is not None else None,
        "beta": round(b, 4),
        "alpha": round(a, 6),
        "var_95": round(var95, 6),
        "cvar_95": round(cvar95, 6),
        "risk_tier": risk_tier,
        "risk_summary": generate_risk_summary({
            "ticker": ticker.upper(),
            "risk_tier": risk_tier,
            "annualized_volatility": ann_vol,
            "max_drawdown": mdd,
            "sharpe_ratio": sharpe,
            "beta": b,
        }),
    }
    return json.dumps(result)


calculate_risk_metrics_tool = StructuredTool(
    name="calculate_risk_metrics",
    description=(
        "Computes full quantitative risk metrics for a single ticker: "
        "annualized return & volatility, Sharpe ratio, Sortino ratio, max drawdown, "
        "Calmar ratio, beta, Jensen's alpha, VaR (95%), CVaR (95%), and risk tier classification. "
        "Use this for every ticker you need to analyze. Returns JSON."
    ),
    func=_calculate_risk_metrics,
    args_schema=RiskCalculationInput,
)
