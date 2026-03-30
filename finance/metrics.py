from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats


def align_returns(
    returns_a: pd.Series, returns_b: pd.Series
) -> Tuple[pd.Series, pd.Series]:
    aligned = pd.concat([returns_a, returns_b], axis=1, join="inner").dropna()
    return aligned.iloc[:, 0], aligned.iloc[:, 1]


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    if len(returns) == 0:
        return 0.0
    total = (1 + returns).prod()
    n = len(returns)
    return float(total ** (periods_per_year / n) - 1)


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    if len(returns) < 2:
        return 0.0
    return float(returns.std() * np.sqrt(periods_per_year))


def sharpe_ratio(
    returns: pd.Series, risk_free_rate: float = 0.0425, periods_per_year: int = 252
) -> Optional[float]:
    vol = annualized_volatility(returns, periods_per_year)
    if vol < 1e-10:
        return None
    ann_ret = annualized_return(returns, periods_per_year)
    return float((ann_ret - risk_free_rate) / vol)


def sortino_ratio(
    returns: pd.Series, risk_free_rate: float = 0.0425, periods_per_year: int = 252
) -> Optional[float]:
    downside = returns[returns < 0]
    if len(downside) < 2:
        return None
    downside_vol = float(downside.std() * np.sqrt(periods_per_year))
    if downside_vol == 0:
        return None
    ann_ret = annualized_return(returns, periods_per_year)
    return float((ann_ret - risk_free_rate) / downside_vol)


def max_drawdown(returns: pd.Series) -> float:
    if len(returns) == 0:
        return 0.0
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    return float(drawdown.min())


def calmar_ratio(
    returns: pd.Series, risk_free_rate: float = 0.0425
) -> Optional[float]:
    mdd = abs(max_drawdown(returns))
    if mdd == 0:
        return None
    ann_ret = annualized_return(returns)
    return float((ann_ret - risk_free_rate) / mdd)


def beta(asset_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    a, b = align_returns(asset_returns, benchmark_returns)
    if len(a) < 2:
        return 1.0
    slope, _, _, _, _ = stats.linregress(b.values, a.values)
    return float(slope)


def alpha(
    asset_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.0425,
    periods_per_year: int = 252,
) -> float:
    b = beta(asset_returns, benchmark_returns)
    a_aligned, bm_aligned = align_returns(asset_returns, benchmark_returns)
    ann_asset = annualized_return(a_aligned, periods_per_year)
    ann_bm = annualized_return(bm_aligned, periods_per_year)
    return float(ann_asset - (risk_free_rate + b * (ann_bm - risk_free_rate)))


def correlation_matrix(returns_dict: Dict[str, pd.Series]) -> pd.DataFrame:
    df = pd.DataFrame(returns_dict).dropna()
    return df.corr()


def value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
    if len(returns) == 0:
        return 0.0
    return float(np.percentile(returns, (1 - confidence) * 100))


def conditional_var(returns: pd.Series, confidence: float = 0.95) -> float:
    var = value_at_risk(returns, confidence)
    tail = returns[returns <= var]
    if len(tail) == 0:
        return var
    return float(tail.mean())
