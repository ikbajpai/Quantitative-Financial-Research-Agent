from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router
from finance.fetcher import DataFetchError

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


app.include_router(router, prefix="/api")

# Serve frontend static files
_frontend_dir = Path(__file__).parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(str(_frontend_dir / "index.html"))
