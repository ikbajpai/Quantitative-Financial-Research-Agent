"""
Quantitative Financial Research Agent — Streamlit Dashboard
Run with: streamlit run streamlit_app.py
"""

import json
import os
import sys
import time

import streamlit as st

# ── Page Config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="Quant Research Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    st.divider()

    llm_model = st.selectbox(
        "LLM Model",
        ["claude-sonnet-4-6", "claude-opus-4-6", "gpt-4o", "gpt-4o-mini"],
        index=0,
        help="Which model powers the agent",
    )

    default_period = st.selectbox(
        "Default Analysis Period",
        ["1y", "2y", "3y", "5y", "10y"],
        index=2,
    )

    st.divider()
    st.caption("**Example Queries**")
    examples = [
        "Compare the risk profile of AAPL and MSFT over 5 years",
        "What is the risk profile of NVDA?",
        "Analyze a portfolio: 60% SPY, 30% TLT, 10% GLD",
        "What are the main risks in TSLA's latest 10-K?",
        "What is the news sentiment for AMZN?",
        "Find the optimal weights for AAPL, MSFT, GOOGL, AMZN",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=ex):
            st.session_state["prefill_query"] = ex

    st.divider()
    if st.button("🗑️ Clear Cache", use_container_width=True):
        from utils.cache import ResponseCache
        count = ResponseCache().clear()
        st.success(f"Cleared {count} cached responses.")

    st.divider()
    st.caption("Built with LangChain · LangGraph · yfinance")

# ── Main Header ─────────────────────────────────────────────────────────────
st.title("📊 Quantitative Financial Research Agent")
st.caption(
    "Ask any financial question — the AI agent fetches live data, "
    "runs the math, and generates an institutional-grade report."
)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_research, tab_optimizer, tab_about = st.tabs(
    ["🔍 Research Agent", "⚖️ Portfolio Optimizer", "ℹ️ About"]
)

# ════════════════════════════════════════════════════════════════════════════
# TAB 1: RESEARCH AGENT
# ════════════════════════════════════════════════════════════════════════════
with tab_research:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and isinstance(msg["content"], dict):
                _render_report(msg["content"])
            else:
                st.write(msg["content"])

    # Prefill from sidebar example click
    prefill = st.session_state.pop("prefill_query", "")
    query = st.chat_input(
        "Ask anything: 'Compare AAPL and MSFT risk over 5 years'",
    ) or prefill

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            report = _run_agent(query, llm_model)
            st.session_state.messages.append({"role": "assistant", "content": report})
            _render_report(report)

    if st.session_state.messages:
        if st.button("🗑️ Clear conversation", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# TAB 2: PORTFOLIO OPTIMIZER
# ════════════════════════════════════════════════════════════════════════════
with tab_optimizer:
    st.subheader("Markowitz Efficient Frontier Optimizer")
    st.caption(
        "Enter tickers and optionally your current weights to get optimal allocations "
        "and a rebalancing strategy."
    )

    col_input, col_spacer = st.columns([2, 1])
    with col_input:
        tickers_input = st.text_input(
            "Tickers (comma-separated)",
            value="AAPL, MSFT, GOOGL, AMZN, NVDA",
            help="US-listed stock or ETF tickers",
        )
        current_weights_input = st.text_input(
            "Current weights (comma-separated, must sum to 1.0) — optional",
            value="",
            placeholder="e.g. 0.3, 0.25, 0.2, 0.15, 0.1",
            help="Leave blank for equal weights",
        )
        opt_period = st.selectbox(
            "Historical period for optimization",
            ["1y", "2y", "3y", "5y"],
            index=2,
        )
        opt_rfr = st.number_input(
            "Risk-free rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=4.25,
            step=0.25,
            help="Current annual risk-free rate",
        ) / 100

    if st.button("▶ Run Optimization", type="primary", use_container_width=False):
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        if len(tickers) < 2:
            st.error("Please enter at least 2 tickers.")
        else:
            current_weights = None
            if current_weights_input.strip():
                try:
                    cw = [float(w.strip()) for w in current_weights_input.split(",")]
                    if len(cw) != len(tickers):
                        st.error(f"Expected {len(tickers)} weights, got {len(cw)}.")
                        cw = None
                    elif abs(sum(cw) - 1.0) > 0.02:
                        st.error(f"Weights must sum to 1.0 (got {sum(cw):.3f}).")
                        cw = None
                    current_weights = cw
                except ValueError:
                    st.error("Invalid weights. Use comma-separated decimals (e.g. 0.4, 0.6).")

            with st.spinner("Running Markowitz optimization..."):
                result = _run_optimizer(tickers, current_weights, opt_period, opt_rfr)

            if "error" in result:
                st.error(result["error"])
            else:
                _render_optimizer_results(result)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3: ABOUT
# ════════════════════════════════════════════════════════════════════════════
with tab_about:
    st.subheader("About This Project")
    st.markdown("""
    **Quantitative Financial Research Agent** is an AI-powered analyst that combines:

    | Capability | Technology |
    |---|---|
    | Agent reasoning | LangGraph ReAct + LangChain |
    | LLM | Claude (Anthropic) or GPT-4o (OpenAI) |
    | Live market data | Yahoo Finance (`yfinance`) |
    | Risk metrics | NumPy · SciPy · Pandas |
    | Portfolio optimization | Markowitz Mean-Variance (SciPy SLSQP) |
    | News sentiment | yfinance headlines + LLM scoring |
    | SEC filings RAG | EDGAR API + FAISS + sentence-transformers |
    | Frontend | Streamlit + Plotly |
    | REST API | FastAPI + Uvicorn |
    | Observability | LangSmith tracing |

    **Metrics computed:** Sharpe · Sortino · Beta · Alpha · Max Drawdown · Calmar · VaR · CVaR

    **Built by:** Kanishk Bajpai
    """)


# ════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (defined after widgets so session_state is available)
# ════════════════════════════════════════════════════════════════════════════

def _run_agent(query: str, model: str) -> dict:
    from agent.core import create_financial_agent, run_query
    from utils.cache import ResponseCache
    from config import get_settings

    settings = get_settings()
    cache = ResponseCache(ttl_seconds=settings.CACHE_TTL_SECONDS, enabled=settings.CACHE_ENABLED)

    cached = cache.get(query, model)
    if cached:
        return cached

    tool_log = []

    with st.status("Running financial analysis...", expanded=True) as status:
        import logging
        from agent.callbacks import FinancialAgentCallbackHandler

        class StreamlitCallback(FinancialAgentCallbackHandler):
            def on_tool_start(self, serialized, input_str, *, run_id, **kwargs):
                name = serialized.get("name", "tool")
                tool_log.append(name)
                status.update(label=f"Calling `{name}`...")
                super().on_tool_start(serialized, input_str, run_id=run_id, **kwargs)

            def on_agent_finish(self, finish, **kwargs):
                status.update(label="Analysis complete!", state="complete")
                super().on_agent_finish(finish, **kwargs)

        try:
            agent = create_financial_agent(model_override=model)
            report = run_query(agent, query, extra_callbacks=[StreamlitCallback()])
        except Exception as e:
            status.update(label="Analysis failed", state="error")
            return {"error": str(e), "query": query}

    if tool_log:
        st.caption(f"Tools used: {' → '.join(tool_log)}")

    if "error" not in report:
        cache.set(query, report, model)

    return report


def _render_report(report: dict) -> None:
    from utils.charts import (
        plot_cumulative_returns,
        plot_drawdown,
        plot_correlation_heatmap,
        plot_metrics_bar,
    )

    if "error" in report:
        st.error(f"Error: {report['error']}")
        return

    report_type = report.get("report_type", "comparison")
    query = report.get("query", "")
    tickers = report.get("tickers", [])
    period = report.get("period", "1y")

    # Handle natural language responses
    if "response" in report and report_type not in ("comparison", "portfolio"):
        st.write(report["response"])
        return

    recommendation = report.get("recommendation", "")
    if recommendation:
        st.info(f"**Recommendation:** {recommendation}")

    if report_type == "comparison":
        metrics = report.get("metrics", [])
        if metrics and tickers:
            col1, col2 = st.columns(2)
            with col1:
                fig = plot_cumulative_returns(tickers, period)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = plot_drawdown(tickers, period)
                st.plotly_chart(fig, use_container_width=True)

            fig = plot_metrics_bar(metrics)
            st.plotly_chart(fig, use_container_width=True)

            corr = report.get("correlation_matrix", {})
            if corr:
                fig = plot_correlation_heatmap(corr)
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("Risk Metrics Detail")
            _render_metrics_table(metrics)

    elif report_type == "portfolio":
        from utils.charts import plot_portfolio_weights
        pm = report.get("portfolio_metrics")
        individual = report.get("individual_metrics", [])
        weights = report.get("weights", [])

        if tickers and period:
            col1, col2 = st.columns(2)
            with col1:
                fig = plot_cumulative_returns(tickers, period)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                if tickers and weights:
                    weight_dict = dict(zip(tickers, weights))
                    fig = plot_portfolio_weights(weight_dict, "Portfolio Allocation")
                    st.plotly_chart(fig, use_container_width=True)

        if pm:
            st.subheader("Portfolio Metrics")
            _render_metrics_table([pm])

        if individual:
            st.subheader("Individual Holdings")
            _render_metrics_table(individual)
    else:
        st.json(report)

    with st.expander("Raw JSON Report"):
        st.json(report)


def _render_metrics_table(metrics_list: list) -> None:
    import pandas as pd

    TIER_EMOJI = {
        "Conservative": "🟢",
        "Moderate": "🟡",
        "Aggressive": "🟠",
        "Speculative": "🔴",
    }

    rows = []
    for m in metrics_list:
        if not isinstance(m, dict):
            continue
        tier = m.get("risk_tier", "")
        rows.append({
            "Ticker": m.get("ticker", ""),
            "Ann. Return": f"{m.get('annualized_return', 0) * 100:.2f}%",
            "Ann. Volatility": f"{m.get('annualized_volatility', 0) * 100:.2f}%",
            "Sharpe": f"{m.get('sharpe_ratio') or 0:.3f}",
            "Sortino": f"{m.get('sortino_ratio') or 0:.3f}",
            "Max Drawdown": f"{m.get('max_drawdown', 0) * 100:.2f}%",
            "Beta": f"{m.get('beta', 0):.3f}",
            "Alpha": f"{m.get('alpha', 0) * 100:.2f}%",
            "VaR 95%": f"{m.get('var_95', 0) * 100:.2f}%",
            "Risk Tier": f"{TIER_EMOJI.get(tier, '')} {tier}",
        })

    if rows:
        df = pd.DataFrame(rows).set_index("Ticker")
        st.dataframe(df, use_container_width=True)


def _run_optimizer(
    tickers: list,
    current_weights,
    period: str,
    risk_free_rate: float,
) -> dict:
    from tools.portfolio_optimizer import _optimize_portfolio
    import json

    raw = _optimize_portfolio(
        tickers=tickers,
        current_weights=current_weights,
        period=period,
        risk_free_rate=risk_free_rate,
        include_frontier=True,
    )
    try:
        return json.loads(raw)
    except Exception:
        return {"error": "Optimization failed to return valid JSON."}


def _render_optimizer_results(result: dict) -> None:
    from utils.charts import (
        plot_efficient_frontier,
        plot_portfolio_weights,
    )

    max_sharpe = result.get("max_sharpe_portfolio", {})
    min_vol = result.get("min_volatility_portfolio", {})
    current = result.get("current_portfolio")
    frontier = result.get("efficient_frontier", [])

    if frontier:
        fig = plot_efficient_frontier(frontier, max_sharpe, min_vol, current)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⭐ Max Sharpe Portfolio")
        if max_sharpe.get("weights"):
            fig = plot_portfolio_weights(max_sharpe["weights"], "Max Sharpe Weights")
            st.plotly_chart(fig, use_container_width=True)
        st.metric("Sharpe Ratio", f"{max_sharpe.get('sharpe_ratio', 0):.3f}")
        st.metric("Ann. Return", f"{max_sharpe.get('annualized_return', 0) * 100:.2f}%")
        st.metric("Ann. Volatility", f"{max_sharpe.get('annualized_volatility', 0) * 100:.2f}%")

    with col2:
        st.subheader("🛡️ Min Volatility Portfolio")
        if min_vol.get("weights"):
            fig = plot_portfolio_weights(min_vol["weights"], "Min Vol Weights")
            st.plotly_chart(fig, use_container_width=True)
        st.metric("Sharpe Ratio", f"{min_vol.get('sharpe_ratio', 0):.3f}")
        st.metric("Ann. Return", f"{min_vol.get('annualized_return', 0) * 100:.2f}%")
        st.metric("Ann. Volatility", f"{min_vol.get('annualized_volatility', 0) * 100:.2f}%")

    if result.get("rebalancing_advice"):
        st.subheader("📋 Rebalancing Strategy")
        st.info(result["rebalancing_advice"])

    with st.expander("Full Optimization Data (JSON)"):
        st.json({k: v for k, v in result.items() if k != "efficient_frontier"})
