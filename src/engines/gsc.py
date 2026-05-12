"""Google Search Console engine using the Search Analytics API."""
import json
import os
from datetime import date, timedelta
from typing import Any

import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleAuthRequest

from src.engines.base import BaseEngine


GSC_API_URL = "https://www.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def _get_access_token(service_account_json: str) -> str:
    info = json.loads(service_account_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    creds.refresh(GoogleAuthRequest())
    return creds.token


class GSCEngine(BaseEngine):
    name = "gsc"

    def _query_gsc(self, access_token: str, site_url: str, phrases: list[str],
                   start_date: str, end_date: str) -> list[dict]:
        url = GSC_API_URL.format(site_url=requests.utils.quote(site_url, safe=""))
        headers = {"Authorization": f"Bearer {access_token}"}
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query"],
            "rowLimit": 25000,
            "dataState": "final",
        }
        if phrases:
            body["dimensionFilterGroups"] = [{
                "filters": [{
                    "dimension": "query",
                    "operator": "includingRegex",
                    "expression": "|".join(p.lower() for p in phrases),
                }]
            }]
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        return resp.json().get("rows", [])

    def run(self, dry_run: bool = False) -> list[dict[str, Any]]:
        sa_json = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "")
        site_url = os.environ.get("GSC_SITE_URL", "")
        if not sa_json:
            raise ValueError("GSC_SERVICE_ACCOUNT_JSON not set")
        if not site_url:
            raise ValueError("GSC_SITE_URL not set")

        gsc_settings = self.settings.get("engines", {}).get("seo", {}).get("gsc", {})
        lookback_days = gsc_settings.get("lookback_days", 28)
        end_date = (date.today() - timedelta(days=3)).isoformat()
        start_date = (date.today() - timedelta(days=lookback_days + 3)).isoformat()

        queries = self.config.get("queries", [])
        phrases = [q["phrase"] for q in queries if q.get("phrase")]
        phrase_to_meta = {q["phrase"].lower(): q for q in queries if q.get("phrase")}

        run_id = date.today().isoformat()
        access_token = _get_access_token(sa_json)
        rows_api = self._query_gsc(access_token, site_url, phrases, start_date, end_date)
        api_by_query = {r["keys"][0].lower(): r for r in rows_api}

        rows = []
        for phrase in phrases:
            meta = phrase_to_meta.get(phrase.lower(), {})
            api_row = api_by_query.get(phrase.lower())

            if api_row:
                position = round(api_row.get("position", 0), 1)
                clicks = api_row.get("clicks", 0)
                impressions = api_row.get("impressions", 0)
                ctr = round(api_row.get("ctr", 0) * 100, 2)
                response_excerpt = f"clicks={clicks} impressions={impressions} ctr={ctr}%"
                domain_matched = "true"
                url_found = site_url
                error = ""
            else:
                position = ""
                response_excerpt = f"no data ({start_date}–{end_date})"
                domain_matched = "false"
                url_found = ""
                error = ""

            rows.append(self._empty_row(
                run_date=run_id, run_id=run_id, engine=self.name,
                query_type="seo", query_or_prompt=phrase,
                category=meta.get("category", ""),
                priority=meta.get("priority", "medium"),
                position=str(position) if position != "" else "",
                url_found=url_found,
                domain_matched=domain_matched,
                response_excerpt=response_excerpt,
                error=error,
                cost_pln="0.00",
            ))
        return rows

    def run_mock(self) -> list[dict[str, Any]]:
        run_id = date.today().isoformat()
        queries = self.config.get("queries", [])
        mock_data = [
            (5.2, 12, 340, 3.53),
            (8.1, 3, 89, 3.37),
            (None, 0, 0, 0),
            (1.0, 45, 210, 21.43),
            (23.4, 1, 56, 1.79),
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
                response_excerpt=f"clicks={clicks} impressions={impressions} ctr={ctr}%" if has_data else "no data",
                cost_pln="0.00",
            ))
        return rows
