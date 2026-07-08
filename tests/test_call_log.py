"""Tests for the call/trace log store and the logging decorator."""

from __future__ import annotations

import pytest

from seconds import call_log


@pytest.fixture()
def logs_db(tmp_path):
    return tmp_path / "logs.db"


def test_record_and_recent(logs_db):
    call_log.record("mcp", "summarize", {"metric": "avg"}, "ok", 1.5,
                    result={"value": 42}, db_path=logs_db)
    call_log.record("api", "GET /stats", {}, "ok", 0.2, db_path=logs_db)

    rows = call_log.recent(db_path=logs_db)
    assert len(rows) == 2
    # Newest first.
    assert rows[0]["name"] == "GET /stats"
    assert rows[1]["name"] == "summarize"
    assert rows[1]["source"] == "mcp"
    assert rows[1]["status"] == "ok"


def test_clear(logs_db):
    call_log.record("mcp", "trend", db_path=logs_db)
    assert call_log.recent(db_path=logs_db)
    call_log.clear(db_path=logs_db)
    assert call_log.recent(db_path=logs_db) == []


def test_logged_decorator_records_success(logs_db, monkeypatch):
    monkeypatch.setenv("SECONDS_LOGS_DB_PATH", str(logs_db))

    @call_log.logged("mcp")
    def add(a: int, b: int) -> int:
        return a + b

    assert add(2, 3) == 5
    rows = call_log.recent(db_path=logs_db)
    assert len(rows) == 1
    assert rows[0]["name"] == "add"
    assert rows[0]["status"] == "ok"
    assert '"a": 2' in rows[0]["arguments"]


def test_logged_decorator_records_error_and_reraises(logs_db, monkeypatch):
    monkeypatch.setenv("SECONDS_LOGS_DB_PATH", str(logs_db))

    @call_log.logged("mcp")
    def boom() -> None:
        raise ValueError("nope")

    with pytest.raises(ValueError):
        boom()
    rows = call_log.recent(db_path=logs_db)
    assert rows[0]["status"] == "error"
    assert "nope" in rows[0]["error"]


def test_logged_preserves_signature(logs_db):
    import inspect

    @call_log.logged("mcp")
    def tool(metric: str, column: str | None = None) -> dict:
        return {}

    # FastMCP relies on the wrapped signature to build the tool schema.
    params = list(inspect.signature(tool).parameters)
    assert params == ["metric", "column"]
