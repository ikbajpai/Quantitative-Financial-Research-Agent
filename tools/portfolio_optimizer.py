import json
import logging
from typing import List, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from finance.fetcher import fetch_multiple_tickers
from finance.optimizer import (
    efficient_frontier,
    generate_rebalancing_advice,
    max_sharpe_portfolio,
    min_volatility_portfolio,
)
from finance import metrics as m

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class PortfolioOptimizerInput(BaseModel):
    tickers: List[str] = Field(description="List of ticker symbols to optimize across")
    current_weights: Optional[List[float]] = Field(
        default=None,
        description=(
            "User's current portfolio weights (must sum to 1.0). "
            "If provided, generates a rebalancing recommendation."
        ),
    )
    period: str = Field(
        default="3y",
        description="Historical period for estimating expected returns and covariance",
    )
    risk_free_rate: float = Field(
        default=0.0425,
        description="Annual risk-free rate as a decimal",
    )
    include_frontier: bool = Field(
        default=False,
        description="Set True to include efficient frontier data points (used for charts)",
    )


def _optimize_portfolio(
    tickers: List[str],
    current_weights: Optional[List[float]] = None,
    period: str = "3y",
    risk_free_rate: float = 0.0425,
    include_frontier: bool = False,
) -> str:
    data = fetch_multiple_tickers(tickers, period=period)
    returns_dict = {}
    for t, df in data.items():
        if not df.empty:
            returns_dict[t.upper()] = df["returns"]

    if len(returns_dict) < 2:
        return json.dumps({"error": "Need at least 2 valid tickers for optimization."})

    returns_df = pd.DataFrame(returns_dict).dropna()
    valid_tickers = list(returns_df.columns)

    max_sharpe = max_sharpe_portfolio(returns_df, risk_free_rate)
    min_vol = min_volatility_portfolio(returns_df, risk_free_rate)

    result = {
        "tickers": valid_tickers,
        "period": period,
        "risk_free_rate": risk_free_rate,
        "max_sharpe_portfolio": max_sharpe,
        "min_volatility_portfolio": min_vol,
    }

    if current_weights is not None and len(current_weights) == len(valid_tickers):
        w_array = np.array(current_weights, dtype=float)
        w_array = w_array / w_array.sum()
        portfolio_returns = returns_df.values @ w_array
        portfolio_series = pd.Series(portfolio_returns, index=returns_df.index)

        current_metrics = {
            "sharpe_ratio": m.sharpe_ratio(portfolio_series, risk_free_rate),
            "annualized_volatility": m.annualized_volatility(portfolio_series),
            "annualized_return": m.annualized_return(portfolio_series),
        }
        current_weight_dict = dict(zip(valid_tickers, [round(float(w), 4) for w in w_array]))

        result["current_portfolio"] = {
            "weights": current_weight_dict,
            **{k: round(v, 4) if v is not None else None for k, v in current_metrics.items()},
        }
        result["rebalancing_advice"] = generate_rebalancing_advice(
            current_weight_dict,
            max_sharpe["weights"],
            current_metrics,
            max_sharpe,
        )

    if include_frontier:
        frontier = efficient_frontier(returns_df, n_points=30, risk_free_rate=risk_free_rate)
        result["efficient_frontier"] = frontier

    return json.dumps(result)


optimize_portfolio_tool = StructuredTool(
    name="optimize_portfolio",
    description=(
        "Runs Markowitz Mean-Variance portfolio optimization on a set of tickers. "
        "Returns the Maximum Sharpe Ratio portfolio weights AND the Minimum Volatility portfolio weights. "
        "If current_weights are provided, also generates a plain-English rebalancing strategy. "
        "Use this when the user asks: 'What is the optimal allocation for these assets?' "
        "or 'How should I rebalance my portfolio?' Returns JSON."
    ),
    func=_optimize_portfolio,
    args_schema=PortfolioOptimizerInput,
)
