import json
import logging
from typing import Any, Dict, List, Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
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

    llm = init_chat_model(model_name)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    agent = create_react_agent(
        model=llm_with_tools,
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
    final_message = messages[-1] if messages else None

    if final_message is None:
        return {"error": "No response from agent", "query": query}

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
