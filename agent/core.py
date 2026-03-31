import json
import logging
from typing import Any, Dict, List, Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from agent.prompts import SYSTEM_PROMPT
from agent.callbacks import FinancialAgentCallbackHandler
from tools import ALL_TOOLS
from config import get_settings

logger = logging.getLogger(__name__)


def create_financial_agent(model_override: Optional[str] = None):
    """
    Creates and returns the LangGraph ReAct financial research agent.
    """
    settings = get_settings()
    model_name = model_override or settings.LLM_MODEL

    if settings.GROQ_API_KEY and settings.LLM_PROVIDER == "groq":
        import os
        from langchain_groq import ChatGroq
        os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
        llm = ChatGroq(model=model_name, temperature=0)
    else:
        llm = init_chat_model(model_name)

    # Pass raw llm — create_react_agent handles tool binding internally
    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
    )

    logger.info("Financial agent created with model: %s", model_name)
    return agent


def run_query(
    agent: Any,
    query: str,
    verbose: bool = False,
    extra_callbacks: Optional[List] = None,
) -> Dict[str, Any]:
    """
    Runs a query through the agent and returns the structured result.
    """
    callbacks = [FinancialAgentCallbackHandler(verbose=verbose)]
    if extra_callbacks:
        callbacks.extend(extra_callbacks)

    config = {"callbacks": callbacks}

    result = agent.invoke(
        {"messages": [HumanMessage(content=query)]},
        config=config,
    )

    messages = result.get("messages", [])
    if not messages:
        return {"error": "No response from agent", "query": query}

    # First priority: find a build_final_report ToolMessage with real metrics.
    # Groq/Llama may call tools in parallel so the report ToolMessage may have
    # empty metrics if calculate_risk_metrics ran at the same time. In that case
    # we fall back to reconstructing the report from the raw tool outputs.
    build_report_msg: Optional[str] = None
    raw_metrics_list: List[Dict] = []
    portfolio_raw: Optional[Dict] = None

    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        content_str = msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
        try:
            data = json.loads(content_str)
        except (json.JSONDecodeError, ValueError):
            continue

        if not isinstance(data, dict):
            continue

        # Collect build_final_report output
        if "report_type" in data:
            metrics_ok = (
                ("metrics" in data and data["metrics"] and
                 any(len(m) > 5 for m in data["metrics"] if isinstance(m, dict)))
                or
                ("portfolio_metrics" in data and data["portfolio_metrics"])
            )
            if metrics_ok:
                return data  # perfect — full report with real metrics
            build_report_msg = data  # keep as fallback (has structure, but empty metrics)

        # Collect calculate_risk_metrics results for reconstruction fallback
        if "ticker" in data and "annualized_return" in data:
            raw_metrics_list.append(data)

        # Collect analyze_portfolio result
        if "portfolio_metrics" in data and "individual_metrics" in data:
            portfolio_raw = data

    # Fallback: reconstruct from raw tool outputs
    if portfolio_raw:
        from tools.report_builder import _build_final_report
        report_str = _build_final_report(
            query=query,
            report_type="portfolio",
            metrics_json=json.dumps(portfolio_raw),
            tickers=portfolio_raw.get("tickers", []),
            period=portfolio_raw.get("period", "3y"),
        )
        return json.loads(report_str)

    if raw_metrics_list:
        tickers = [m.get("ticker", "") for m in raw_metrics_list]
        period = raw_metrics_list[0].get("period", "5y")
        from tools.report_builder import _build_final_report
        report_str = _build_final_report(
            query=query,
            report_type="comparison",
            metrics_json=json.dumps(raw_metrics_list),
            tickers=tickers,
            period=period,
        )
        return json.loads(report_str)

    # Last resort: natural language from final message
    final_message = messages[-1]
    content = final_message.content if hasattr(final_message, "content") else str(final_message)

    report_data = _extract_json_report(content)
    if report_data:
        return report_data

    return {
        "query": query,
        "response": content,
        "note": "Response is in natural language format",
    }


def _extract_json_report(content: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to extract a JSON report from the agent's response content.
    Handles cases where JSON is embedded in text.
    """
    if not content:
        return None

    content = content.strip()

    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    import re
    json_pattern = re.compile(r'\{[\s\S]*\}', re.MULTILINE)
    matches = json_pattern.findall(content)

    for match in reversed(matches):
        try:
            data = json.loads(match)
            if isinstance(data, dict) and ("metrics" in data or "portfolio_metrics" in data):
                return data
        except (json.JSONDecodeError, ValueError):
            continue

    return None
