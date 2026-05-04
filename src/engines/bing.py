"""Bing Web Search engine using Azure Cognitive Services."""
import os
import requests
from datetime import date
from typing import Any

from src.engines.base import BaseEngine
from src.utils.domain_match import match_domain, extract_domain
from src.utils.retry import retry

BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"


class BingEngine(BaseEngine):
    name = "bing"

    def run(self, dry_run: bool = False) -> list[dict[str, Any]]:
        api_key = os.environ.get("BING_API_KEY", "")
        if not api_key:
            raise ValueError("BING_API_KEY not set")

        queries = self.config.get("queries", [])
        domains = self.settings.get("domains_to_track", ["wypasionydraminek.pl", "draminek.pl"])
        cost_per = self.settings.get("cost_per_query_pln", {}).get("bing", 0.05)
        count = self.settings.get("engines", {}).get("seo", {}).get("bing", {}).get("count", 50)
        mkt = self.settings.get("engines", {}).get("seo", {}).get("bing", {}).get("mkt", "pl-PL")
        run_id = date.today().isoformat()

        headers = {"Ocp-Apim-Subscription-Key": api_key}

        rows = []
        for q in queries:
            phrase = q.get("phrase", "")
            category = q.get("category", "")
            priority = q.get("priority", "medium")
            position = ""
            url_found = ""
            domain_matched = "false"
            response_excerpt = ""
            error = ""

            @retry(max_attempts=3, backoff_base=2)
            def call_api(kw=phrase):
                resp = requests.get(
                    BING_ENDPOINT,
                    headers=headers,
                    params={"q": kw, "count": count, "mkt": mkt},
                    timeout=15,
                )
                resp.raise_for_status()
                return resp.json()

            try:
                data = call_api()
                web_pages = data.get("webPages", {}).get("value", [])
                competitors = []
                for idx, item in enumerate(web_pages, start=1):
                    url = item.get("url", "")
                    domain = extract_domain(url)
                    if match_domain(url, domains):
                        position = str(idx)
                        url_found = url
                        domain_matched = "true"
                        break
                    elif domain and domain not in competitors:
                        competitors.append(domain)

                if domain_matched != "true" and competitors:
                    response_excerpt = ", ".join(competitors[:3])

            except Exception as e:
                error = str(e)

            rows.append(self._empty_row(
                run_date=run_id, run_id=run_id, engine=self.name,
                query_type="seo", query_or_prompt=phrase,
                category=category, priority=priority,
                position=position, url_found=url_found,
                domain_matched=domain_matched,
                response_excerpt=response_excerpt,
                error=error, cost_pln=str(cost_per),
            ))
        return rows

    def run_mock(self) -> list[dict[str, Any]]:
        run_id = date.today().isoformat()
        queries = self.config.get("queries", [])
        mock_positions = [3, None, 18, None, 7, 42, None, 2, None, 11]
        rows = []
        for i, q in enumerate(queries):
            pos = mock_positions[i % len(mock_positions)]
            has_match = pos is not None
            rows.append(self._empty_row(
                run_date=run_id, run_id=run_id, engine=self.name,
                query_type="seo", query_or_prompt=q.get("phrase", ""),
                category=q.get("category", ""), priority=q.get("priority", "medium"),
                position=str(pos) if has_match else "",
                url_found=f"https://draminek.pl/{q.get('phrase', '').replace(' ', '-')}" if has_match else "",
                domain_matched="true" if has_match else "false",
                response_excerpt="" if has_match else "empik.com, allegro.pl, amazon.pl",
                cost_pln="0.05",
            ))
        return rows
