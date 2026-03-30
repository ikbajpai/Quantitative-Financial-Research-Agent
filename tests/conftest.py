from datetime import date, timedelta
from typing import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest


def _make_price_df(n: int = 252, seed: int = 42) -> pd.DataFrame:
    """Creates a synthetic daily OHLCV DataFrame."""
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0004, 0.01, n)
    prices = 100.0 * np.cumprod(1 + returns)

    dates = pd.bdate_range(end=date.today(), periods=n)
    df = pd.DataFrame(
        {
            "open": prices * (1 + rng.uniform(-0.005, 0.005, n)),
            "high": prices * (1 + rng.uniform(0, 0.01, n)),
            "low": prices * (1 - rng.uniform(0, 0.01, n)),
            "close": prices,
            "volume": rng.integers(1_000_000, 10_000_000, n),
        },
        index=dates,
    )
    df.index.name = "date"
    df["returns"] = df["close"].pct_change()
    df = df.dropna(subset=["returns"])
    return df


@pytest.fixture
def sample_price_df() -> pd.DataFrame:
    return _make_price_df(252, seed=42)


@pytest.fixture
def sample_returns(sample_price_df: pd.DataFrame) -> pd.Series:
    return sample_price_df["returns"]


@pytest.fixture
def benchmark_returns() -> pd.Series:
    return _make_price_df(252, seed=99)["returns"]


@pytest.fixture
def mock_yfinance():
    """Patches yfinance.Ticker to return synthetic data."""
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = _make_price_df(252)
    mock_ticker.info = {
        "longName": "Test Corp",
        "sector": "Technology",
        "industry": "Software",
        "marketCap": 1_000_000_000,
        "currency": "USD",
        "exchange": "NASDAQ",
    }

    with patch("yfinance.Ticker", return_value=mock_ticker) as mock:
        yield mock
