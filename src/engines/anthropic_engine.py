"""Anthropic (Claude) engine for GEO tracking."""
import os
import re
from datetime import date
from typing import Any

from src.engines.base import BaseEngine
from src.utils.retry import retry


TARGETS = ["wypasionydraminek.pl", "wypasiony draminek", "draminek.pl", "draminek"]
AMBIGUOUS = ["draminek"]
STRONG = ["wypasionydraminek.pl", "wypasiony draminek", "draminek.pl"]


def _find_mentions(text: str, targets: list[str], context_chars: int = 50) -> list[dict]:
    """Find all mention occurrences and return context snippets."""
    mentions = []
    text_lower = text.lower()
    for target in targets:
        t_lower = target.lower()
        start = 0
        while True:
            idx = text_lower.find(t_lower, start)
            if idx == -1:
                break
            ctx_start = max(0, idx - context_chars)
            ctx_end = min(len(text), idx + len(target) + context_chars)
            excerpt = text[ctx_start:ctx_end]
            # Determine category
            if target.lower() in [s.lower() for s in STRONG]:
                category = "confirmed"
            else:
                category = "ambiguous"
            mentions.append({
                "mention_text": target,
                "response_excerpt": excerpt,
                "category": category,
            })
            start = idx + 1
    return mentions


class AnthropicEngine(BaseEngine):
    name = "anthropic"

    def run(self, dry_run: bool = False) -> list[dict[str, Any]]:
        """Run prompts against Anthropic Claude API."""
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        client = anthropic.Anthropic(api_key=api_key)
        prompts = self.config.get("prompts", [])
        settings = self.settings
        model = settings.get("engines", {}).get("ai", {}).get("anthropic", {}).get("model", "claude-sonnet-4-5")
        max_tokens = settings.get("engines", {}).get("ai", {}).get("anthropic", {}).get("max_tokens", 1024)
        context_chars = settings.get("mention_context_chars", 50)
        domains = settings.get("domains_to_track", ["wypasionydraminek.pl", "draminek.pl"])
        run_id = date.today().isoformat()
        cost_per = settings.get("cost_per_query_pln", {}).get("anthropic", 0.05)

        rows = []
        for p in prompts:
            prompt_text = p.get("prompt", "")
            category = p.get("category", "")
            priority = p.get("priority", "medium")

            @retry(max_attempts=3, backoff_base=2)
            def call_api(prompt=prompt_text):
                msg = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return msg.content[0].text

            response_text = ""
            error = ""
            try:
                response_text = call_api()
            except Exception as e:
                error = str(e)

            mentions = _find_mentions(response_text, TARGETS, context_chars) if response_text else []
            if not mentions:
                row = self._empty_row(
                    run_date=run_id,
                    run_id=run_id,
                    engine=self.name,
                    query_type="geo",
                    query_or_prompt=prompt_text,
                    category=category,
                    priority=priority,
                    domain_matched="false",
                    error=error,
                    cost_pln=str(cost_per),
                )
                rows.append(row)
            else:
                for m in mentions:
                    row = self._empty_row(
                        run_date=run_id,
                        run_id=run_id,
                        engine=self.name,
                        query_type="geo",
                        query_or_prompt=prompt_text,
                        category=m["category"],
                        priority=priority,
                        domain_matched="true",
                        mention_text=m["mention_text"],
                        response_excerpt=m["response_excerpt"],
                        error=error,
                        cost_pln=str(cost_per),
                    )
                    rows.append(row)
        return rows

    def run_mock(self) -> list[dict[str, Any]]:
        """Return mock data without API calls."""
        run_id = date.today().isoformat()
        prompts = self.config.get("prompts", [])
        rows = []
        mock_responses = [
            ("wypasionydraminek.pl", "confirmed", "Możesz zamówić na wypasionydraminek.pl – świetny wybór!"),
            ("draminek", "ambiguous", "Draminek to popularny napój dla dzieci dostępny online."),
            ("", "confirmed", ""),
        ]
        for i, p in enumerate(prompts):
            mention, cat, excerpt = mock_responses[i % len(mock_responses)]
            row = self._empty_row(
                run_date=run_id,
                run_id=run_id,
                engine=self.name,
                query_type="geo",
                query_or_prompt=p.get("prompt", ""),
                category=p.get("category", "") if not mention else cat,
                priority=p.get("priority", "medium"),
                domain_matched="true" if mention else "false",
                mention_text=mention,
                response_excerpt=excerpt,
                cost_pln="0.05",
            )
            rows.append(row)
        return rows
