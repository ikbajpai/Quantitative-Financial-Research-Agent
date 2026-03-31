# Quantitative Financial Research Agent

> Ask a question. Get an institutional-grade research report.

An AI-powered financial analyst built on **LangChain + LangGraph** that translates natural language queries into structured quantitative and qualitative research reports. It fetches live market data, computes 10+ risk metrics, scores news sentiment, reads SEC filings via RAG, and optimizes portfolios using Markowitz theory — all from a single query.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-ReAct%20Agent-green?logo=chainlink)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-orange)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-teal?logo=fastapi)
![Groq](https://img.shields.io/badge/Groq-Free%20LLM-purple)
![Tests](https://img.shields.io/badge/Tests-37%20Passing-brightgreen?logo=pytest)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## What It Does

```
"Compare AAPL and MSFT risk. Check sentiment and what their 10-Ks say."
                               │
                               ▼
              ┌─────────────────────────────────┐
              │   LangGraph ReAct Agent          │
              │   Llama 3.3 70B (Groq / free)   │
              │   Claude · GPT-4o (optional)     │
              └──────────────┬──────────────────┘
                             │ Picks tools based on query
      ┌──────────┬───────────┼────────────┬──────────────┐
      ▼          ▼           ▼            ▼              ▼
fetch_price  calculate   analyze_     analyze_       optimize_
_data        _risk       news_        sec_filing     portfolio
             _metrics    sentiment    (RAG)
      └──────────┴───────────┴────────────┴──────────────┘
                             │
                             ▼
                    build_final_report
                             │
              ┌──────────────▼──────────────┐
              │     Structured JSON          │
              └──────────────┬──────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       Web UI (Vanilla   FastAPI REST    Streamlit
       JS + Plotly.js)   API + Auth      Dashboard
```

---

## Features

### Core — Quantitative Risk Engine
- **Live market data** via Yahoo Finance historical OHLCV
- **10+ risk metrics per asset** — Sharpe, Sortino, Beta, Alpha, Max Drawdown, Calmar, VaR (95%), CVaR (95%)
- **Risk tier classification** — Conservative / Moderate / Aggressive / Speculative
- **Multi-asset correlation matrix** with interpretation labels
- **Portfolio analysis** — weighted aggregate + per-holding breakdown

### Feature 1 — News Sentiment (Unstructured Data)
- Fetches latest headlines for any ticker via Yahoo Finance
- LLM scores **Bullish / Bearish / Neutral** sentiment with confidence
- Extracts key themes, bullish/bearish signals, and an analyst note

### Feature 2 — Portfolio Optimizer (Markowitz)
- **Efficient Frontier** computed via `scipy.optimize` SLSQP
- **Maximum Sharpe Ratio** and **Minimum Volatility** portfolio weights
- If current weights provided → plain-English **rebalancing strategy**
- Interactive frontier chart with ⭐ Max Sharpe and 💎 Min Vol markers

### Feature 3 — SEC Filings RAG (Fundamental Analysis)
- Fetches latest **10-K or 10-Q** from **SEC EDGAR** (no API key needed)
- Extracts Risk Factors (Item 1A) and MD&A (Item 7)
- Chunks and indexes in **FAISS** with sentence-transformers embeddings
- Answers specific analyst questions via RAG

### Feature 4 — Web UI (Vanilla JS + Plotly.js)
- Dark-themed single-page app served at **http://localhost:8000**
- **Research Agent tab** — natural language queries, animated tool progress, metric cards
- **Portfolio Optimizer tab** — ticker tag input, efficient frontier chart, weight bars
- Interactive Plotly charts: cumulative returns, drawdown, correlation heatmap
- No React, no build step — pure HTML/CSS/JS

### Feature 5 — Google OAuth2 Authentication
- Full **Google Sign-In** flow — login overlay before accessing the app
- JWT stored as httpOnly cookie (7-day expiry)
- User avatar, name, and logout button in sidebar
- **Dev mode** — if Google credentials not set, auth is skipped automatically

### Feature 6 — Agent Observability (LangSmith)
- Full **LangSmith tracing** — every tool call, token, and reasoning step logged
- Enable with `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY`

### Feature 7 — Docker
- `Dockerfile` for FastAPI, `Dockerfile.streamlit` for Streamlit
- `docker-compose.yml` orchestrates both services

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent | LangGraph ReAct + LangChain |
| LLMs | **Llama 3.3 70B via Groq (free)** · Claude · GPT-4o |
| Tools | `langchain_core.tools.StructuredTool` + Pydantic v2 |
| Market Data | Yahoo Finance (`yfinance`) |
| SEC Filings | SEC EDGAR API (free, no key) |
| RAG | FAISS + `sentence-transformers/all-MiniLM-L6-v2` |
| Portfolio Optimization | SciPy SLSQP (Markowitz Mean-Variance) |
| Data Processing | Pandas · NumPy · SciPy |
| REST API | FastAPI + Uvicorn |
| Web UI | Vanilla JS + Plotly.js (CDN) |
| Auth | Google OAuth2 + JWT (`authlib`, `python-jose`) |
| CLI | Typer + Rich |
| Dashboard | Streamlit + Plotly |
| Observability | LangSmith |
| Containers | Docker + Docker Compose |
| Testing | Pytest (37 tests, fully offline) |

---

## Project Structure

```
├── agent/
│   ├── core.py              # Agent factory + run_query() with parallel-tool fallback
│   ├── prompts.py           # System prompt (tool rules, defaults, conventions)
│   └── callbacks.py         # Logging + Streamlit callback handler
│
├── auth/                    # Google OAuth2 + JWT
│   ├── jwt_utils.py         # Token creation & verification
│   └── dependencies.py      # FastAPI Depends — validates Bearer / cookie
│
├── tools/                   # 8 LangChain StructuredTools
│   ├── data_fetcher.py           # fetch_price_data
│   ├── risk_calculator.py        # calculate_risk_metrics
│   ├── correlation_analyzer.py   # analyze_correlation
│   ├── portfolio_analyzer.py     # analyze_portfolio
│   ├── portfolio_optimizer.py    # optimize_portfolio
│   ├── news_sentiment.py         # analyze_news_sentiment
│   ├── sec_rag.py                # analyze_sec_filing (RAG)
│   └── report_builder.py         # build_final_report
│
├── finance/                 # Pure Python — zero LangChain coupling
│   ├── fetcher.py           # yfinance wrapper
│   ├── metrics.py           # Risk math (Sharpe, Beta, VaR, etc.)
│   ├── risk_profile.py      # Risk tier classification
│   └── optimizer.py         # Markowitz optimization
│
├── api/
│   ├── app.py               # FastAPI app, middleware, error handlers
│   ├── routes.py            # /api/analyze · /api/prices · /api/optimize · /api/health
│   └── auth_routes.py       # /auth/login · /auth/callback · /auth/logout · /auth/me
│
├── frontend/                # Vanilla JS web UI
│   ├── index.html           # Single-page app (login overlay + main app)
│   ├── app.js               # Auth check, report rendering, Plotly charts
│   └── style.css            # Dark navy theme, glassmorphism cards
│
├── config/settings.py       # Pydantic BaseSettings (.env loader)
├── utils/
│   ├── cache.py             # SHA256 disk-based response cache (1-hr TTL)
│   ├── charts.py            # Plotly chart builders (Streamlit)
│   └── formatting.py        # Rich terminal tables (CLI)
│
├── cli/main.py              # Typer CLI: analyze · batch · server · clear-cache
├── streamlit_app.py         # Streamlit dashboard (3 tabs)
├── Dockerfile
├── Dockerfile.streamlit
├── docker-compose.yml
└── tests/                   # 37 pytest unit tests (fully offline)
```

---

## Setup

### Prerequisites
- Python 3.10+
- A free [Groq API key](https://console.groq.com) (recommended) **or** Anthropic/OpenAI key

### Install

```bash
git clone https://github.com/ikbajpai/Quantitative-Financial-Research-Agent.git
cd Quantitative-Financial-Research-Agent

pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
# --- LLM (choose one) ---

# Option A: Groq — FREE, no credit card required
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=gsk_...          # get at console.groq.com

# Option B: Anthropic Claude
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-sonnet-4-6
# ANTHROPIC_API_KEY=sk-ant-...

# Option C: OpenAI GPT-4o
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o
# OPENAI_API_KEY=sk-...

# --- Google OAuth2 (optional — skip for dev mode) ---
# GOOGLE_CLIENT_ID=....apps.googleusercontent.com
# GOOGLE_CLIENT_SECRET=GOCSPX-...
# SECRET_KEY=your-random-secret-key
# BASE_URL=http://localhost:8000

# --- LangSmith Observability (optional) ---
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=ls__...
```

### Verify

```bash
python3 -m pytest tests/ -v
# 37 passed in ~2s (no API calls needed)
```

---

## Usage

### Web UI (Recommended)

```bash
python3 -m uvicorn api.app:app --host 0.0.0.0 --port 8000
# Opens at http://localhost:8000
```

Two tabs:
- **Research Agent** — type any financial question, get a structured report with interactive charts
- **Portfolio Optimizer** — enter tickers, see the efficient frontier and optimal weights

Example queries to try:
```
Compare the risk profile of AAPL and MSFT over 5 years
What is the news sentiment for TSLA?
Analyze portfolio: 40% SPY, 30% QQQ, 20% TLT, 10% GLD
What are the main risks in NVDA's latest 10-K?
```

### CLI

```bash
# Risk profile
python3 -m cli.main analyze "What is the risk profile of NVDA over 5 years?"

# Multi-ticker comparison
python3 -m cli.main analyze "Compare AAPL, MSFT, and GOOGL risk"

# Portfolio analysis
python3 -m cli.main analyze "Analyze portfolio: 40% SPY, 30% QQQ, 20% TLT, 10% GLD"

# News sentiment
python3 -m cli.main analyze "What is the current news sentiment for TSLA?"

# SEC filing analysis (RAG)
python3 -m cli.main analyze "What are the main AI competition risks in NVDA's latest 10-K?"

# Save output
python3 -m cli.main analyze "Compare QQQ and SPY" --output json --save ./report.json

# Batch queries from file
python3 -m cli.main batch queries.txt --output-dir ./reports/

# Start server
python3 -m cli.main server --port 8000
```

### REST API

```bash
# Start
python3 -m uvicorn api.app:app --port 8000

# Analyze
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare AAPL and TSLA risk over 5 years"}'

# Direct portfolio optimization (no LLM needed)
curl -X POST http://localhost:8000/api/optimize \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL","MSFT","GOOGL"], "period": "3y"}'

# Historical price series for charts
curl "http://localhost:8000/api/prices?tickers=AAPL,MSFT&period=1y"

# Health check
curl http://localhost:8000/api/health
```

### Streamlit Dashboard

```bash
streamlit run streamlit_app.py
# Opens at http://localhost:8501
```

### Docker

```bash
cp .env.example .env
# Add your API keys to .env

docker-compose up --build
# FastAPI   → http://localhost:8000
# Streamlit → http://localhost:8501
```

### Python SDK

```python
from agent.core import create_financial_agent, run_query

agent = create_financial_agent()
report = run_query(agent, "Compare SPY and QQQ risk over 3 years")

for m in report["metrics"]:
    print(f"{m['ticker']}: Sharpe={m['sharpe_ratio']:.2f}, Tier={m['risk_tier']}")
```

---

## Google OAuth2 Setup

The app runs without authentication by default (dev mode). To enable Google Login:

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → **APIs & Services → Credentials → Create OAuth 2.0 Client ID**
2. Application type: **Web application**
3. Fill in the two separate fields:
   - **Authorized JavaScript origins**: `http://localhost:8000` *(no path, no trailing slash)*
   - **Authorized redirect URIs**: `http://localhost:8000/auth/callback`
4. Add to `.env`:
   ```env
   GOOGLE_CLIENT_ID=....apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-...
   SECRET_KEY=any-random-32-char-string
   BASE_URL=http://localhost:8000
   ```
5. Restart the server — the login overlay appears automatically.

---

## Metrics Reference

| Metric | Formula |
|---|---|
| **Annualized Return** | `((1+r).prod())^(252/n) - 1` |
| **Annualized Volatility** | `σ_daily × √252` |
| **Sharpe Ratio** | `(R_ann − Rf) / σ_ann` |
| **Sortino Ratio** | `(R_ann − Rf) / Downside_σ_ann` |
| **Max Drawdown** | `min((cum − rolling_max) / rolling_max)` |
| **Calmar Ratio** | `(R_ann − Rf) / |Max Drawdown|` |
| **Beta** | OLS slope: asset returns ~ benchmark returns |
| **Jensen's Alpha** | `R_asset − [Rf + β(R_bm − Rf)]` |
| **VaR (95%)** | Historical 5th percentile of daily returns |
| **CVaR (95%)** | Mean of daily returns below VaR threshold |

### Risk Tiers

| Tier | Annualized Volatility |
|---|---|
| 🟢 Conservative | < 10% |
| 🟡 Moderate | 10% – 20% |
| 🟠 Aggressive | 20% – 35% |
| 🔴 Speculative | > 35% |

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `groq`, `anthropic`, or `openai` |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Model identifier |
| `GROQ_API_KEY` | — | Free at console.groq.com |
| `ANTHROPIC_API_KEY` | — | Required for Claude |
| `OPENAI_API_KEY` | — | Required for GPT |
| `DEFAULT_RISK_FREE_RATE` | `0.0425` | Annual risk-free rate |
| `DEFAULT_BENCHMARK` | `^GSPC` | Benchmark ticker |
| `CACHE_ENABLED` | `true` | Disk response cache |
| `CACHE_TTL_SECONDS` | `3600` | Cache lifetime (1 hr) |
| `GOOGLE_CLIENT_ID` | — | Google OAuth2 Client ID |
| `GOOGLE_CLIENT_SECRET` | — | Google OAuth2 Client Secret |
| `SECRET_KEY` | auto-generated | JWT signing key |
| `BASE_URL` | `http://localhost:8000` | OAuth2 redirect base URL |
| `LANGCHAIN_TRACING_V2` | `false` | Enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | — | LangSmith API key |
| `LANGCHAIN_PROJECT` | `quant-financial-research-agent` | LangSmith project name |

---

## Design Decisions

**Why separate `finance/` from `tools/`**
The `finance/` layer has zero LangChain dependency. All math is unit-testable in isolation, reusable without an LLM, and verified independently of agent behavior.

**Why Groq + Llama 3.3 70B as default**
Groq's free tier gives 100K tokens/day with ~300 token/s throughput — fast enough for real-time use. Llama 3.3 70B fully supports tool calling, making it a zero-cost alternative to Claude/GPT-4o for most queries.

**Why `build_final_report` is a tool**
Forces a deterministic stopping condition. The tool guarantees a consistent JSON schema regardless of query type — the frontend always knows what to render.

**Why tools return JSON strings (not DataFrames)**
A 1,250-row DataFrame as tool output would overflow the LLM context window. Each tool returns a compact statistical summary — exactly the numbers the agent needs to reason about.

**Handling Groq parallel tool calls**
Groq/Llama sometimes calls `calculate_risk_metrics` and `build_final_report` simultaneously. `run_query()` detects this and reconstructs the report from raw tool outputs rather than the empty parallel-called report.

**Why FAISS + sentence-transformers for RAG**
Works fully offline after the first model download (~90MB). No embedding API cost and `all-MiniLM-L6-v2` is well-calibrated for financial text similarity.

**Why file-based caching**
Yahoo Finance historical data doesn't change intraday. A SHA256-keyed JSON cache at `~/.quant-agent/cache/` with a 1-hour TTL eliminates redundant API calls with zero infrastructure overhead.

---

## License

MIT © [Kanishk Bajpai](https://github.com/ikbajpai)
