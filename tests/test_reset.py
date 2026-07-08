"""Tests for database (re)initialization used by the reset feature."""

from __future__ import annotations

import sqlite3

from seed.generate_data import generate


def _count(db_path) -> int:
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    finally:
        conn.close()


def _dump(db_path):
    """The full ordered dataset, so two runs can be compared exactly."""
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute(
            "SELECT region, urgency, response_time_seconds FROM incidents ORDER BY id"
        ).fetchall()
    finally:
        conn.close()


def test_generate_creates_rows(tmp_path):
    db = tmp_path / "reset.db"
    assert generate(db_path=db, count=50) == 50
    assert _count(db) == 50


def test_generate_replaces_without_duplicating(tmp_path):
    db = tmp_path / "reset.db"
    generate(db_path=db, count=50)
    # Re-running drops + recreates the table, so the row count stays put.
    assert generate(db_path=db, count=50) == 50
    assert _count(db) == 50


def test_generate_reseeds_by_default(tmp_path):
    """Reset / reinitialize should produce a *different* dataset each time."""
    db = tmp_path / "reset.db"
    generate(db_path=db, count=200)
    before = _dump(db)
    generate(db_path=db, count=200)
    assert _dump(db) != before


def test_generate_is_reproducible_with_explicit_seed(tmp_path):
    """A fixed seed reproduces the exact same data (for reproducible fixtures)."""
    db = tmp_path / "reset.db"
    generate(db_path=db, count=200, seed=123)
    seeded = _dump(db)
    generate(db_path=db, count=200, seed=123)
    assert _dump(db) == seeded
    # …and a different seed yields different data.
    generate(db_path=db, count=200, seed=456)
    assert _dump(db) != seeded
