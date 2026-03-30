from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MetricsResult(BaseModel):
    ticker: str
    period: str
    annualized_return: float = Field(description="Annualized return as decimal")
    annualized_volatility: float = Field(description="Annualized volatility as decimal")
    sharpe_ratio: Optional[float] = Field(default=None, description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(default=None, description="Sortino ratio")
    max_drawdown: float = Field(description="Maximum drawdown as negative decimal")
    calmar_ratio: Optional[float] = Field(default=None, description="Calmar ratio")
    beta: float = Field(description="Beta relative to benchmark")
    alpha: float = Field(description="Jensen's alpha (annualized)")
    var_95: float = Field(description="Value at Risk at 95% confidence (daily)")
    cvar_95: float = Field(description="Conditional VaR / Expected Shortfall (daily)")
    risk_tier: str = Field(description="Risk classification: Conservative/Moderate/Aggressive/Speculative")
    risk_summary: str = Field(description="Human-readable risk narrative")


class ComparisonReport(BaseModel):
    query: str = Field(description="The original user query")
    tickers: List[str]
    period: str
    benchmark: str
    metrics: List[MetricsResult]
    correlation_matrix: Dict[str, Dict[str, float]] = Field(
        description="Pairwise correlation matrix keyed by ticker"
    )
    recommendation: str = Field(
        description="Brief investment recommendation based on comparative metrics"
    )
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PortfolioReport(BaseModel):
    query: str = Field(description="The original user query")
    tickers: List[str]
    weights: List[float]
    period: str
    benchmark: str
    portfolio_metrics: MetricsResult
    individual_metrics: List[MetricsResult]
    recommendation: str = Field(description="Portfolio-level recommendation")
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
