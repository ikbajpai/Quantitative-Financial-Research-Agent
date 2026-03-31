import json
import logging
from typing import Optional

import yfinance as yf
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_SENTIMENT_PROMPT = """You are a financial news analyst. Given the following recent news headlines for {ticker},
analyze the overall market sentiment.

Headlines:
{headlines}

Respond ONLY with a valid JSON object in this exact format:
{{
  "overall_sentiment": "Bullish" | "Bearish" | "Neutral",
  "confidence": 0.0-1.0,
  "key_themes": ["theme1", "theme2", "theme3"],
  "bullish_signals": ["signal1", "signal2"],
  "bearish_signals": ["signal1", "signal2"],
  "analyst_note": "One sentence summary of the news landscape"
}}"""


class NewsSentimentInput(BaseModel):
    ticker: str = Field(description="Stock ticker symbol to fetch news for")
    max_headlines: int = Field(
        default=10,
        description="Number of recent headlines to analyze (5-20 recommended)",
    )


def _analyze_news_sentiment(ticker: str, max_headlines: int = 10) -> str:
    try:
        t = yf.Ticker(ticker)
        news_items = t.news or []
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch news for {ticker}: {e}"})

    if not news_items:
        return json.dumps({
            "ticker": ticker.upper(),
            "overall_sentiment": "Neutral",
            "confidence": 0.0,
            "key_themes": [],
            "bullish_signals": [],
            "bearish_signals": [],
            "analyst_note": "No recent news found for this ticker.",
            "headlines_analyzed": 0,
        })

    headlines = []
    for item in news_items[:max_headlines]:
        content = item.get("content", {})
        if isinstance(content, dict):
            title = content.get("title", "")
            provider = content.get("provider", {})
            if isinstance(provider, dict):
                source = provider.get("displayName", "")
            else:
                source = str(provider)
        else:
            title = item.get("title", "")
            source = item.get("publisher", "")
        if title:
            headlines.append(f"- [{source}] {title}")

    if not headlines:
        return json.dumps({
            "ticker": ticker.upper(),
            "overall_sentiment": "Neutral",
            "confidence": 0.0,
            "key_themes": [],
            "bullish_signals": [],
            "bearish_signals": [],
            "analyst_note": "Could not extract headlines from news data.",
            "headlines_analyzed": 0,
        })

    headlines_text = "\n".join(headlines)

    try:
        from config import get_settings
        import os
        settings = get_settings()
        if settings.GROQ_API_KEY and settings.LLM_PROVIDER == "groq":
            from langchain_groq import ChatGroq
            os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
            llm = ChatGroq(model=settings.LLM_MODEL, temperature=0)
        else:
            llm = init_chat_model(settings.LLM_MODEL)
        prompt = _SENTIMENT_PROMPT.format(ticker=ticker.upper(), headlines=headlines_text)
        response = llm.invoke([HumanMessage(content=prompt)])
        content_str = response.content.strip()

        # Strip markdown code fences if present
        if content_str.startswith("```"):
            lines = content_str.split("\n")
            content_str = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        sentiment_data = json.loads(content_str)
        sentiment_data["ticker"] = ticker.upper()
        sentiment_data["headlines_analyzed"] = len(headlines)
        sentiment_data["sample_headlines"] = headlines[:3]
        return json.dumps(sentiment_data)

    except json.JSONDecodeError:
        return json.dumps({
            "ticker": ticker.upper(),
            "overall_sentiment": "Neutral",
            "confidence": 0.5,
            "analyst_note": "Sentiment analysis completed but response format was unexpected.",
            "headlines_analyzed": len(headlines),
        })
    except Exception as e:
        logger.error("Sentiment LLM call failed for %s: %s", ticker, e)
        return json.dumps({"error": f"Sentiment analysis failed: {e}", "ticker": ticker})


news_sentiment_tool = StructuredTool(
    name="analyze_news_sentiment",
    description=(
        "Fetches recent news headlines for a ticker and uses AI to score market sentiment. "
        "Returns: overall sentiment (Bullish/Bearish/Neutral), confidence score, key themes, "
        "bullish/bearish signals, and an analyst note. "
        "Use this to complement quantitative risk metrics with qualitative market context. "
        "Returns JSON."
    ),
    func=_analyze_news_sentiment,
    args_schema=NewsSentimentInput,
)
