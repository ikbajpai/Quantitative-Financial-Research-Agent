from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router
from finance.fetcher import DataFetchError

try:
    from groq import RateLimitError as GroqRateLimitError
except ImportError:
    GroqRateLimitError = None

app = FastAPI(
    title="Quantitative Financial Research Agent",
    description="AI-powered quantitative risk analysis for stocks, ETFs, and portfolios.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DataFetchError)
async def data_fetch_error_handler(request: Request, exc: DataFetchError):
    return JSONResponse(
        status_code=503,
        content={"error": "Data fetch failed", "detail": str(exc)},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid input", "detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    # Surface Groq rate limit errors as readable JSON
    exc_str = str(exc)
    if "rate_limit_exceeded" in exc_str or "Rate limit reached" in exc_str:
        import re
        wait = re.search(r"try again in (\S+)", exc_str)
        wait_str = wait.group(1) if wait else "some time"
        return JSONResponse(
            status_code=429,
            content={
                "error": f"Groq API rate limit reached. Please try again in {wait_str}.",
                "detail": "Free tier daily token limit exhausted. Consider upgrading or waiting.",
            },
        )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": exc_str[:300]},
    )


app.include_router(router, prefix="/api")

# Serve frontend static files
_frontend_dir = Path(__file__).parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(str(_frontend_dir / "index.html"))
