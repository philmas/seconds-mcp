"""SQLite connection helpers.

Query paths open the database **read-only** (``mode=ro``) so the summarization
API can never mutate the data.  The seed script opens it writable.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

# Default location of the generated database, relative to the repo root.
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "seconds.db"


def resolve_db_path(db_path: str | Path | None = None) -> Path:
    """Resolve the database path from (in order): explicit arg, the
    ``SECONDS_DB_PATH`` env var, or the packaged default."""
    if db_path is not None:
        return Path(db_path)
    env = os.environ.get("SECONDS_DB_PATH")
    return Path(env) if env else DEFAULT_DB_PATH


def get_connection(
    db_path: str | Path | None = None, *, read_only: bool = True
) -> sqlite3.Connection:
    path = resolve_db_path(db_path)
    if read_only:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connect(
    db_path: str | Path | None = None, *, read_only: bool = True
) -> Iterator[sqlite3.Connection]:
    """Context manager that always closes the connection."""
    conn = get_connection(db_path, read_only=read_only)
    try:
        yield conn
    finally:
        conn.close()
