import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

_agent_cache: Dict[str, Any] = {}


class AnalyzeRequest(BaseModel):
    query: str
    model: Optional[str] = None
    use_cache: bool = True


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
