"""Lightweight call/trace log for the API and MCP tools.

Every MCP tool call and REST request is recorded here so the dashboard's
"Logs / traces" page can show what the agent did: which tool, with which
arguments, the status and how long it took.

Design notes:
* Logs live in their **own** SQLite database (``data/seconds_logs.db``), separate
  from the incidents data.  That keeps the incidents DB strictly read-only for
  queries and means reinitializing the incidents data does not wipe the audit
  trail.
* The DB is opened in **WAL** mode so the MCP-server process and the Reflex
  dashboard process can read/write concurrently.
* Logging must never break the thing being logged: all writes are best-effort
  and swallow their own errors.
"""

from __future__ import annotations

import functools
import inspect
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

DEFAULT_LOGS_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "seconds_logs.db"

_MAX_FIELD = 2000  # truncate serialized args/results to keep the log compact


def resolve_logs_path(db_path: str | Path | None = None) -> Path:
    if db_path is not None:
        return Path(db_path)
    env = os.environ.get("SECONDS_LOGS_DB_PATH")
    return Path(env) if env else DEFAULT_LOGS_DB_PATH


def _connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = resolve_logs_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS call_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT    NOT NULL,
            source      TEXT    NOT NULL,
            name        TEXT    NOT NULL,
            arguments   TEXT,
            status      TEXT    NOT NULL,
            duration_ms REAL,
            result      TEXT,
            error       TEXT
        )
        """
    )
    return conn


def _serialize(value: Any) -> str:
    try:
        text = json.dumps(value, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        text = str(value)
    return text if len(text) <= _MAX_FIELD else text[:_MAX_FIELD] + "…"


def record(
    source: str,
    name: str,
    arguments: Any = None,
    status: str = "ok",
    duration_ms: float | None = None,
    result: Any = None,
    error: str | None = None,
    *,
    db_path: str | Path | None = None,
) -> None:
    """Best-effort insert of one log row.  Never raises."""
    try:
        with _connect(db_path) as conn:
            conn.execute(
                "INSERT INTO call_log (ts, source, name, arguments, status, "
                "duration_ms, result, error) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    source,
                    name,
                    _serialize(arguments) if arguments is not None else None,
                    status,
                    duration_ms,
                    _serialize(result) if result is not None else None,
                    error,
                ),
            )
            conn.commit()
    except sqlite3.Error as exc:  # pragma: no cover - logging must not break callers
        print(f"[call_log] failed to record {name!r}: {exc}", file=sys.stderr)


def recent(limit: int = 100, *, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Return the most recent log rows, newest first."""
    try:
        with _connect(db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM call_log ORDER BY id DESC LIMIT ?", (int(limit),)
            ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:  # pragma: no cover
        print(f"[call_log] failed to read log: {exc}", file=sys.stderr)
        return []


def clear(*, db_path: str | Path | None = None) -> None:
    """Delete all log rows."""
    try:
        with _connect(db_path) as conn:
            conn.execute("DELETE FROM call_log")
            conn.commit()
    except sqlite3.Error as exc:  # pragma: no cover
        print(f"[call_log] failed to clear log: {exc}", file=sys.stderr)


def logged(source: str) -> Callable[[Callable], Callable]:
    """Decorator that records each call to ``fn`` (status, args, duration).

    ``functools.wraps`` preserves the wrapped function's signature and
    annotations, so FastMCP still generates the correct tool schema.
    """

    def decorator(fn: Callable) -> Callable:
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                arguments = dict(sig.bind_partial(*args, **kwargs).arguments)
            except TypeError:
                arguments = {"args": args, "kwargs": kwargs}
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                record(
                    source,
                    fn.__name__,
                    arguments,
                    status="error",
                    duration_ms=round((time.perf_counter() - start) * 1000, 2),
                    error=str(exc),
                )
                raise
            record(
                source,
                fn.__name__,
                arguments,
                status="ok",
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
                result=result,
            )
            return result

        return wrapper

    return decorator
