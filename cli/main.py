import json
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    name="quant-agent",
    help="Quantitative Financial Research Agent — AI-powered risk analysis for stocks & portfolios.",
    add_completion=False,
)

console = Console()
err_console = Console(stderr=True)


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s | %(name)s | %(message)s",
    )


@app.command()
def analyze(
    query: str = typer.Argument(..., help="Natural language financial query"),
    output: str = typer.Option("pretty", "--output", "-o", help="Output format: pretty|json|table"),
    save: Optional[Path] = typer.Option(None, "--save", "-s", help="Save JSON report to file"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override LLM model"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass response cache"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show tool call details"),
    log_level: str = typer.Option("WARNING", "--log-level", help="Logging level"),
) -> None:
    """Analyze stocks, funds, or portfolios with AI-powered quantitative research."""
    _setup_logging(log_level)

    from config import get_settings
    from agent.core import create_financial_agent, run_query
    from utils.cache import ResponseCache
    from utils.formatting import print_report

    settings = get_settings()
    cache = ResponseCache(
        ttl_seconds=settings.CACHE_TTL_SECONDS,
        enabled=(settings.CACHE_ENABLED and not no_cache),
    )

    model_name = model or settings.LLM_MODEL

    cached = cache.get(query, model_name)
    if cached:
        console.print("[dim]Using cached result...[/dim]")
        report = cached
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=err_console,
        ) as progress:
            progress.add_task("Running financial analysis...", total=None)
            try:
                agent = create_financial_agent(model_override=model_name)
                report = run_query(agent, query, verbose=verbose)
            except Exception as e:
                err_console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(1)

        if "error" not in report:
            cache.set(query, report, model_name)

    if output == "json":
        console.print_json(json.dumps(report, indent=2))
    elif output == "table":
        from utils.formatting import print_metrics_table, print_correlation_heatmap
        metrics = report.get("metrics") or (
            [report.get("portfolio_metrics")] if report.get("portfolio_metrics") else []
        )
        if metrics:
            print_metrics_table([m for m in metrics if m])
        corr = report.get("correlation_matrix", {})
        if corr:
            print_correlation_heatmap(corr)
    else:
        print_report(report)

    if save:
        save.write_text(json.dumps(report, indent=2))
        console.print(f"\n[green]Report saved to:[/green] {save}")


@app.command()
def batch(
    queries_file: Path = typer.Argument(..., help="Text file with one query per line"),
    output_dir: Path = typer.Option(Path("./reports"), "--output-dir", "-d", help="Directory to save reports"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override LLM model"),
    log_level: str = typer.Option("WARNING", "--log-level"),
) -> None:
    """Run multiple queries from a file, saving each report as JSON."""
    _setup_logging(log_level)

    if not queries_file.exists():
        err_console.print(f"[red]File not found:[/red] {queries_file}")
        raise typer.Exit(1)

    queries = [q.strip() for q in queries_file.read_text().splitlines() if q.strip()]
    if not queries:
        err_console.print("[yellow]No queries found in file.[/yellow]")
        raise typer.Exit(0)

    output_dir.mkdir(parents=True, exist_ok=True)

    from config import get_settings
    from agent.core import create_financial_agent, run_query

    settings = get_settings()
    model_name = model or settings.LLM_MODEL
    agent = create_financial_agent(model_override=model_name)

    console.print(f"Running [bold]{len(queries)}[/bold] queries...")

    for i, query in enumerate(queries, 1):
        console.print(f"\n[{i}/{len(queries)}] {query[:80]}...")
        try:
            report = run_query(agent, query)
            filename = output_dir / f"report_{i:03d}.json"
            filename.write_text(json.dumps(report, indent=2))
            console.print(f"  [green]Saved:[/green] {filename}")
        except Exception as e:
            console.print(f"  [red]Failed:[/red] {e}")

    console.print(f"\n[bold green]Done.[/bold green] Reports saved to {output_dir}/")


@app.command()
def server(
    host: str = typer.Option("127.0.0.1", "--host", help="Server host"),
    port: int = typer.Option(8000, "--port", "-p", help="Server port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (dev only)"),
    log_level: str = typer.Option("info", "--log-level"),
) -> None:
    """Start the FastAPI REST API server."""
    try:
        import uvicorn
    except ImportError:
        err_console.print("[red]uvicorn not installed. Run: pip install uvicorn[standard][/red]")
        raise typer.Exit(1)

    console.print(f"Starting server at [bold]http://{host}:{port}[/bold]")
    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )


@app.command()
def clear_cache() -> None:
    """Clear the local response cache."""
    from utils.cache import ResponseCache
    count = ResponseCache().clear()
    console.print(f"[green]Cleared {count} cached responses.[/green]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
