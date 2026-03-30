from typing import List, Optional
from pydantic import BaseModel, Field


class FetchPriceDataInput(BaseModel):
    ticker: str = Field(description="Stock/ETF ticker symbol, e.g. 'AAPL', 'SPY'")
    period: str = Field(
        default="1y",
        description=(
            "Time period for historical data. Options: '1d','5d','1mo','3mo','6mo',"
            "'1y','2y','5y','10y','ytd','max'"
        ),
    )
    interval: str = Field(
        default="1d",
        description="Data interval. Options: '1m','5m','15m','1h','1d','1wk','1mo'",
    )


class RiskCalculationInput(BaseModel):
    ticker: str = Field(description="Stock/ETF ticker symbol to analyze")
    period: str = Field(
        default="5y",
        description="Time period for analysis. Default '5y' for robust risk profiling.",
    )
    benchmark: str = Field(
        default="^GSPC",
        description="Benchmark ticker for beta/alpha. Default '^GSPC' (S&P 500)",
    )
    risk_free_rate: float = Field(
        default=0.0425,
        description="Annual risk-free rate as a decimal (e.g. 0.0425 for 4.25%)",
    )


class CorrelationInput(BaseModel):
    tickers: List[str] = Field(
        description="List of 2+ ticker symbols to compute pairwise correlations"
    )
    period: str = Field(
        default="1y",
        description="Time period over which to compute correlations",
    )


class PortfolioInput(BaseModel):
    tickers: List[str] = Field(description="List of ticker symbols in the portfolio")
    weights: Optional[List[float]] = Field(
        default=None,
        description=(
            "Portfolio weights (must sum to 1.0). If None, equal weights are used."
        ),
    )
    period: str = Field(default="3y", description="Analysis period")
    benchmark: str = Field(default="^GSPC", description="Benchmark ticker")


class ComparisonInput(BaseModel):
    tickers: List[str] = Field(
        description="List of 2+ ticker symbols to compare risk profiles"
    )
    period: str = Field(
        default="5y",
        description="Analysis period. Default '5y' for comprehensive risk comparison.",
    )
    benchmark: str = Field(default="^GSPC", description="Benchmark ticker for beta/alpha")
