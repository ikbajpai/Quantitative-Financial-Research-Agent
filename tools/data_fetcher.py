import json
import logging

from langchain_core.tools import StructuredTool

from finance.fetcher import fetch_price_history, fetch_ticker_info, DataFetchError
from schemas.inputs import FetchPriceDataInput

logger = logging.getLogger(__name__)


def _fetch_price_data(ticker: str, period: str = "1y", interval: str = "1d") -> str:
    """
    Fetches historical price data for a ticker and returns a JSON summary.
    Use this tool when you need raw price statistics before computing risk metrics.
    """
    try:
        df = fetch_price_history(ticker, period=period, interval=interval)
        info = fetch_ticker_info(ticker)
    except DataFetchError as e:
        return json.dumps({"error": str(e), "ticker": ticker})

    returns = df["returns"]
    summary = {
        "ticker": ticker.upper(),
        "name": info.get("longName", ticker),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "period": period,
        "interval": interval,
        "start_date": str(df.index.min().date()),
        "end_date": str(df.index.max().date()),
        "trading_days": len(df),
        "price_stats": {
            "start_price": round(float(df["close"].iloc[0]), 4),
            "end_price": round(float(df["close"].iloc[-1]), 4),
            "min_price": round(float(df["close"].min()), 4),
            "max_price": round(float(df["close"].max()), 4),
            "mean_close": round(float(df["close"].mean()), 4),
        },
        "return_stats": {
            "mean_daily_return": round(float(returns.mean()), 6),
            "std_daily_return": round(float(returns.std()), 6),
            "min_daily_return": round(float(returns.min()), 6),
            "max_daily_return": round(float(returns.max()), 6),
            "total_return": round(float((df["close"].iloc[-1] / df["close"].iloc[0]) - 1), 4),
        },
    }
    return json.dumps(summary)


fetch_price_data_tool = StructuredTool(
    name="fetch_price_data",
    description=(
        "Fetches historical OHLCV price data summary for a single ticker. "
        "Use this to inspect data availability and basic price statistics BEFORE computing metrics. "
        "Returns JSON with price stats, return stats, trading day count, and ticker metadata."
    ),
    func=_fetch_price_data,
    args_schema=FetchPriceDataInput,
)
