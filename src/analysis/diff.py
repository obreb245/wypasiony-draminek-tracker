"""Diff analysis: compare current run to previous runs."""
import csv
from collections import defaultdict
from datetime import date


def load_csv(filepath: str) -> list[dict]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def get_runs(rows: list[dict]) -> list[str]:
    """Return sorted list of unique run_dates."""
    dates = sorted(set(r["run_date"] for r in rows if r.get("run_date")))
    return dates


def diff_since(filepath: str, since_date: str) -> dict:
    """Compare latest run to the run at or before since_date."""
    rows = load_csv(filepath)
    runs = get_runs(rows)

    if len(runs) < 2:
        return {"status": "no_previous_runs", "message": "Brak poprzednich runów do porównania."}

    latest = runs[-1]
    previous = [r for r in runs if r <= since_date and r != latest]
    if not previous:
        return {"status": "no_previous_runs", "message": f"Brak runów przed datą {since_date}."}

    prev_date = previous[-1]
    latest_rows = [r for r in rows if r["run_date"] == latest]
    prev_rows = [r for r in rows if r["run_date"] == prev_date]

    # SEO comparison
    def seo_positions(run_rows):
        result = {}
        for r in run_rows:
            if r.get("query_type") == "seo" and r.get("engine") in ("google", "bing"):
                key = (r["engine"], r["query_or_prompt"])
                result[key] = int(r["position"]) if r.get("position") else None
        return result

    latest_pos = seo_positions(latest_rows)
    prev_pos = seo_positions(prev_rows)

    wins = []
    losses = []
    for key in set(latest_pos) | set(prev_pos):
        lp = latest_pos.get(key)
        pp = prev_pos.get(key)
        if lp is not None and pp is not None and lp < pp:
            wins.append({"engine": key[0], "phrase": key[1], "from": pp, "to": lp})
        elif lp is not None and pp is not None and lp > pp:
            losses.append({"engine": key[0], "phrase": key[1], "from": pp, "to": lp})

    # GEO comparison
    def geo_mentions(run_rows):
        result = defaultdict(set)
        for r in run_rows:
            if r.get("query_type") == "geo" and r.get("domain_matched") == "true":
                result[r["engine"]].add(r["query_or_prompt"])
        return result

    latest_geo = geo_mentions(latest_rows)
    prev_geo = geo_mentions(prev_rows)
    new_mentions = []
    for engine in set(latest_geo) | set(prev_geo):
        new = latest_geo[engine] - prev_geo[engine]
        for prompt in new:
            new_mentions.append({"engine": engine, "prompt": prompt})

    return {
        "status": "ok",
        "latest_run": latest,
        "compared_to": prev_date,
        "seo_wins": wins,
        "seo_losses": losses,
        "geo_new_mentions": new_mentions,
    }
