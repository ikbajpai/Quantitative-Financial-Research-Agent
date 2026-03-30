"""
Plotly chart builders for the Streamlit dashboard.
All functions return plotly.graph_objects.Figure objects.
"""

from typing import Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


COLORS = px.colors.qualitative.Set2


def plot_cumulative_returns(
    tickers: List[str],
    period: str = "1y",
) -> go.Figure:
    import yfinance as yf

    fig = go.Figure()
    for i, ticker in enumerate(tickers):
        try:
            df = yf.Ticker(ticker).history(period=period)
            if df.empty:
                continue
            cumret = (1 + df["Close"].pct_change().dropna()).cumprod() - 1
            fig.add_trace(go.Scatter(
                x=cumret.index,
                y=cumret.values * 100,
                name=ticker,
                line=dict(color=COLORS[i % len(COLORS)], width=2),
                hovertemplate=f"<b>{ticker}</b><br>Date: %{{x|%Y-%m-%d}}<br>Return: %{{y:.2f}}%<extra></extra>",
            ))
        except Exception:
            continue

    fig.update_layout(
        title=f"Cumulative Returns ({period})",
        xaxis_title="Date",
        yaxis_title="Cumulative Return (%)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0", zeroline=True, zerolinecolor="#888", zerolinewidth=1),
        xaxis=dict(gridcolor="#f0f0f0"),
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#888", opacity=0.5)
    return fig


def plot_drawdown(
    tickers: List[str],
    period: str = "1y",
) -> go.Figure:
    import yfinance as yf

    fig = go.Figure()
    for i, ticker in enumerate(tickers):
        try:
            df = yf.Ticker(ticker).history(period=period)
            if df.empty:
                continue
            closes = df["Close"]
            cumulative = (1 + closes.pct_change().dropna()).cumprod()
            rolling_max = cumulative.cummax()
            drawdown = (cumulative - rolling_max) / rolling_max * 100

            fig.add_trace(go.Scatter(
                x=drawdown.index,
                y=drawdown.values,
                name=ticker,
                fill="tozeroy",
                line=dict(color=COLORS[i % len(COLORS)], width=1.5),
                fillcolor=COLORS[i % len(COLORS)].replace("rgb", "rgba").replace(")", ", 0.15)"),
                hovertemplate=f"<b>{ticker}</b><br>Date: %{{x|%Y-%m-%d}}<br>Drawdown: %{{y:.2f}}%<extra></extra>",
            ))
        except Exception:
            continue

    fig.update_layout(
        title=f"Drawdown ({period})",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0"),
        xaxis=dict(gridcolor="#f0f0f0"),
    )
    return fig


def plot_correlation_heatmap(correlation_matrix: Dict[str, Dict[str, float]]) -> go.Figure:
    if not correlation_matrix:
        return go.Figure()

    tickers = list(correlation_matrix.keys())
    z = [[correlation_matrix[r].get(c, 0) for c in tickers] for r in tickers]
    text = [[f"{correlation_matrix[r].get(c, 0):.3f}" for c in tickers] for r in tickers]

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=tickers,
        y=tickers,
        text=text,
        texttemplate="%{text}",
        textfont={"size": 13},
        colorscale="RdYlGn",
        zmid=0,
        zmin=-1,
        zmax=1,
        colorbar=dict(title="Correlation"),
    ))

    fig.update_layout(
        title="Return Correlation Matrix",
        xaxis_title="",
        yaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


def plot_metrics_bar(metrics_list: List[Dict]) -> go.Figure:
    if not metrics_list:
        return go.Figure()

    tickers = [m.get("ticker", f"Asset {i}") for i, m in enumerate(metrics_list)]
    metric_keys = [
        ("Sharpe Ratio", "sharpe_ratio", 1.0),
        ("Sortino Ratio", "sortino_ratio", 1.0),
        ("Calmar Ratio", "calmar_ratio", 1.0),
        ("Beta", "beta", 1.0),
    ]

    fig = make_subplots(
        rows=1, cols=len(metric_keys),
        subplot_titles=[m[0] for m in metric_keys],
    )

    for col_idx, (label, key, _) in enumerate(metric_keys, 1):
        values = [m.get(key) or 0 for m in metrics_list]
        colors = [COLORS[i % len(COLORS)] for i in range(len(tickers))]
        fig.add_trace(
            go.Bar(
                x=tickers,
                y=values,
                name=label,
                marker_color=colors,
                showlegend=False,
                hovertemplate=f"<b>%{{x}}</b><br>{label}: %{{y:.3f}}<extra></extra>",
            ),
            row=1, col=col_idx,
        )

    fig.update_layout(
        title="Risk-Adjusted Performance Metrics",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=350,
    )
    for i in range(1, len(metric_keys) + 1):
        fig.update_yaxes(gridcolor="#f0f0f0", row=1, col=i)
        fig.update_xaxes(gridcolor="#f0f0f0", row=1, col=i)

    return fig


def plot_efficient_frontier(
    frontier_points: List[Dict],
    max_sharpe: Optional[Dict] = None,
    min_vol: Optional[Dict] = None,
    current_portfolio: Optional[Dict] = None,
) -> go.Figure:
    if not frontier_points:
        return go.Figure()

    vols = [p["annualized_volatility"] * 100 for p in frontier_points]
    rets = [p["annualized_return"] * 100 for p in frontier_points]
    sharpes = [p["sharpe_ratio"] for p in frontier_points]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=vols,
        y=rets,
        mode="lines+markers",
        name="Efficient Frontier",
        line=dict(color="#4A90D9", width=2),
        marker=dict(
            size=6,
            color=sharpes,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Sharpe"),
        ),
        hovertemplate="Vol: %{x:.1f}%<br>Return: %{y:.1f}%<br>Sharpe: %{marker.color:.2f}<extra></extra>",
    ))

    if max_sharpe:
        fig.add_trace(go.Scatter(
            x=[max_sharpe["annualized_volatility"] * 100],
            y=[max_sharpe["annualized_return"] * 100],
            mode="markers",
            name="Max Sharpe",
            marker=dict(symbol="star", size=18, color="#FFD700", line=dict(color="#000", width=1)),
            hovertemplate=f"Max Sharpe Portfolio<br>Vol: {max_sharpe['annualized_volatility']*100:.1f}%<br>Return: {max_sharpe['annualized_return']*100:.1f}%<br>Sharpe: {max_sharpe['sharpe_ratio']:.2f}<extra></extra>",
        ))

    if min_vol:
        fig.add_trace(go.Scatter(
            x=[min_vol["annualized_volatility"] * 100],
            y=[min_vol["annualized_return"] * 100],
            mode="markers",
            name="Min Volatility",
            marker=dict(symbol="diamond", size=14, color="#00C851", line=dict(color="#000", width=1)),
            hovertemplate=f"Min Volatility Portfolio<br>Vol: {min_vol['annualized_volatility']*100:.1f}%<br>Return: {min_vol['annualized_return']*100:.1f}%<extra></extra>",
        ))

    if current_portfolio:
        fig.add_trace(go.Scatter(
            x=[current_portfolio.get("annualized_volatility", 0) * 100],
            y=[current_portfolio.get("annualized_return", 0) * 100],
            mode="markers",
            name="Your Portfolio",
            marker=dict(symbol="circle", size=14, color="#FF4136", line=dict(color="#000", width=1)),
            hovertemplate=f"Your Portfolio<br>Vol: {current_portfolio.get('annualized_volatility', 0)*100:.1f}%<br>Return: {current_portfolio.get('annualized_return', 0)*100:.1f}%<extra></extra>",
        ))

    fig.update_layout(
        title="Markowitz Efficient Frontier",
        xaxis_title="Annualized Volatility (%)",
        yaxis_title="Annualized Return (%)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(gridcolor="#f0f0f0"),
        yaxis=dict(gridcolor="#f0f0f0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )
    return fig


def plot_portfolio_weights(weights: Dict[str, float], title: str = "Portfolio Weights") -> go.Figure:
    if not weights:
        return go.Figure()

    labels = list(weights.keys())
    values = [v * 100 for v in weights.values()]

    fig = go.Figure(data=go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo="label+percent",
        marker=dict(colors=COLORS[:len(labels)]),
        hovertemplate="<b>%{label}</b><br>Weight: %{value:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=title,
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=380,
    )
    return fig
