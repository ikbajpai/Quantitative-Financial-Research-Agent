# Quantitative Financial Research Agent

> Ask a question. Get an institutional-grade research report.

An AI-powered financial analyst built on **LangChain + LangGraph** that translates natural language queries into structured quantitative and qualitative research reports. It fetches live market data, computes 10+ risk metrics, scores news sentiment, reads SEC filings via RAG, and optimizes portfolios using Markowitz theory — all from a single query.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-ReAct%20Agent-green?logo=chainlink)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-orange)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-teal?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit)
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
              │   (Claude / GPT-4o)              │
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
                    ┌────────▼────────┐
                    │ Structured JSON │  →  Streamlit Dashboard
                    │ + Rich CLI table│  →  FastAPI REST API
                    └─────────────────┘
```

---

## Features

### Core (Quantitative)
- **Live market data** — Yahoo Finance historical OHLCV
- **10+ risk metrics per asset** — Sharpe, Sortino, Beta, Alpha, Max Drawdown, Calmar, VaR (95%), CVaR (95%)
- **Risk tier classification** — Conservative / Moderate / Aggressive / Speculative
- **Multi-asset correlation matrix** with interpretation labels
- **Portfolio analysis** — weighted aggregate + per-holding breakdown

### Feature 1 — News Sentiment (Unstructured Data)
- Fetches latest headlines for any ticker via **Yahoo Finance news**
- Uses the LLM to score **Bullish / Bearish / Neutral** sentiment with confidence
- Extracts **key themes**, bullish signals, bearish signals, and an analyst note
- Bridges quantitative math with qualitative market context

### Feature 2 — Portfolio Optimizer (Markowitz)
- **Efficient Frontier** computed via `scipy.optimize` SLSQP
- Returns **Maximum Sharpe Ratio** portfolio weights
- Returns **Minimum Volatility** portfolio weights
- If current weights provided → generates a plain-English **rebalancing strategy**

### Feature 3 — SEC Filings RAG (Fundamental Analysis)
- Fetches latest **10-K or 10-Q** directly from **SEC EDGAR** (no API key needed)
- Extracts Risk Factors (Item 1A) and MD&A (Item 7) sections
- Chunks and indexes text in **FAISS** vector store
- Uses **sentence-transformers** embeddings + RAG to answer specific analyst questions
- Returns: answer, key points, risks mentioned, sentiment

### Feature 4 — Agent Observability (LangSmith)
- Full **LangSmith tracing** — every tool call, token, and reasoning step logged
- Enable with two `.env` variables: `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY`
- Visual graph of every agent run at [smith.langchain.com](https://smith.langchain.com)

### Feature 5 — Streamlit Dashboard + Docker
- Interactive **chat interface** with tool-call progress indicator
- **Plotly charts**: cumulative returns, drawdown curves, correlation heatmap, metrics bars
- **Efficient Frontier visualizer** with Max Sharpe ⭐ and Min Vol 💎 markers
- **Donut charts** for portfolio weight allocation
- Full **Docker** setup: `Dockerfile` + `Dockerfile.streamlit` + `docker-compose.yml`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent | LangGraph ReAct + LangChain |
| LLMs | Claude (`claude-sonnet-4-6`) · GPT-4o |
| Tools | `langchain_core.tools.StructuredTool` + Pydantic v2 schemas |
| Market Data | Yahoo Finance (`yfinance`) |
| SEC Filings | SEC EDGAR API (free, no key needed) |
| RAG | FAISS + `sentence-transformers/all-MiniLM-L6-v2` |
| Portfolio Optimization | SciPy SLSQP (Markowitz Mean-Variance) |
| Data Processing | Pandas · NumPy · SciPy |
| Validation | Pydantic v2 |
| REST API | FastAPI + Uvicorn |
| CLI | Typer + Rich |
| Frontend | Streamlit + Plotly |
| Observability | LangSmith |
| Containers | Docker + Docker Compose |
| Testing | Pytest (37 tests, fully offline) |

---

## Project Structure

```
├── agent/
│   ├── core.py          # Agent factory + run_query()
│   ├── prompts.py       # System prompt (tool rules, defaults, conventions)
│   └── callbacks.py     # Logging + Streamlit callback handler
│
├── tools/               # 8 LangChain StructuredTools
│   ├── data_fetcher.py           # fetch_price_data
│   ├── risk_calculator.py        # calculate_risk_metrics
│   ├── correlation_analyzer.py   # analyze_correlation
│   ├── portfolio_analyzer.py     # analyze_portfolio
│   ├── portfolio_optimizer.py    # optimize_portfolio  ← NEW
│   ├── news_sentiment.py         # analyze_news_sentiment  ← NEW
│   ├── sec_rag.py                # analyze_sec_filing (RAG)  ← NEW
│   └── report_builder.py         # build_final_report
│
├── finance/             # Pure Python — zero LangChain coupling
│   ├── fetcher.py       # yfinance wrapper
│   ├── metrics.py       # Risk math (Sharpe, Beta, VaR, etc.)
│   ├── risk_profile.py  # Risk tier classification
│   └── optimizer.py     # Markowitz optimization  ← NEW
│
├── schemas/
│   ├── inputs.py        # Tool args_schema (Pydantic BaseModels)
│   └── outputs.py       # MetricsResult, ComparisonReport, PortfolioReport
│
├── utils/
│   ├── formatting.py    # Rich terminal tables
│   ├── cache.py         # Disk-based SHA256 response cache
│   └── charts.py        # Plotly chart builders  ← NEW
│
├── api/                 # FastAPI: POST /analyze · GET /health
├── cli/                 # Typer: analyze · batch · server · clear-cache
├── config/              # Pydantic BaseSettings (.env loader)
│
├── streamlit_app.py     # Streamlit dashboard (3 tabs)  ← NEW
├── Dockerfile           # FastAPI container
├── Dockerfile.streamlit # Streamlit container  ← NEW
├── docker-compose.yml   # Orchestrates both services  ← NEW
└── tests/               # 37 pytest unit tests (fully offline)
```

---

## Setup

### Prerequisites
- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com) or [OpenAI API key](https://platform.openai.com)

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
# Required
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-...

# Optional — LangSmith observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=quant-research-agent
```

### Verify

```bash
python3 -m pytest tests/ -v
# 37 passed in ~2s (no API calls needed)
```

---

## Usage

### Streamlit Dashboard (Recommended)

```bash
streamlit run streamlit_app.py
# Opens at http://localhost:8501
```

The dashboard has three tabs:
- **Research Agent** — chat interface, auto-renders Plotly charts from agent output
- **Portfolio Optimizer** — Efficient Frontier visualizer with rebalancing advice
- **About** — project info and tech stack

### CLI

```bash
# Risk profile
python3 -m cli.main analyze "What is the risk profile of NVDA over 5 years?"

# Multi-ticker comparison
python3 -m cli.main analyze "Compare AAPL, MSFT, and GOOGL risk"

# Portfolio analysis
python3 -m cli.main analyze "Analyze portfolio: 40% SPY, 30% QQQ, 20% TLT, 10% GLD"

# Portfolio optimization
python3 -m cli.main analyze "What are the optimal weights for AAPL, MSFT, GOOGL, AMZN?"

# News sentiment
python3 -m cli.main analyze "What is the current news sentiment for TSLA?"

# SEC filing analysis (RAG)
python3 -m cli.main analyze "What are the main AI competition risks in NVDA's latest 10-K?"

# Full research report (quant + qualitative)
python3 -m cli.main analyze "Full research report on AAPL: risk metrics, news sentiment, and 10-K highlights"

# Output options
python3 -m cli.main analyze "Compare QQQ and SPY" --output json
python3 -m cli.main analyze "Compare QQQ and SPY" --save ./report.json

# Batch queries from file
python3 -m cli.main batch queries.txt --output-dir ./reports/

# Start REST API server
python3 -m cli.main server --port 8000
```

### REST API

```bash
# Start
python3 -m cli.main server

# Analyze
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare AAPL and TSLA risk over 5 years"}'

# Health
curl http://localhost:8000/health
```

### Docker

```bash
cp .env.example .env
# Add your API keys to .env

docker-compose up --build

# FastAPI  → http://localhost:8000
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
| `LLM_PROVIDER` | `anthropic` | `anthropic` or `openai` |
| `LLM_MODEL` | `claude-sonnet-4-6` | Model identifier |
| `ANTHROPIC_API_KEY` | — | Required for Claude |
| `OPENAI_API_KEY` | — | Required for GPT |
| `DEFAULT_RISK_FREE_RATE` | `0.0425` | Annual risk-free rate |
| `DEFAULT_BENCHMARK` | `^GSPC` | Benchmark ticker |
| `CACHE_ENABLED` | `true` | Disk response cache |
| `CACHE_TTL_SECONDS` | `3600` | Cache lifetime (1 hr) |
| `LANGCHAIN_TRACING_V2` | `false` | Enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | — | LangSmith API key |
| `LANGCHAIN_PROJECT` | `quant-financial-research-agent` | LangSmith project name |

---

## Design Decisions

**Why separate `finance/` from `tools/`**
The `finance/` layer has zero LangChain dependency. All math is unit-testable in isolation, reusable without an LLM, and verified independently of agent behavior.

**Why `build_final_report` is a tool**
Forces a deterministic stopping condition. Without it, the LLM might emit partial results mid-conversation. The tool guarantees a consistent Pydantic-validated JSON schema regardless of query type.

**Why tools return JSON strings (not DataFrames)**
A 1,250-row DataFrame as tool output would overflow the LLM context window. Each tool returns a compact statistical summary — exactly the numbers the agent needs to reason about.

**Why FAISS + sentence-transformers for RAG**
Works fully offline after the first model download (~90MB). No embedding API cost, no per-token billing, and `all-MiniLM-L6-v2` is well-calibrated for financial text similarity.

**Why file-based caching**
Yahoo Finance historical data doesn't change intraday. A SHA256-keyed JSON cache at `~/.quant-agent/cache/` with a 1-hour TTL eliminates redundant API calls with zero infrastructure overhead.

---

## License

MIT © [Kanishk Bajpai](https://github.com/ikbajpai)
