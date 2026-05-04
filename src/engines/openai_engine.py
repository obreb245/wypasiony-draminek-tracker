"""OpenAI (ChatGPT) engine for GEO tracking."""
import os
from datetime import date
from typing import Any

from src.engines.base import BaseEngine
from src.engines.anthropic_engine import _find_mentions, TARGETS
from src.utils.retry import retry


class OpenAIEngine(BaseEngine):
    name = "openai"

    def run(self, dry_run: bool = False) -> list[dict[str, Any]]:
        """Run prompts against OpenAI API."""
        import openai

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        client = openai.OpenAI(api_key=api_key)
        prompts = self.config.get("prompts", [])
        settings = self.settings
        model = settings.get("engines", {}).get("ai", {}).get("openai", {}).get("model", "gpt-4o")
        max_tokens = settings.get("engines", {}).get("ai", {}).get("openai", {}).get("max_tokens", 1024)
        context_chars = settings.get("mention_context_chars", 50)
        cost_per = settings.get("cost_per_query_pln", {}).get("openai", 0.08)
        run_id = date.today().isoformat()

        rows = []
        for p in prompts:
            prompt_text = p.get("prompt", "")
            category = p.get("category", "")
            priority = p.get("priority", "medium")

            @retry(max_attempts=3, backoff_base=2)
            def call_api(prompt=prompt_text):
                resp = client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.choices[0].message.content

            response_text = ""
            error = ""
            try:
                response_text = call_api()
            except Exception as e:
                error = str(e)

            mentions = _find_mentions(response_text, TARGETS, context_chars) if response_text else []
            if not mentions:
                rows.append(self._empty_row(
                    run_date=run_id, run_id=run_id, engine=self.name,
                    query_type="geo", query_or_prompt=prompt_text,
                    category=category, priority=priority,
                    domain_matched="false", error=error, cost_pln=str(cost_per),
                ))
            else:
                for m in mentions:
                    rows.append(self._empty_row(
                        run_date=run_id, run_id=run_id, engine=self.name,
                        query_type="geo", query_or_prompt=prompt_text,
                        category=m["category"], priority=priority,
                        domain_matched="true", mention_text=m["mention_text"],
                        response_excerpt=m["response_excerpt"],
                        error=error, cost_pln=str(cost_per),
                    ))
        return rows

    def run_mock(self) -> list[dict[str, Any]]:
        run_id = date.today().isoformat()
        prompts = self.config.get("prompts", [])
        rows = []
        mock_data = [
            ("wypasionydraminek.pl", "confirmed", "Polecam wypasionydraminek.pl — świetna oferta."),
            ("", "brand_awareness", ""),
            ("draminek", "ambiguous", "Słyszałem o draminku, ale nie znam strony."),
        ]
        for i, p in enumerate(prompts):
            mention, cat, excerpt = mock_data[i % len(mock_data)]
            rows.append(self._empty_row(
                run_date=run_id, run_id=run_id, engine=self.name,
                query_type="geo", query_or_prompt=p.get("prompt", ""),
                category=p.get("category", "") if not mention else cat,
                priority=p.get("priority", "medium"),
                domain_matched="true" if mention else "false",
                mention_text=mention, response_excerpt=excerpt, cost_pln="0.08",
            ))
        return rows
