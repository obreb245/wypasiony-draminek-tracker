"""Tests for csv_writer — append-only behavior."""
import csv
import os
import tempfile
import pytest
from src.storage.csv_writer import append_rows, MASTER_HEADERS


def make_row(**kwargs):
    row = {k: "" for k in MASTER_HEADERS}
    row.update(kwargs)
    return row


def test_creates_file_with_header():
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode='w') as f:
        path = f.name
    os.unlink(path)  # Remove so writer creates it
    try:
        append_rows(path, [make_row(engine="test", run_id="2026-05-01")])
        with open(path) as f:
            lines = f.readlines()
        assert lines[0].strip() == ",".join(MASTER_HEADERS)
        assert len(lines) == 2  # header + 1 row
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_append_only_two_calls():
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode='w') as f:
        path = f.name
    os.unlink(path)
    try:
        row1 = make_row(engine="anthropic", run_id="2026-05-01", query_or_prompt="p1")
        row2 = make_row(engine="openai", run_id="2026-05-01", query_or_prompt="p2")
        append_rows(path, [row1])
        append_rows(path, [row2])
        with open(path) as f:
            reader = list(csv.DictReader(f))
        assert len(reader) == 2
        assert reader[0]["engine"] == "anthropic"
        assert reader[1]["engine"] == "openai"
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_returns_count():
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode='w') as f:
        path = f.name
    os.unlink(path)
    try:
        rows = [make_row(engine="test") for _ in range(5)]
        count = append_rows(path, rows)
        assert count == 5
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_empty_rows_returns_zero():
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name
    try:
        count = append_rows(path, [])
        assert count == 0
    finally:
        os.unlink(path)
