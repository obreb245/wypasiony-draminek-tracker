"""CLI entry point for the Wypasiony Draminek Tracker."""
import os
from datetime import date

import click
import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()
console = Console()

SETTINGS_PATH = "config/settings.yaml"
QUERIES_PATH = "config/queries.yaml"
AI_PROMPTS_PATH = "config/ai_prompts.yaml"
MASTER_CSV = "data/master.csv"
RUNS_DIR = "data/runs"
DOCS_DIR = "docs"

ALL_ENGINES = ["anthropic", "openai", "perplexity", "gemini", "gsc", "google", "bing"]
AI_ENGINES = ["anthropic", "openai", "perplexity", "gemini"]
SEO_ENGINES = ["gsc", "google", "bing"]


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_engine(name: str, settings: dict, config: dict):
    if name == "anthropic":
        from src.engines.anthropic_engine import AnthropicEngine
        return AnthropicEngine(settings, config)
    elif name == "openai":
        from src.engines.openai_engine import OpenAIEngine
        return OpenAIEngine(settings, config)
    elif name == "perplexity":
        from src.engines.perplexity import PerplexityEngine
        return PerplexityEngine(settings, config)
    elif name == "gemini":
        from src.engines.gemini import GeminiEngine
        return GeminiEngine(settings, config)
    elif name == "gsc":
        from src.engines.gsc import GSCEngine
        return GSCEngine(settings, config)
    elif name == "google":
        from src.engines.google import GoogleEngine
        return GoogleEngine(settings, config)
    elif name == "bing":
        from src.engines.bing import BingEngine
        return BingEngine(settings, config)
    else:
        raise ValueError(f"Unknown engine: {name}")


@click.group()
def cli():
    """Wypasiony Draminek SEO/GEO Tracker."""


@cli.command()
@click.option("--engines", default="all", help="Comma-separated engines or 'all'")
@click.option("--mock", is_flag=True, help="Run in mock mode (no API calls)")
@click.option("--dry-run", is_flag=True, help="Don't write to CSV or disk")
def run(engines: str, mock: bool, dry_run: bool):
    """Run the tracker engines and collect data."""
    settings = load_yaml(SETTINGS_PATH)
    queries = load_yaml(QUERIES_PATH)
    ai_prompts = load_yaml(AI_PROMPTS_PATH)
    run_id = date.today().isoformat()

    if engines == "all":
        engine_list = ALL_ENGINES
    else:
        engine_list = [e.strip() for e in engines.split(",")]

    console.print(f"[bold]Run ID:[/bold] {run_id}")
    console.print(f"[bold]Engines:[/bold] {', '.join(engine_list)}")
    console.print(f"[bold]Mock:[/bold] {mock} | [bold]Dry run:[/bold] {dry_run}")
    console.print("")

    all_rows = []
    for engine_name in engine_list:
        # Choose config: SEO engines get queries, AI engines get prompts
        if engine_name in SEO_ENGINES:
            config = queries
        else:
            config = ai_prompts

        try:
            engine = get_engine(engine_name, settings, config)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            continue

        try:
            if mock:
                rows = engine.run_mock()
            else:
                rows = engine.run(dry_run=dry_run)
        except Exception as e:
            console.print(f"[red]{engine_name} failed:[/red] {e}")
            continue

        console.print(f"[green]{engine_name}:[/green] {len(rows)} rows")

        if not dry_run and rows:
            from src.storage.csv_writer import append_rows
            from src.storage.json_archiver import save_run
            append_rows(MASTER_CSV, rows)
            save_run(run_id, engine_name, rows, RUNS_DIR)

        all_rows.extend(rows)

    console.print(f"\n[bold]Total rows:[/bold] {len(all_rows)}")

    if dry_run:
        # Print sample to stdout
        t = Table(title="Sample output (dry run)")
        cols = ["engine", "query_type", "query_or_prompt", "position", "domain_matched", "mention_text"]
        for c in cols:
            t.add_column(c)
        for r in all_rows[:10]:
            t.add_row(*[str(r.get(c, "")) for c in cols])
        console.print(t)
    else:
        console.print(f"[bold green]Data written to {MASTER_CSV}[/bold green]")


@cli.command()
def dashboard():
    """Generate the HTML dashboard from master.csv."""
    from src.dashboard.generator import generate
    # Copy static CSS to docs
    import shutil
    static_src = os.path.join(os.path.dirname(__file__), "dashboard", "static", "style.css")
    os.makedirs(DOCS_DIR, exist_ok=True)
    shutil.copy2(static_src, os.path.join(DOCS_DIR, "style.css"))
    generate(MASTER_CSV, DOCS_DIR)
    console.print(f"[green]Dashboard generated:[/green] {DOCS_DIR}/index.html")


@cli.command()
@click.option("--latest", is_flag=True, help="Report for the latest run")
def report(latest: bool):
    """Print a markdown report."""
    from src.analysis.report import latest_run_report
    md = latest_run_report(MASTER_CSV)
    console.print(md)


@cli.command()
@click.option("--since", required=True, help="Compare to runs since this date (YYYY-MM-DD)")
def diff(since: str):
    """Show diff between latest and a previous run."""
    from src.analysis.diff import diff_since
    result = diff_since(MASTER_CSV, since)
    if result["status"] == "no_previous_runs":
        console.print(f"[yellow]{result['message']}[/yellow]")
        return

    console.print(f"[bold]Comparing:[/bold] {result['latest_run']} vs {result['compared_to']}")
    console.print(f"\n[green]SEO Wins (awanse):[/green] {len(result['seo_wins'])}")
    for w in result["seo_wins"]:
        console.print(f"  {w['engine']} | {w['phrase']}: {w['from']} → {w['to']}")

    console.print(f"\n[red]SEO Losses (spadki):[/red] {len(result['seo_losses'])}")
    for l in result["seo_losses"]:
        console.print(f"  {l['engine']} | {l['phrase']}: {l['from']} → {l['to']}")

    console.print(f"\n[cyan]Nowe wzmianki GEO:[/cyan] {len(result['geo_new_mentions'])}")
    for m in result["geo_new_mentions"]:
        console.print(f"  {m['engine']} | {m['prompt']}")


if __name__ == "__main__":
    cli()
