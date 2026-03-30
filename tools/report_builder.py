import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BuildReportInput(BaseModel):
    query: str = Field(description="The original user query")
    report_type: str = Field(
        description="'comparison' for multi-ticker comparison, 'portfolio' for portfolio analysis"
    )
    metrics_json: str = Field(
        description=(
            "JSON string containing the metrics data. "
            "For comparison: list of MetricsResult objects. "
            "For portfolio: dict with portfolio_metrics and individual_metrics."
        )
    )
    correlation_json: str = Field(
        default="{}",
        description="JSON string from analyze_correlation tool output (optional for portfolio)",
    )
    tickers: List[str] = Field(description="List of ticker symbols analyzed")
    period: str = Field(description="Analysis period used")
    benchmark: str = Field(default="^GSPC", description="Benchmark used")


def _build_final_report(
    query: str,
    report_type: str,
    metrics_json: str,
    correlation_json: str = "{}",
    tickers: List[str] = [],
    period: str = "5y",
    benchmark: str = "^GSPC",
) -> str:
    """
    Assembles all collected metrics into a final structured JSON report.
    ALWAYS call this tool last after collecting all metrics.
    """
    try:
        metrics_data = json.loads(metrics_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid metrics_json: {e}"})

    try:
        corr_data = json.loads(correlation_json) if correlation_json else {}
    except json.JSONDecodeError:
        corr_data = {}

    generated_at = datetime.utcnow().isoformat()

    if report_type == "comparison":
        if isinstance(metrics_data, list):
            all_metrics = metrics_data
        elif isinstance(metrics_data, dict) and "metrics" in metrics_data:
            all_metrics = metrics_data["metrics"]
        else:
            all_metrics = [metrics_data] if isinstance(metrics_data, dict) else []

        recommendation = _generate_comparison_recommendation(all_metrics)
        corr_matrix = corr_data.get("correlation_matrix", {})

        report = {
            "report_type": "comparison",
            "query": query,
            "tickers": tickers,
            "period": period,
            "benchmark": benchmark,
            "metrics": all_metrics,
            "correlation_matrix": corr_matrix,
            "recommendation": recommendation,
            "generated_at": generated_at,
        }

    elif report_type == "portfolio":
        if isinstance(metrics_data, dict):
            portfolio_m = metrics_data.get("portfolio_metrics", metrics_data)
            individual_m = metrics_data.get("individual_metrics", [])
            weights = metrics_data.get("weights", [1.0 / len(tickers)] * len(tickers))
        else:
            portfolio_m = {}
            individual_m = []
            weights = []

        recommendation = _generate_portfolio_recommendation(portfolio_m)

        report = {
            "report_type": "portfolio",
            "query": query,
            "tickers": tickers,
            "weights": weights,
            "period": period,
            "benchmark": benchmark,
            "portfolio_metrics": portfolio_m,
            "individual_metrics": individual_m,
            "recommendation": recommendation,
            "generated_at": generated_at,
        }
    else:
        report = {
            "report_type": report_type,
            "query": query,
            "data": metrics_data,
            "generated_at": generated_at,
        }

    return json.dumps(report, indent=2)


def _generate_comparison_recommendation(metrics_list: List[Dict[str, Any]]) -> str:
    if not metrics_list:
        return "Insufficient data to generate recommendation."

    valid = [m for m in metrics_list if isinstance(m, dict) and "sharpe_ratio" in m]
    if not valid:
        return "Unable to generate recommendation from the provided metrics."

    best_sharpe = max(valid, key=lambda x: x.get("sharpe_ratio") or -999)
    lowest_vol = min(valid, key=lambda x: x.get("annualized_volatility") or 999)
    best_return = max(valid, key=lambda x: x.get("annualized_return") or -999)

    parts = []
    best_ticker = best_sharpe.get("ticker", "N/A")
    best_sr = best_sharpe.get("sharpe_ratio")
    sr_str = f"{best_sr:.2f}" if best_sr else "N/A"
    parts.append(
        f"{best_ticker} offers the best risk-adjusted return with a Sharpe ratio of {sr_str}."
    )

    if lowest_vol["ticker"] != best_ticker:
        parts.append(
            f"{lowest_vol['ticker']} has the lowest volatility at "
            f"{lowest_vol.get('annualized_volatility', 0) * 100:.1f}%, "
            f"making it the most defensive choice."
        )

    if best_return["ticker"] != best_ticker:
        parts.append(
            f"{best_return['ticker']} leads on raw annualized return at "
            f"{best_return.get('annualized_return', 0) * 100:.1f}%, "
            f"but with higher associated risk."
        )

    tiers = [m.get("risk_tier") for m in valid if m.get("risk_tier")]
    if tiers:
        tier_strs = ", ".join(m["ticker"] + ": " + m["risk_tier"] for m in valid if m.get("risk_tier"))
        parts.append(f"Risk tiers: {tier_strs}.")

    return " ".join(parts)


def _generate_portfolio_recommendation(portfolio_m: Dict[str, Any]) -> str:
    if not portfolio_m:
        return "Insufficient portfolio data for recommendation."

    tier = portfolio_m.get("risk_tier", "Unknown")
    sharpe = portfolio_m.get("sharpe_ratio")
    vol = portfolio_m.get("annualized_volatility", 0)
    ret = portfolio_m.get("annualized_return", 0)
    mdd = portfolio_m.get("max_drawdown", 0)

    sharpe_str = f"{sharpe:.2f}" if sharpe else "N/A"
    rec = (
        f"The portfolio is classified as {tier} with an annualized return of "
        f"{ret * 100:.1f}% and volatility of {vol * 100:.1f}%. "
        f"Sharpe ratio: {sharpe_str}. Maximum drawdown: {abs(mdd) * 100:.1f}%. "
    )

    if sharpe and sharpe > 1.0:
        rec += "The portfolio demonstrates strong risk-adjusted performance."
    elif sharpe and sharpe > 0.5:
        rec += "The portfolio shows moderate risk-adjusted performance; consider rebalancing to improve efficiency."
    else:
        rec += "Consider reviewing asset allocation to improve the risk-return tradeoff."

    return rec


build_final_report_tool = StructuredTool(
    name="build_final_report",
    description=(
        "Assembles collected metrics into a final structured JSON report. "
        "ALWAYS call this tool LAST after you have gathered all metrics. "
        "Specify report_type='comparison' for multi-ticker comparisons, "
        "'portfolio' for portfolio analysis. "
        "Pass all previously computed metrics as metrics_json. "
        "This tool produces the final output that will be shown to the user."
    ),
    func=_build_final_report,
    args_schema=BuildReportInput,
)
