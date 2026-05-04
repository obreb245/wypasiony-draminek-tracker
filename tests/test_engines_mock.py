"""Tests for all engine mock modes — no API keys needed."""
import pytest
import yaml
from src.engines.base import ROW_SCHEMA


def load_settings():
    with open("config/settings.yaml") as f:
        return yaml.safe_load(f)


def load_queries():
    with open("config/queries.yaml") as f:
        return yaml.safe_load(f)


def load_ai_prompts():
    with open("config/ai_prompts.yaml") as f:
        return yaml.safe_load(f)


def assert_valid_rows(rows, engine_name):
    assert isinstance(rows, list), f"{engine_name}: expected list"
    assert len(rows) > 0, f"{engine_name}: expected non-empty list"
    for row in rows:
        for key in ROW_SCHEMA:
            assert key in row, f"{engine_name}: missing key '{key}' in row"
        assert row["engine"] == engine_name, f"{engine_name}: wrong engine name in row"


def test_anthropic_mock():
    from src.engines.anthropic_engine import AnthropicEngine
    settings = load_settings()
    config = load_ai_prompts()
    engine = AnthropicEngine(settings, config)
    rows = engine.run_mock()
    assert_valid_rows(rows, "anthropic")


def test_openai_mock():
    from src.engines.openai_engine import OpenAIEngine
    settings = load_settings()
    config = load_ai_prompts()
    engine = OpenAIEngine(settings, config)
    rows = engine.run_mock()
    assert_valid_rows(rows, "openai")


def test_perplexity_mock():
    from src.engines.perplexity import PerplexityEngine
    settings = load_settings()
    config = load_ai_prompts()
    engine = PerplexityEngine(settings, config)
    rows = engine.run_mock()
    assert_valid_rows(rows, "perplexity")


def test_gemini_mock():
    from src.engines.gemini import GeminiEngine
    settings = load_settings()
    config = load_ai_prompts()
    engine = GeminiEngine(settings, config)
    rows = engine.run_mock()
    assert_valid_rows(rows, "gemini")


def test_google_mock():
    from src.engines.google import GoogleEngine
    settings = load_settings()
    config = load_queries()
    engine = GoogleEngine(settings, config)
    rows = engine.run_mock()
    assert_valid_rows(rows, "google")


def test_bing_mock():
    from src.engines.bing import BingEngine
    settings = load_settings()
    config = load_queries()
    engine = BingEngine(settings, config)
    rows = engine.run_mock()
    assert_valid_rows(rows, "bing")


def test_mock_rows_have_correct_query_type():
    from src.engines.anthropic_engine import AnthropicEngine
    from src.engines.google import GoogleEngine
    settings = load_settings()
    ai_rows = AnthropicEngine(settings, load_ai_prompts()).run_mock()
    seo_rows = GoogleEngine(settings, load_queries()).run_mock()
    for r in ai_rows:
        assert r["query_type"] == "geo", f"Expected geo, got {r['query_type']}"
    for r in seo_rows:
        assert r["query_type"] == "seo", f"Expected seo, got {r['query_type']}"


def test_mock_row_count_matches_config():
    from src.engines.anthropic_engine import AnthropicEngine
    settings = load_settings()
    config = load_ai_prompts()
    engine = AnthropicEngine(settings, config)
    rows = engine.run_mock()
    prompts = config.get("prompts", [])
    assert len(rows) == len(prompts), f"Expected {len(prompts)} rows, got {len(rows)}"
