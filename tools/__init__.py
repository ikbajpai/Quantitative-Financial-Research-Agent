from .data_fetcher import fetch_price_data_tool
from .risk_calculator import calculate_risk_metrics_tool
from .correlation_analyzer import analyze_correlation_tool
from .portfolio_analyzer import analyze_portfolio_tool
from .report_builder import build_final_report_tool
from .portfolio_optimizer import optimize_portfolio_tool
from .news_sentiment import news_sentiment_tool
from .sec_rag import sec_filing_rag_tool

ALL_TOOLS = [
    fetch_price_data_tool,
    calculate_risk_metrics_tool,
    analyze_correlation_tool,
    analyze_portfolio_tool,
    build_final_report_tool,
    optimize_portfolio_tool,
    news_sentiment_tool,
    sec_filing_rag_tool,
]

__all__ = ["ALL_TOOLS"]
