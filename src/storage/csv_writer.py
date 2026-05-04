"""Append-only CSV writer for master.csv."""
import csv
import os
from typing import Any

MASTER_HEADERS = [
    "run_date", "run_id", "engine", "query_type", "query_or_prompt",
    "category", "priority", "position", "url_found", "domain_matched",
    "mention_text", "response_excerpt", "raw_response_path", "error", "cost_pln",
]


def append_rows(filepath: str, rows: list[dict[str, Any]]) -> int:
    """Append rows to CSV file. Creates file with headers if it doesn't exist.
    Returns number of rows written."""
    if not rows:
        return 0

    file_exists = os.path.isfile(filepath)
    has_header = False
    if file_exists:
        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            has_header = first_line == ",".join(MASTER_HEADERS)

    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)

    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MASTER_HEADERS, extrasaction="ignore")
        if not file_exists or not has_header:
            writer.writeheader()
        writer.writerows(rows)

    return len(rows)
