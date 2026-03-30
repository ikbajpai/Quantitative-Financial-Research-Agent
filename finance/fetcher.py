import time
import logging
from typing import Dict, List

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class DataFetchError(Exception):
    pass


def fetch_price_history(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval)
    except Exception as e:
        raise DataFetchError(f"Failed to fetch data for {ticker}: {e}") from e

    if df.empty:
        raise DataFetchError(f"No data returned for ticker '{ticker}'. Check the symbol.")

    df.columns = [c.lower() for c in df.columns]
    df.index.name = "date"

    if "close" not in df.columns:
        raise DataFetchError(f"Unexpected data format for ticker '{ticker}'.")

    df["returns"] = df["close"].pct_change()
    df = df.dropna(subset=["returns"])
    return df


def fetch_ticker_info(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
    except Exception as e:
        logger.warning("Could not fetch info for %s: %s", ticker, e)
        return {"ticker": ticker}

    keys = ["longName", "sector", "industry", "marketCap", "currency", "exchange"]
    return {k: info.get(k) for k in keys} | {"ticker": ticker}


def fetch_multiple_tickers(
    tickers: List[str],
    period: str = "1y",
    interval: str = "1d",
) -> Dict[str, pd.DataFrame]:
    results: Dict[str, pd.DataFrame] = {}
    for i, ticker in enumerate(tickers):
        if i > 0:
            time.sleep(0.3)
        try:
            results[ticker] = fetch_price_history(ticker, period=period, interval=interval)
        except DataFetchError as e:
            logger.error("Skipping %s: %s", ticker, e)
            results[ticker] = pd.DataFrame()
    return results


def period_to_label(period: str) -> str:
    mapping = {
        "1d": "1 Day", "5d": "5 Days", "1mo": "1 Month",
        "3mo": "3 Months", "6mo": "6 Months", "1y": "1 Year",
        "2y": "2 Years", "5y": "5 Years", "10y": "10 Years",
        "ytd": "Year-to-Date", "max": "All Time",
    }
    return mapping.get(period, period)
