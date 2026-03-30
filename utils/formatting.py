from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

RISK_TIER_COLORS = {
    "Conservative": "green",
    "Moderate": "yellow",
    "Aggressive": "orange1",
    "Speculative": "red",
}


def _tier_color(tier: str) -> str:
    return RISK_TIER_COLORS.get(tier, "white")


def print_metrics_table(metrics_list: List[Dict[str, Any]]) -> None:
    if not metrics_list:
        console.print("[red]No metrics to display.[/red]")
        return

    table = Table(
        title="Risk Metrics Comparison",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Metric", style="bold", min_width=24)
    for m in metrics_list:
        ticker = m.get("ticker", "N/A")
        tier = m.get("risk_tier", "")
        color = _tier_color(tier)
        table.add_column(f"[{color}]{ticker}[/{color}]", min_width=14, justify="right")

    rows = [
        ("Period", "period", lambda v: str(v)),
        ("Ann. Return", "annualized_return", lambda v: f"{v * 100:.2f}%" if v is not None else "N/A"),
        ("Ann. Volatility", "annualized_volatility", lambda v: f"{v * 100:.2f}%" if v is not None else "N/A"),
        ("Sharpe Ratio", "sharpe_ratio", lambda v: f"{v:.3f}" if v is not None else "N/A"),
        ("Sortino Ratio", "sortino_ratio", lambda v: f"{v:.3f}" if v is not None else "N/A"),
        ("Max Drawdown", "max_drawdown", lambda v: f"{v * 100:.2f}%" if v is not None else "N/A"),
        ("Calmar Ratio", "calmar_ratio", lambda v: f"{v:.3f}" if v is not None else "N/A"),
        ("Beta", "beta", lambda v: f"{v:.3f}" if v is not None else "N/A"),
        ("Alpha (Ann.)", "alpha", lambda v: f"{v * 100:.2f}%" if v is not None else "N/A"),
        ("VaR (95%)", "var_95", lambda v: f"{v * 100:.2f}%" if v is not None else "N/A"),
        ("CVaR (95%)", "cvar_95", lambda v: f"{v * 100:.2f}%" if v is not None else "N/A"),
        ("Risk Tier", "risk_tier", lambda v: f"[{_tier_color(str(v))}]{v}[/{_tier_color(str(v))}]"),
    ]

    for label, key, formatter in rows:
        row_values = [label]
        for m in metrics_list:
            val = m.get(key)
            row_values.append(formatter(val))
        table.add_row(*row_values)

    console.print(table)


def print_correlation_heatmap(corr_matrix: Dict[str, Dict[str, float]]) -> None:
    if not corr_matrix:
        return

    tickers = list(corr_matrix.keys())
    table = Table(
        title="Return Correlation Matrix",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("", style="bold")

    for t in tickers:
        table.add_column(t, justify="center", min_width=8)

    for t_row in tickers:
        row_vals = [t_row]
        for t_col in tickers:
            val = corr_matrix.get(t_row, {}).get(t_col, 0.0)
            if t_row == t_col:
                row_vals.append("[bold]1.000[/bold]")
            else:
                color = "green" if val > 0.7 else ("yellow" if val > 0.3 else ("white" if val > 0 else "red"))
                row_vals.append(f"[{color}]{val:.3f}[/{color}]")
        table.add_row(*row_vals)

    console.print(table)


def print_report(report: Dict[str, Any]) -> None:
    if "error" in report:
        console.print(Panel(f"[red]Error:[/red] {report['error']}", title="Analysis Failed"))
        return

    report_type = report.get("report_type", "comparison")
    query = report.get("query", "")

    console.print()
    console.print(Panel(f"[bold cyan]{query}[/bold cyan]", title="Query", border_style="cyan"))

    if report_type == "comparison":
        metrics = report.get("metrics", [])
        if metrics:
            print_metrics_table(metrics)

        corr = report.get("correlation_matrix", {})
        if corr:
            print_correlation_heatmap(corr)

    elif report_type == "portfolio":
        pm = report.get("portfolio_metrics")
        if pm:
            console.print("\n[bold]Portfolio Aggregate Metrics[/bold]")
            print_metrics_table([pm])

        individual = report.get("individual_metrics", [])
        if individual:
            console.print("\n[bold]Individual Holdings[/bold]")
            print_metrics_table(individual)

    rec = report.get("recommendation", "")
    if rec:
        console.print()
        console.print(Panel(rec, title="Recommendation", border_style="green"))

    generated_at = report.get("generated_at", "")
    if generated_at:
        console.print(f"\n[dim]Report generated: {generated_at} UTC[/dim]")
