"""Google Search Console engine — import z CSV eksportowanego ręcznie z GSC.

Jak używać:
1. Wejdź na search.google.com/search-console
2. Performance → Search results → ustaw zakres dat (ostatnie 28 dni)
3. Kliknij ikonę pobierania (↓) → "Download CSV"
4. Zapisz plik jako data/gsc_export/gsc_YYYY-MM-DD.csv
5. Uruchom: python -m src.main run --engines gsc
"""
import csv
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engines.base import BaseEngine

EXPORT_DIR = Path("data/gsc_export")


def _find_latest_csv() -> Path | None:
    if not EXPORT_DIR.exists():
        return None
    csvs = sorted(EXPORT_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return csvs[0] if csvs else None


def _parse_gsc_csv(path: Path) -> dict[str, dict]:
    results = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = (
                row.get("Top queries") or row.get("Query") or
                row.get("Zapytanie") or row.get("Najlepsze zapytania") or ""
            ).strip().lower()
            if not query:
                continue
            try:
                position = float(row.get("Position") or row.get("Pozycja") or row.get("Average position") or 0)
                clicks = int(row.get("Clicks") or row.get("Kliknięcia") or 0)
                impressions = int(row.get("Impressions") or row.get("Wyświetlenia") or 0)
                ctr_raw = (row.get("CTR") or row.get("Współczynnik CTR") or "0").replace("%", "").replace(",", ".").strip()
                ctr = float(ctr_raw) if ctr_raw else 0.0
            except (ValueError, TypeError):
                continue
            results[query] = {
                "position": round(position, 1),
                "clicks": clicks,
                "impressions": impressions,
                "ctr": round(ctr, 2),
            }
    return results


class GSCEngine(BaseEngine):
    name = "gsc"

    def run(self, dry_run: bool = False) -> list[dict[str, Any]]:
        csv_path = _find_latest_csv()
        if csv_path is None:
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            raise FileNotFoundError(
                f"Brak pliku CSV w {EXPORT_DIR}/.\n"
                "Pobierz eksport z GSC:\n"
                "  Performance → Search results → ikona ↓ → Download CSV\n"
                f"  Zapisz jako: {EXPORT_DIR}/gsc_{date.today().isoformat()}.csv"
            )

        gsc_data = _parse_gsc_csv(csv_path)
        file_date = csv_path.stat().st_mtime
        export_date = datetime.fromtimestamp(file_date).date().isoformat()

        queries = self.config.get("queries", [])
        run_id = date.today().isoformat()
        rows = []

        for q in queries:
            phrase = q.get("phrase", "")
            data = gsc_data.get(phrase.lower())

            if data and data["position"] > 0:
                position = str(data["position"])
                response_excerpt = f"clicks={data['clicks']} impressions={data['impressions']} ctr={data['ctr']}%"
                domain_matched = "true"
                url_found = "https://wypasionydraminek.pl/"
                error = ""
            else:
                position = ""
                response_excerpt = f"brak danych (eksport: {export_date})"
                domain_matched = "false"
                url_found = ""
                error = ""

            rows.append(self._empty_row(
                run_date=run_id, run_id=run_id, engine=self.name,
                query_type="seo", query_or_prompt=phrase,
                category=q.get("category", ""), priority=q.get("priority", "medium"),
                position=position, url_found=url_found, domain_matched=domain_matched,
                response_excerpt=response_excerpt, error=error, cost_pln="0.00",
            ))

        return rows

    def run_mock(self) -> list[dict[str, Any]]:
        run_id = date.today().isoformat()
        queries = self.config.get("queries", [])
        mock_data = [
            (3.2, 18, 420, 4.29),
            (1.0, 52, 180, 28.89),
            (None, 0, 0, 0),
            (7.4, 5, 110, 4.55),
            (None, 0, 0, 0),
            (15.1, 2, 67, 2.99),
            (None, 0, 0, 0),
        ]
        rows = []
        for i, q in enumerate(queries):
            position, clicks, impressions, ctr = mock_data[i % len(mock_data)]
            has_data = position is not None
            rows.append(self._empty_row(
                run_date=run_id, run_id=run_id, engine=self.name,
                query_type="seo", query_or_prompt=q.get("phrase", ""),
                category=q.get("category", ""), priority=q.get("priority", "medium"),
                position=str(position) if has_data else "",
                url_found="https://wypasionydraminek.pl/" if has_data else "",
                domain_matched="true" if has_data else "false",
                response_excerpt=f"clicks={clicks} impressions={impressions} ctr={ctr}%" if has_data else "brak danych",
                cost_pln="0.00",
            ))
        return rows
