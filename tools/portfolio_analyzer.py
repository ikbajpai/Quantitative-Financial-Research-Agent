import json
import logging
from typing import List, Optional

import numpy as np
import pandas as pd
from langchain_core.tools import StructuredTool

from finance.fetcher import fetch_multiple_tickers, fetch_price_history, DataFetchError
from finance import metrics as m
from finance.risk_profile import classify_risk_tier, generate_risk_summary
from schemas.inputs import PortfolioInput

logger = logging.getLogger(__name__)


def _analyze_portfolio(
    tickers: List[str],
    weights: Optional[List[float]] = None,
    period: str = "3y",
    benchmark: str = "^GSPC",
) -> str:
    """
    Analyzes a portfolio's aggregate and individual risk metrics.
    """
    if weights is None:
        weights = [1.0 / len(tickers)] * len(tickers)

    if abs(sum(weights) - 1.0) > 0.01:
        return json.dumps({"error": f"Weights must sum to 1.0, got {sum(weights):.4f}"})

    data = fetch_multiple_tickers(tickers, period=period)
    returns_dict = {}
    for t, df in data.items():
        if not df.empty:
            returns_dict[t.upper()] = df["returns"]

    if len(returns_dict) < 1:
        return json.dumps({"error": "No valid data fetched for any ticker."})

    aligned_returns = pd.DataFrame(returns_dict).dropna()
    valid_tickers = list(aligned_returns.columns)
    valid_weights = []
    for t, w in zip([t.upper() for t in tickers], weights):
        if t in valid_tickers:
            valid_weights.append(w)
    w_array = np.array(valid_weights, dtype=float)
    w_array = w_array / w_array.sum()

    portfolio_returns = aligned_returns.values @ w_array
    portfolio_series = pd.Series(portfolio_returns, index=aligned_returns.index, name="PORTFOLIO")

    try:
        bm_df = fetch_price_history(benchmark, period=period)
        bm_returns = bm_df["returns"]
    except DataFetchError:
        bm_returns = portfolio_series * 0

    risk_free_rate = 0.0425

    def build_metrics(series: pd.Series, ticker: str) -> dict:
        ann_ret = m.annualized_return(series)
        ann_vol = m.annualized_volatility(series)
        sharpe = m.sharpe_ratio(series, risk_free_rate)
        sortino = m.sortino_ratio(series, risk_free_rate)
        mdd = m.max_drawdown(series)
        calmar = m.calmar_ratio(series, risk_free_rate)
        b = m.beta(series, bm_returns)
        a = m.alpha(series, bm_returns, risk_free_rate)
        var95 = m.value_at_risk(series)
        cvar95 = m.conditional_var(series)
        tier = classify_risk_tier(ann_vol, mdd, b)
        return {
            "ticker": ticker,
            "period": period,
            "annualized_return": round(ann_ret, 6),
            "annualized_volatility": round(ann_vol, 6),
            "sharpe_ratio": round(sharpe, 4) if sharpe else None,
            "sortino_ratio": round(sortino, 4) if sortino else None,
            "max_drawdown": round(mdd, 6),
            "calmar_ratio": round(calmar, 4) if calmar else None,
            "beta": round(b, 4),
            "alpha": round(a, 6),
            "var_95": round(var95, 6),
            "cvar_95": round(cvar95, 6),
            "risk_tier": tier,
            "risk_summary": generate_risk_summary({
                "ticker": ticker,
                "risk_tier": tier,
                "annualized_volatility": ann_vol,
                "max_drawdown": mdd,
                "sharpe_ratio": sharpe,
                "beta": b,
            }),
        }

    portfolio_m = build_metrics(portfolio_series, "PORTFOLIO")
    individual_m = [
        build_metrics(aligned_returns[t], t) for t in valid_tickers
    ]

    result = {
        "tickers": valid_tickers,
        "weights": w_array.tolist(),
        "period": period,
        "benchmark": benchmark,
        "portfolio_metrics": portfolio_m,
        "individual_metrics": individual_m,
    }
    return json.dumps(result)


analyze_portfolio_tool = StructuredTool(
    name="analyze_portfolio",
    description=(
        "Analyzes a weighted portfolio of assets. Computes both aggregate portfolio-level "
        "risk metrics AND individual ticker metrics. Use this when the user mentions a portfolio "
        "or asks about a collection of assets with weights. Returns JSON."
    ),
    func=_analyze_portfolio,
    args_schema=PortfolioInput,
)
