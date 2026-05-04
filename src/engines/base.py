"""Abstract base class for all tracker engines."""
from abc import ABC, abstractmethod
from typing import Any


# Required keys in every row returned by engines
ROW_SCHEMA = [
    "run_date", "run_id", "engine", "query_type", "query_or_prompt",
    "category", "priority", "position", "url_found", "domain_matched",
    "mention_text", "response_excerpt", "raw_response_path", "error", "cost_pln",
]


class BaseEngine(ABC):
    """Base class for SEO and GEO tracking engines."""

    name: str = "base"

    def __init__(self, settings: dict, config: dict):
        self.settings = settings
        self.config = config

    @abstractmethod
    def run(self, dry_run: bool = False) -> list[dict[str, Any]]:
        """Run the engine and return list of result rows matching ROW_SCHEMA."""

    @abstractmethod
    def run_mock(self) -> list[dict[str, Any]]:
        """Return mock result rows without making any API calls."""

    def _empty_row(self, **kwargs) -> dict[str, Any]:
        """Create an empty row with all required keys, overridden by kwargs."""
        row = {k: "" for k in ROW_SCHEMA}
        row.update(kwargs)
        return row
