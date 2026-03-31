from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_PROVIDER: str = "anthropic"
    LLM_MODEL: str = "claude-sonnet-4-6"

    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    DEFAULT_RISK_FREE_RATE: float = 0.0425
    DEFAULT_BENCHMARK: str = "^GSPC"

    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600

    LOG_LEVEL: str = "INFO"

    # News Sentiment (optional — uses yfinance if not set)
    NEWS_API_KEY: Optional[str] = None

    # LangSmith Observability (Feature 4)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "quant-financial-research-agent"

    # Google OAuth2
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    SECRET_KEY: str = "3f2e65d7c433cafe93cd7b07cdd4200cc89cfda7319fa5393f7c605e3625a194"
    BASE_URL: str = "http://localhost:8000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
