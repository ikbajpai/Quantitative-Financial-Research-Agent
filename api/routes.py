import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

_agent_cache: Dict[str, Any] = {}


class AnalyzeRequest(BaseModel):
    query: str
    model: Optional[str] = None
    use_cache: bool = True


class OptimizeRequest(BaseModel):
    tickers: List[str]
    current_weights: Optional[List[float]] = None
    period: str = "3y"
    risk_free_rate: float = 0.0425


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_provider: str
    llm_model: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    from config import get_settings
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.LLM_MODEL,
    )


@router.post("/analyze")
async def analyze(request: AnalyzeRequest) -> Dict[str, Any]:
    from config import get_settings
    from agent.core import create_financial_agent, run_query
    from utils.cache import ResponseCache

    settings = get_settings()
    model_name = request.model or settings.LLM_MODEL

    cache = ResponseCache(
        ttl_seconds=settings.CACHE_TTL_SECONDS,
        enabled=(settings.CACHE_ENABLED and request.use_cache),
    )

    cached = cache.get(request.query, model_name)
    if cached:
        logger.info("Returning cached result for query: %s...", request.query[:50])
        return cached

    agent_key = model_name
    if agent_key not in _agent_cache:
        _agent_cache[agent_key] = create_financial_agent(model_override=model_name)

    agent = _agent_cache[agent_key]
    result = run_query(agent, request.query)

    if "error" not in result:
        cache.set(request.query, result, model_name)

    return result


@router.get("/prices")
async def get_prices(
    tickers: str = Query(..., description="Comma-separated ticker symbols"),
    period: str = Query("1y", description="Time period: 1y, 3y, 5y, etc."),
) -> Dict[str, Any]:
    """Returns historical price series for chart rendering."""
    from finance.fetcher import fetch_multiple_tickers

    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        return {}

    data = fetch_multiple_tickers(ticker_list, period=period)
    result: Dict[str, Any] = {}

    for ticker, df in data.items():
        if df.empty:
            continue
        returns = df["returns"].dropna()
        if len(returns) < 2:
            continue
        cum = (1 + returns).cumprod()
        drawdown = ((cum / cum.cummax()) - 1) * 100
        result[ticker] = {
            "dates": [str(d.date()) for d in returns.index],
            "close": [round(float(v), 2) for v in df.loc[returns.index, "close"]],
            "cumulative_returns": [round(float(v), 3) for v in (cum - 1) * 100],
            "drawdown": [round(float(v), 3) for v in drawdown],
        }

    return result


@router.post("/optimize")
async def optimize_direct(request: OptimizeRequest) -> Dict[str, Any]:
    """Direct portfolio optimization endpoint (bypasses the agent)."""
    from tools.portfolio_optimizer import _optimize_portfolio

    raw = _optimize_portfolio(
        tickers=request.tickers,
        current_weights=request.current_weights,
        period=request.period,
        risk_free_rate=request.risk_free_rate,
        include_frontier=True,
    )
    return json.loads(raw)
