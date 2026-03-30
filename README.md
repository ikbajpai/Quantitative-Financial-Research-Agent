# Quantitative Financial Research Agent

> Ask a question. Get an institutional-grade risk report.

An AI-powered analyst built on **LangChain + LangGraph** that translates natural language queries into structured quantitative research reports. Ask it to compare fund risk profiles, analyze a portfolio, or deep-dive on a single stock — it fetches live data, runs the math, and returns clean JSON.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-ReAct%20Agent-green?logo=chainlink)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-orange)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-teal?logo=fastapi)
![Tests](https://img.shields.io/badge/Tests-37%20Passing-brightgreen?logo=pytest)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## What It Does

```
"Compare the risk profile of QQQ and SPY over the last 5 years"
                            │
                            ▼
              LangGraph ReAct Agent (Claude / GPT-4o)
                            │
           ┌────────────────┼────────────────┐
           ▼                ▼                ▼
   fetch_price_data  calculate_risk   analyze_correlation
                     _metrics
           └────────────────┼────────────────┘
                            ▼
                   build_final_report
                            │
                            ▼
              ┌─────────────────────────┐
              │  Structured JSON Report │
              │  + Rich terminal table  │
              └─────────────────────────┘
```

The agent is a **LangGraph ReAct loop** — it reasons, picks tools, executes them with live Yahoo Finance data, and assembles a typed Pydantic report. No hardcoded workflows; the LLM decides the tool call sequence based on the query.

---

## Features

- **Natural language interface** — no query syntax to learn
- **Live market data** via Yahoo Finance (`yfinance`)
- **10+ risk metrics** per asset: Sharpe, Sortino, Beta, Alpha, VaR, CVaR, Max Drawdown, Calmar, and more
- **Risk tier classification** — Conservative / Moderate / Aggressive / Speculative
- **Portfolio analysis** — weighted aggregate metrics + per-holding breakdown
- **Correlation matrix** — pairwise return correlations with interpretation labels
- **Structured JSON output** — all responses are Pydantic-validated, predictable, downstream-renderable
- **Response caching** — disk-based SHA256 cache, 1-hour TTL (no redundant API calls)
- **Dual interface** — Typer CLI with Rich tables + FastAPI REST server
- **Dual LLM support** — swap between Claude and GPT-4o via a single `.env` change

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent | LangGraph ReAct + LangChain |
| LLMs | Claude (`claude-sonnet-4-6`) · GPT-4o |
| Tools | `langchain_core.tools.StructuredTool` with Pydantic schemas |
| Market Data | Yahoo Finance (`yfinance`) |
| Data Processing | Pandas · NumPy · SciPy |
| Validation | Pydantic v2 |
| REST API | FastAPI + Uvicorn |
| CLI | Typer + Rich |
| Testing | Pytest (37 tests, offline via `mock_yfinance`) |

---

## Project Structure

```
├── agent/
│   ├── core.py          # Agent factory + run_query()
│   ├── prompts.py       # System prompt with tool-use rules & defaults
│   └── callbacks.py     # Logging callback handler
│
├── tools/               # 5 LangChain StructuredTools
│   ├── data_fetcher.py       # fetch_price_data
│   ├── risk_calculator.py    # calculate_risk_metrics
│   ├── correlation_analyzer.py
│   ├── portfolio_analyzer.py
│   └── report_builder.py     # build_final_report (always last)
│
├── finance/             # Pure Python — zero LangChain coupling
│   ├── fetcher.py       # yfinance wrapper
│   ├── metrics.py       # All risk math (Sharpe, Beta, VaR, etc.)
│   └── risk_profile.py  # Risk tier classification + narrative
│
├── schemas/
│   ├── inputs.py        # Tool args_schema (Pydantic BaseModels)
│   └── outputs.py       # MetricsResult, ComparisonReport, PortfolioReport
│
├── api/                 # FastAPI: POST /analyze · GET /health
├── cli/                 # Typer: analyze · batch · server · clear-cache
├── config/              # Pydantic BaseSettings (.env loader)
├── utils/               # Rich console formatting + disk cache
└── tests/               # 37 pytest unit tests (fully offline)
```

---

## Setup

### Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com) or [OpenAI API key](https://platform.openai.com)

### Install

```bash
git clone https://github.com/your-username/Quantitative-Financial-Research-Agent.git
cd Quantitative-Financial-Research-Agent

pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
```

Edit `.env` and set your API key:

```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-...

# Or for OpenAI:
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o
# OPENAI_API_KEY=sk-...
```

### Verify

```bash
python3 -m pytest tests/ -v
# 37 passed in ~2s (fully offline — no API calls needed for tests)
```

---

## Usage

### CLI

```bash
# Single stock risk profile
python3 -m cli.main analyze "What is the risk profile of NVDA over the last 5 years?"

# Compare two assets
python3 -m cli.main analyze "Compare QQQ and SPY risk over 3 years"

# Multi-ticker comparison
python3 -m cli.main analyze "Compare the risk profiles of AAPL, MSFT, and GOOGL"

# Portfolio analysis with weights
python3 -m cli.main analyze "Analyze a portfolio: 40% SPY, 30% QQQ, 20% TLT, 10% GLD"

# Output as raw JSON
python3 -m cli.main analyze "Compare QQQ and SPY" --output json

# Save report to file
python3 -m cli.main analyze "Compare QQQ and SPY" --save ./reports/qqqspy.json

# Batch mode (one query per line in a .txt file)
python3 -m cli.main batch queries.txt --output-dir ./reports/

# Start REST API server
python3 -m cli.main server --port 8000

# Clear response cache
python3 -m cli.main clear-cache
```

### REST API

```bash
# Start server
python3 -m cli.main server

# POST /analyze
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare AAPL and TSLA risk over 5 years"}'

# GET /health
curl http://localhost:8000/health
```

### Python

```python
from agent.core import create_financial_agent, run_query

agent = create_financial_agent()
report = run_query(agent, "Compare SPY and QQQ risk profiles over 3 years")

# Access structured fields
print(report["recommendation"])
for m in report["metrics"]:
    print(f"{m['ticker']}: Sharpe={m['sharpe_ratio']:.2f}, Tier={m['risk_tier']}")
```

---

## Metrics Reference

| Metric | Formula / Method |
|---|---|
| **Annualized Return** | Geometric mean: `((1+r).prod())^(252/n) - 1` |
| **Annualized Volatility** | `σ_daily × √252` |
| **Sharpe Ratio** | `(Ann. Return − Rf) / Ann. Volatility` |
| **Sortino Ratio** | `(Ann. Return − Rf) / Downside Deviation` |
| **Max Drawdown** | `min((cumulative − rolling_max) / rolling_max)` |
| **Calmar Ratio** | `(Ann. Return − Rf) / |Max Drawdown|` |
| **Beta** | OLS slope of asset returns on benchmark returns |
| **Jensen's Alpha** | `R_asset − [Rf + β(R_bm − Rf)]` |
| **VaR (95%)** | Historical 5th percentile of daily returns |
| **CVaR (95%)** | Mean of daily returns below VaR threshold |
| **Risk Tier** | Scored from volatility + drawdown + beta bands |

### Risk Tier Thresholds

| Tier | Annualized Volatility |
|---|---|
| Conservative | < 10% |
| Moderate | 10% – 20% |
| Aggressive | 20% – 35% |
| Speculative | > 35% |

---

## Example Output

```json
{
  "report_type": "comparison",
  "query": "Compare AAPL and MSFT risk over 5 years",
  "tickers": ["AAPL", "MSFT"],
  "period": "5y",
  "benchmark": "^GSPC",
  "metrics": [
    {
      "ticker": "AAPL",
      "period": "5y",
      "annualized_return": 0.2341,
      "annualized_volatility": 0.2812,
      "sharpe_ratio": 0.831,
      "sortino_ratio": 1.142,
      "max_drawdown": -0.3174,
      "calmar_ratio": 0.736,
      "beta": 1.21,
      "alpha": 0.0312,
      "var_95": -0.0241,
      "cvar_95": -0.0389,
      "risk_tier": "Aggressive",
      "risk_summary": "AAPL is classified as an Aggressive asset..."
    },
    {
      "ticker": "MSFT",
      "annualized_return": 0.2618,
      "annualized_volatility": 0.2534,
      "sharpe_ratio": 0.941,
      "risk_tier": "Aggressive"
    }
  ],
  "correlation_matrix": {
    "AAPL": { "AAPL": 1.0, "MSFT": 0.782 },
    "MSFT": { "AAPL": 0.782, "MSFT": 1.0 }
  },
  "recommendation": "MSFT offers the best risk-adjusted return with a Sharpe ratio of 0.94. Risk tiers: AAPL: Aggressive, MSFT: Aggressive.",
  "generated_at": "2026-03-31T10:00:00.000000"
}
```

---

## Configuration Reference

All settings loaded from `.env` (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` | `anthropic` or `openai` |
| `LLM_MODEL` | `claude-sonnet-4-6` | Model identifier |
| `ANTHROPIC_API_KEY` | — | Required when using Claude |
| `OPENAI_API_KEY` | — | Required when using GPT |
| `DEFAULT_RISK_FREE_RATE` | `0.0425` | Annual risk-free rate (4.25%) |
| `DEFAULT_BENCHMARK` | `^GSPC` | Benchmark for beta/alpha (S&P 500) |
| `CACHE_ENABLED` | `true` | Enable disk response cache |
| `CACHE_TTL_SECONDS` | `3600` | Cache lifetime (1 hour) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## Design Decisions

**Why separate `finance/` from `tools/`**
The entire `finance/` layer has zero LangChain dependency. Financial math can be unit-tested in isolation, reused outside the agent, and reasoned about without an LLM context.

**Why `build_final_report` is a tool**
Forcing the agent to call a report-assembly tool as its final step gives a deterministic stopping signal. Without it, the LLM might emit partial results mid-conversation. The tool also guarantees a consistent JSON schema regardless of query type.

**Why tools return JSON strings**
Returning a full 1,250-row DataFrame as tool output would overflow the LLM context window. Each tool returns a compact statistical summary — the numbers the LLM needs to reason about, not the raw data.

**Why file-based caching**
Yahoo Finance historical data doesn't change intraday. A SHA256-keyed JSON cache at `~/.quant-agent/cache/` with a 1-hour TTL eliminates redundant API calls with zero infrastructure overhead.

---

## License

MIT
