"""Shared test fixtures.

Builds a small SQLite database with **known** rows so aggregates can be asserted
exactly, and points the app at it via the ``SECONDS_DB_PATH`` env var.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from seconds.db import connect
from seed.generate_data import INSERT_SQL, create_incidents_table

# (call_id, timestamp, region, urgency, response, on_scene, transport, vehicle, destination)
# Four A1 calls in September (600, 800, 400, 700) -> avg 625; the 09-30 row is
# late in the day to prove that date_to is inclusive.  One October row is the
# out-of-range control.
SAMPLE_ROWS = [
    ("c1", "2025-09-01T08:00:00", "Utrecht", "A1", 600, 700, 900, "UTR-01", "UMC Utrecht"),
    ("c2", "2025-09-10T09:30:00", "Utrecht", "A1", 800, 650, None, "UTR-01", None),
    ("c3", "2025-09-15T12:00:00", "Utrecht", "A2", 1000, 800, 1200, "UTR-02", "St. Antonius"),
    ("c4", "2025-09-20T22:15:00", "Rotterdam-Rijnmond", "A1", 400, 500, 600, "ROT-01", "Erasmus MC"),
    ("c5", "2025-09-30T20:45:00", "Utrecht", "A1", 700, 600, 800, "UTR-03", "UMC Utrecht"),
    ("c6", "2025-10-05T11:00:00", "Utrecht", "A1", 1200, 900, 1500, "UTR-01", "UMC Utrecht"),
]


@pytest.fixture(scope="session")
def sample_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    data_dir = tmp_path_factory.mktemp("data")
    db_path = data_dir / "test.db"
    with connect(db_path, read_only=False) as conn:
        create_incidents_table(conn)
        conn.executemany(INSERT_SQL, SAMPLE_ROWS)
        conn.commit()
    os.environ["SECONDS_DB_PATH"] = str(db_path)
    # Keep API-middleware / MCP logging out of the real logs DB during tests.
    os.environ["SECONDS_LOGS_DB_PATH"] = str(data_dir / "test_logs.db")
    yield db_path
    os.environ.pop("SECONDS_DB_PATH", None)
    os.environ.pop("SECONDS_LOGS_DB_PATH", None)
