"""
Markowitz Mean-Variance Portfolio Optimization.
Pure Python/NumPy/SciPy — no LangChain dependency.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def _portfolio_performance(
    weights: np.ndarray,
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float,
    periods_per_year: int = 252,
) -> Tuple[float, float, float]:
    ret = float(np.dot(weights, mean_returns) * periods_per_year)
    vol = float(np.sqrt(weights @ cov_matrix @ weights) * np.sqrt(periods_per_year))
    sharpe = (ret - risk_free_rate) / vol if vol > 1e-10 else 0.0
    return ret, vol, sharpe


def _neg_sharpe(
    weights: np.ndarray,
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float,
) -> float:
    _, _, sharpe = _portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate)
    return -sharpe


def _portfolio_volatility(
    weights: np.ndarray,
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float,
) -> float:
    _, vol, _ = _portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate)
    return vol


def _build_stats(returns_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    mean_returns = returns_df.mean().values
    cov_matrix = returns_df.cov().values
    return mean_returns, cov_matrix


def _run_optimization(
    objective,
    n: int,
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float,
) -> Optional[np.ndarray]:
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = tuple((0.0, 1.0) for _ in range(n))
    init_weights = np.ones(n) / n

    result = minimize(
        objective,
        init_weights,
        args=(mean_returns, cov_matrix, risk_free_rate),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-9, "maxiter": 1000},
    )
    return result.x if result.success else None


def max_sharpe_portfolio(
    returns_df: pd.DataFrame,
    risk_free_rate: float = 0.0425,
) -> Dict:
    mean_returns, cov_matrix = _build_stats(returns_df)
    n = len(returns_df.columns)
    weights = _run_optimization(_neg_sharpe, n, mean_returns, cov_matrix, risk_free_rate)

    if weights is None:
        weights = np.ones(n) / n

    weights = np.clip(weights, 0, 1)
    weights /= weights.sum()

    ret, vol, sharpe = _portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate)
    return {
        "weights": dict(zip(returns_df.columns, [round(float(w), 4) for w in weights])),
        "annualized_return": round(ret, 6),
        "annualized_volatility": round(vol, 6),
        "sharpe_ratio": round(sharpe, 4),
        "optimization_target": "maximum_sharpe",
    }


def min_volatility_portfolio(
    returns_df: pd.DataFrame,
    risk_free_rate: float = 0.0425,
) -> Dict:
    mean_returns, cov_matrix = _build_stats(returns_df)
    n = len(returns_df.columns)
    weights = _run_optimization(_portfolio_volatility, n, mean_returns, cov_matrix, risk_free_rate)

    if weights is None:
        weights = np.ones(n) / n

    weights = np.clip(weights, 0, 1)
    weights /= weights.sum()

    ret, vol, sharpe = _portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate)
    return {
        "weights": dict(zip(returns_df.columns, [round(float(w), 4) for w in weights])),
        "annualized_return": round(ret, 6),
        "annualized_volatility": round(vol, 6),
        "sharpe_ratio": round(sharpe, 4),
        "optimization_target": "minimum_volatility",
    }


def efficient_frontier(
    returns_df: pd.DataFrame,
    n_points: int = 50,
    risk_free_rate: float = 0.0425,
) -> List[Dict]:
    mean_returns, cov_matrix = _build_stats(returns_df)
    n = len(returns_df.columns)

    # Find min and max return bounds
    min_ret = float(mean_returns.min() * 252)
    max_ret = float(mean_returns.max() * 252)
    target_returns = np.linspace(min_ret, max_ret, n_points)

    frontier_points = []
    for target in target_returns:
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
            {"type": "eq", "fun": lambda w, t=target: np.dot(w, mean_returns) * 252 - t},
        ]
        bounds = tuple((0.0, 1.0) for _ in range(n))
        result = minimize(
            _portfolio_volatility,
            np.ones(n) / n,
            args=(mean_returns, cov_matrix, risk_free_rate),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-9, "maxiter": 500},
        )
        if result.success:
            vol = float(result.fun)
            sharpe = (target - risk_free_rate) / vol if vol > 1e-10 else 0.0
            frontier_points.append({
                "annualized_return": round(target, 6),
                "annualized_volatility": round(vol, 6),
                "sharpe_ratio": round(sharpe, 4),
            })

    return frontier_points


def generate_rebalancing_advice(
    current_weights: Dict[str, float],
    optimal_weights: Dict[str, float],
    current_metrics: Dict,
    optimal_metrics: Dict,
) -> str:
    lines = []
    tickers = list(optimal_weights.keys())

    lines.append(
        f"Your current portfolio has a Sharpe ratio of "
        f"{current_metrics.get('sharpe_ratio', 0):.2f} and annualized volatility of "
        f"{current_metrics.get('annualized_volatility', 0) * 100:.1f}%."
    )
    lines.append(
        f"The optimal (Max Sharpe) portfolio achieves a Sharpe ratio of "
        f"{optimal_metrics.get('sharpe_ratio', 0):.2f} with volatility of "
        f"{optimal_metrics.get('annualized_volatility', 0) * 100:.1f}%."
    )
    lines.append("\nRecommended rebalancing actions:")

    for t in tickers:
        curr = current_weights.get(t, 0)
        opt = optimal_weights.get(t, 0)
        diff = opt - curr
        if abs(diff) < 0.01:
            lines.append(f"  {t}: Hold at {curr * 100:.1f}% (no significant change needed)")
        elif diff > 0:
            lines.append(f"  {t}: Increase from {curr * 100:.1f}% → {opt * 100:.1f}% (+{diff * 100:.1f}%)")
        else:
            lines.append(f"  {t}: Reduce from {curr * 100:.1f}% → {opt * 100:.1f}% ({diff * 100:.1f}%)")

    return "\n".join(lines)
