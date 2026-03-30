import json
import logging

from langchain_core.tools import StructuredTool

from finance.fetcher import fetch_multiple_tickers
from finance.metrics import correlation_matrix
from schemas.inputs import CorrelationInput

logger = logging.getLogger(__name__)


def _interpret_correlation(value: float) -> str:
    abs_v = abs(value)
    direction = "positively" if value >= 0 else "negatively"
    if abs_v >= 0.9:
        return f"{direction} correlated (very strong)"
    elif abs_v >= 0.7:
        return f"{direction} correlated (strong)"
    elif abs_v >= 0.5:
        return f"{direction} correlated (moderate)"
    elif abs_v >= 0.3:
        return f"{direction} correlated (weak)"
    else:
        return "uncorrelated"


def _analyze_correlation(tickers: list, period: str = "1y") -> str:
    """
    Computes pairwise correlation matrix for a list of tickers.
    """
    if len(tickers) < 2:
        return json.dumps({"error": "Need at least 2 tickers for correlation analysis."})

    data = fetch_multiple_tickers(tickers, period=period)
    returns_dict = {}
    errors = []
    for t, df in data.items():
        if df.empty:
            errors.append(f"No data for {t}")
        else:
            returns_dict[t.upper()] = df["returns"]

    if len(returns_dict) < 2:
        return json.dumps({"error": "Insufficient valid data", "details": errors})

    corr_df = correlation_matrix(returns_dict)
    matrix: dict = {}
    interpretations: dict = {}

    for col in corr_df.columns:
        matrix[col] = {}
        for row in corr_df.index:
            val = round(float(corr_df.loc[row, col]), 4)
            matrix[col][row] = val
            if col != row and f"{row}-{col}" not in interpretations:
                interpretations[f"{col}-{row}"] = _interpret_correlation(val)

    result = {
        "tickers": list(returns_dict.keys()),
        "period": period,
        "correlation_matrix": matrix,
        "interpretations": interpretations,
    }
    if errors:
        result["warnings"] = errors
    return json.dumps(result)


analyze_correlation_tool = StructuredTool(
    name="analyze_correlation",
    description=(
        "Computes pairwise return correlation matrix for a list of tickers over a given period. "
        "Use this to understand diversification benefits when comparing multiple assets. "
        "Returns JSON with correlation matrix and human-readable interpretations."
    ),
    func=_analyze_correlation,
    args_schema=CorrelationInput,
)
