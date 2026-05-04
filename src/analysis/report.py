"""Markdown report generator."""
import csv
from collections import defaultdict


def load_csv(filepath: str) -> list[dict]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def latest_run_report(filepath: str) -> str:
    """Generate a markdown report for the latest run."""
    rows = load_csv(filepath)
    if not rows:
        return "# Tracker Report\n\nBrak danych w master.csv.\n"

    run_dates = sorted(set(r["run_date"] for r in rows if r.get("run_date")))
    latest = run_dates[-1] if run_dates else "brak"
    latest_rows = [r for r in rows if r.get("run_date") == latest]

    # SEO summary
    seo_rows = [r for r in latest_rows if r.get("query_type") == "seo"]
    seo_top10 = [r for r in seo_rows if r.get("position") and r.get("position").isdigit() and int(r["position"]) <= 10]
    seo_top30 = [r for r in seo_rows if r.get("position") and r.get("position").isdigit() and 11 <= int(r["position"]) <= 30]
    seo_null = [r for r in seo_rows if not r.get("position")]

    # GEO summary
    geo_rows = [r for r in latest_rows if r.get("query_type") == "geo"]
    geo_matched = [r for r in geo_rows if r.get("domain_matched") == "true"]
    geo_by_engine = defaultdict(int)
    for r in geo_matched:
        geo_by_engine[r["engine"]] += 1

    lines = [
        f"# Tracker Report — {latest}",
        "",
        "## SEO",
        f"- Top 10: **{len(seo_top10)}** fraz",
        f"- Top 11-30: **{len(seo_top30)}** fraz",
        f"- Brak w top 100: **{len(seo_null)}** fraz",
        "",
        "## GEO",
        f"- Łączna liczba wzmianek: **{len(geo_matched)}**",
    ]
    for engine, count in sorted(geo_by_engine.items()):
        lines.append(f"  - {engine}: {count}")

    lines += ["", "---", f"_Run: {latest} | Wierszy: {len(latest_rows)}_"]
    return "\n".join(lines)
