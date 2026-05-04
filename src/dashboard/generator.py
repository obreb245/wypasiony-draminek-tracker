"""Dashboard HTML generator using Jinja2 + Plotly."""
import csv
import json
import os
from collections import defaultdict
from datetime import datetime

from jinja2 import Environment, FileSystemLoader


def load_csv(filepath: str) -> list[dict]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def _position_color(pos_str: str) -> str:
    if not pos_str or not pos_str.isdigit():
        return "pos-null"
    p = int(pos_str)
    if p <= 10:
        return "pos-top10"
    if p <= 30:
        return "pos-top30"
    return "pos-top100"


def generate(master_csv: str = "data/master.csv", docs_dir: str = "docs"):
    """Generate the full HTML dashboard from master.csv."""
    rows = load_csv(master_csv)

    run_dates = sorted(set(r["run_date"] for r in rows if r.get("run_date")))
    latest = run_dates[-1] if run_dates else None
    latest_rows = [r for r in rows if r.get("run_date") == latest] if latest else []

    # SEO data
    seo_rows = [r for r in latest_rows if r.get("query_type") == "seo"]
    seo_top10 = sum(1 for r in seo_rows if r.get("position", "").isdigit() and int(r["position"]) <= 10)
    total_seo = len(set(r["query_or_prompt"] for r in seo_rows))

    # GEO data
    geo_rows = [r for r in latest_rows if r.get("query_type") == "geo"]
    geo_matched = [r for r in geo_rows if r.get("domain_matched") == "true"]
    total_geo = len(set(r["query_or_prompt"] for r in geo_rows))
    geo_mentions = len(set((r["engine"], r["query_or_prompt"]) for r in geo_matched))

    # GEO by engine for table
    geo_engines = sorted(set(r["engine"] for r in geo_rows))
    geo_prompts = sorted(set(r["query_or_prompt"] for r in geo_rows))
    geo_table = []
    for prompt in geo_prompts:
        row_data = {"prompt": prompt, "category": "", "engines": {}}
        for r in geo_rows:
            if r["query_or_prompt"] == prompt:
                row_data["category"] = r.get("category", "")
                row_data["engines"][r["engine"]] = {
                    "matched": r.get("domain_matched") == "true",
                    "excerpt": r.get("response_excerpt", ""),
                    "mention": r.get("mention_text", ""),
                }
        geo_table.append(row_data)

    # SEO table
    seo_table = []
    for r in seo_rows:
        seo_table.append({
            "query": r.get("query_or_prompt", ""),
            "category": r.get("category", ""),
            "priority": r.get("priority", ""),
            "engine": r.get("engine", ""),
            "position": r.get("position", ""),
            "url": r.get("url_found", ""),
            "color_class": _position_color(r.get("position", "")),
        })

    # Trend data for Plotly
    trend_seo = defaultdict(int)
    trend_geo = defaultdict(lambda: defaultdict(int))
    for r in rows:
        rd = r.get("run_date", "")
        if r.get("query_type") == "seo":
            pos = r.get("position", "")
            if pos.isdigit() and int(pos) <= 10:
                trend_seo[rd] += 1
        elif r.get("query_type") == "geo" and r.get("domain_matched") == "true":
            trend_geo[rd][r.get("engine", "")] += 1

    trend_dates = sorted(set(trend_seo.keys()) | set(trend_geo.keys()))
    all_geo_engines = sorted(set(e for d in trend_geo.values() for e in d))

    plotly_seo = {
        "x": trend_dates,
        "y": [trend_seo.get(d, 0) for d in trend_dates],
        "name": "Top 10 SEO",
    }
    plotly_geo_series = []
    for eng in all_geo_engines:
        plotly_geo_series.append({
            "x": trend_dates,
            "y": [trend_geo.get(d, {}).get(eng, 0) for d in trend_dates],
            "name": eng,
        })

    context = {
        "latest_run": latest or "brak",
        "seo_top10": seo_top10,
        "total_seo": total_seo or 30,
        "geo_mentions": geo_mentions,
        "total_geo": total_geo or 18,
        "seo_table": seo_table,
        "geo_table": geo_table,
        "geo_engines": geo_engines,
        "plotly_seo": json.dumps(plotly_seo),
        "plotly_geo_series": json.dumps(plotly_geo_series),
        "run_dates": run_dates,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)

    os.makedirs(docs_dir, exist_ok=True)

    for tpl_name, out_name in [
        ("index.html", "index.html"),
        ("seo.html", "seo.html"),
        ("geo.html", "geo.html"),
        ("trends.html", "trends.html"),
    ]:
        try:
            tpl = env.get_template(tpl_name)
            out = tpl.render(**context)
            with open(os.path.join(docs_dir, out_name), "w", encoding="utf-8") as f:
                f.write(out)
        except Exception as e:
            print(f"Warning: could not render {tpl_name}: {e}")

    print(f"Dashboard generated in {docs_dir}/")
