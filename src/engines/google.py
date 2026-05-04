"""Google SERP engine using DataForSEO API."""
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Any

from src.engines.base import BaseEngine
from src.utils.domain_match import match_domain, extract_domain
from src.utils.retry import retry

DATAFORSEO_URL = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"


class GoogleEngine(BaseEngine):
    name = "google"

    def _search_phrase(self, phrase: str, login: str, password: str, settings: dict) -> dict:
        depth = settings.get("engines", {}).get("seo", {}).get("google", {}).get("depth", 100)
        language_code = settings.get("engines", {}).get("seo", {}).get("google", {}).get("language_code", "pl")
        location_code = settings.get("engines", {}).get("seo", {}).get("google", {}).get("location_code", 2616)

        @retry(max_attempts=3, backoff_base=2)
        def call():
            resp = requests.post(
                DATAFORSEO_URL,
                auth=(login, password),
                json=[{
                    "keyword": phrase,
                    "location_code": location_code,
                    "language_code": language_code,
                    "depth": depth,
                }],
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

        return call()

    def run(self, dry_run: bool = False) -> list[dict[str, Any]]:
        login = os.environ.get("DATAFORSEO_LOGIN", "")
        password = os.environ.get("DATAFORSEO_PASSWORD", "")
        if not login or not password:
            raise ValueError("DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD not set")

        queries = self.config.get("queries", [])
        domains = self.settings.get("domains_to_track", ["wypasionydraminek.pl", "draminek.pl"])
        cost_per = self.settings.get("cost_per_query_pln", {}).get("google", 0.10)
        run_id = date.today().isoformat()
        max_workers = self.settings.get("engines", {}).get("seo", {}).get("google", {}).get("max_concurrent", 5)

        def process_query(q):
            phrase = q.get("phrase", "")
            category = q.get("category", "")
            priority = q.get("priority", "medium")
            error = ""
            position = ""
            url_found = ""
            domain_matched = "false"
            response_excerpt = ""

            try:
                result = self._search_phrase(phrase, login, password, self.settings)
                items = result.get("tasks", [{}])[0].get("result", [{}])[0].get("items", [])
                # Find our domain position
                competitors = []
                for item in items:
                    url = item.get("url", "")
                    pos = item.get("rank_absolute", None)
                    domain = extract_domain(url)
                    if match_domain(url, domains):
                        position = str(pos)
                        url_found = url
                        domain_matched = "true"
                        break
                    elif domain and domain not in competitors:
                        competitors.append(domain)

                if not domain_matched == "true" and competitors:
                    response_excerpt = ", ".join(competitors[:3])

            except Exception as e:
                error = str(e)

            return self._empty_row(
                run_date=run_id, run_id=run_id, engine=self.name,
                query_type="seo", query_or_prompt=phrase,
                category=category, priority=priority,
                position=position, url_found=url_found,
                domain_matched=domain_matched,
                response_excerpt=response_excerpt,
                error=error, cost_pln=str(cost_per),
            )

        rows = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_query, q): q for q in queries}
            for future in as_completed(futures):
                rows.append(future.result())
        return rows

    def run_mock(self) -> list[dict[str, Any]]:
        run_id = date.today().isoformat()
        queries = self.config.get("queries", [])
        mock_positions = [5, 23, None, 1, 67, None, 12, 3, None, 45, 8, None]
        rows = []
        for i, q in enumerate(queries):
            pos = mock_positions[i % len(mock_positions)]
            has_match = pos is not None
            rows.append(self._empty_row(
                run_date=run_id, run_id=run_id, engine=self.name,
                query_type="seo", query_or_prompt=q.get("phrase", ""),
                category=q.get("category", ""), priority=q.get("priority", "medium"),
                position=str(pos) if has_match else "",
                url_found=f"https://wypasionydraminek.pl/szukaj/{q.get('phrase', '').replace(' ', '-')}" if has_match else "",
                domain_matched="true" if has_match else "false",
                response_excerpt="" if has_match else "allegro.pl, ceneo.pl, olx.pl",
                cost_pln="0.10",
            ))
        return rows
