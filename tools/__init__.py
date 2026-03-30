from .data_fetcher import fetch_price_data_tool
from .risk_calculator import calculate_risk_metrics_tool
from .correlation_analyzer import analyze_correlation_tool
from .portfolio_analyzer import analyze_portfolio_tool
from .report_builder import build_final_report_tool

ALL_TOOLS = [
    fetch_price_data_tool,
    calculate_risk_metrics_tool,
    analyze_correlation_tool,
    analyze_portfolio_tool,
    build_final_report_tool,
]

__all__ = ["ALL_TOOLS"]
