"""JSON archiver for per-run data dumps."""
import json
import os
from datetime import date
from typing import Any


def save_run(run_id: str, engine_name: str, data: list[dict[str, Any]], runs_dir: str = "data/runs") -> str:
    """Save run data as JSON. Returns path to saved file."""
    run_date = run_id if run_id else date.today().isoformat()
    dir_path = os.path.join(runs_dir, run_date)
    os.makedirs(dir_path, exist_ok=True)
    filepath = os.path.join(dir_path, f"{engine_name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"run_id": run_id, "engine": engine_name, "rows": data}, f, ensure_ascii=False, indent=2)
    return filepath
