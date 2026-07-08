"""Generate a SQLite database of sample ambulance-dispatch data.

Run from the repo root::

    python -m seed.generate_data

Each run generates a fresh random dataset, so re-initializing the database
yields new data; pass an explicit ``seed`` to reproduce a specific dataset (the
tests do this).  The domain mirrors the "SECONDS" ambulance-dispatch software:
each row is an emergency call with an urgency class and a response time, so
questions like "average A1 response time in September" are meaningful.
"""

from __future__ import annotations

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from seconds.db import DEFAULT_DB_PATH, connect, resolve_db_path

# Dutch ambulance-region (RAV) names.
REGIONS = [
    "Amsterdam-Amstelland",
    "Rotterdam-Rijnmond",
    "Utrecht",
    "Gelderland-Zuid",
]

# Urgency classes with their share of calls.  A1 = life-threatening (lights &
# sirens), A2 = urgent, B = planned transport.
URGENCIES = [("A1", 0.45), ("A2", 0.35), ("B", 0.20)]

# Rough mean response time (seconds) per urgency class.
RESPONSE_MEAN = {"A1": 540, "A2": 900, "B": 1800}

HOSPITALS = {
    "Amsterdam-Amstelland": ["Amsterdam UMC", "OLVG"],
    "Rotterdam-Rijnmond": ["Erasmus MC", "Maasstad Ziekenhuis"],
    "Utrecht": ["UMC Utrecht", "St. Antonius"],
    "Gelderland-Zuid": ["Radboudumc", "CWZ"],
}

CREATE_TABLE_SQL = """
CREATE TABLE incidents (
    id                    INTEGER PRIMARY KEY,
    call_id               TEXT    NOT NULL,
    timestamp             TEXT    NOT NULL,
    region                TEXT    NOT NULL,
    urgency               TEXT    NOT NULL,
    response_time_seconds INTEGER NOT NULL,
    on_scene_seconds      INTEGER NOT NULL,
    transport_seconds     INTEGER,
    vehicle_id            TEXT    NOT NULL,
    destination           TEXT
)
"""

INSERT_SQL = """
INSERT INTO incidents (
    call_id, timestamp, region, urgency, response_time_seconds,
    on_scene_seconds, transport_seconds, vehicle_id, destination
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def create_incidents_table(conn: sqlite3.Connection) -> None:
    """(Re)create an empty ``incidents`` table.  Shared with the test suite."""
    conn.execute("DROP TABLE IF EXISTS incidents")
    conn.execute(CREATE_TABLE_SQL)


def _weighted_urgency(rng: random.Random) -> str:
    roll = rng.random()
    cumulative = 0.0
    for urgency, share in URGENCIES:
        cumulative += share
        if roll <= cumulative:
            return urgency
    return URGENCIES[-1][0]


def _response_time(rng: random.Random, urgency: str, when: datetime) -> int:
    """Response time in seconds with plausible seasonal and day/night variation."""
    mean = RESPONSE_MEAN[urgency]
    # Winter months are a little slower; nights are a little faster.
    seasonal = 1.12 if when.month in (12, 1, 2) else 1.0
    night = 0.9 if when.hour < 6 or when.hour >= 22 else 1.0
    value = rng.gauss(mean * seasonal * night, mean * 0.25)
    return max(120, round(value))


def generate_rows(count: int, rng: random.Random) -> list[tuple]:
    start = datetime(2025, 1, 1)
    rows: list[tuple] = []
    for i in range(1, count + 1):
        when = start + timedelta(
            days=rng.randint(0, 364),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
            seconds=rng.randint(0, 59),
        )
        region = rng.choice(REGIONS)
        urgency = _weighted_urgency(rng)
        response = _response_time(rng, urgency, when)
        on_scene = rng.randint(300, 1800)
        vehicle_id = f"{region.split('-')[0][:3].upper()}-{rng.randint(1, 8):02d}"

        # ~15% of calls are treat-and-release (no transport / destination).
        if rng.random() < 0.15:
            transport = None
            destination = None
        else:
            transport = rng.randint(300, 2400)
            destination = rng.choice(HOSPITALS[region])

        rows.append(
            (
                f"2025-{i:06d}",
                when.isoformat(timespec="seconds"),
                region,
                urgency,
                response,
                on_scene,
                transport,
                vehicle_id,
                destination,
            )
        )
    return rows


def generate(
    db_path: Path | str | None = None, count: int = 4000, seed: int | None = None
) -> int:
    """Create the database and populate it with ``count`` sample incidents.

    The path resolves the same way as the query layer (explicit arg, then the
    ``SECONDS_DB_PATH`` env var, then the packaged default), so a reset targets
    the database the API/MCP actually read.  Returns the number of rows inserted.

    With the default ``seed=None`` each call produces different data (so a
    reset / reinitialize gives a fresh dataset); pass a fixed ``seed`` for a
    reproducible dataset.
    """
    path = resolve_db_path(db_path)
    rng = random.Random(seed)
    rows = generate_rows(count, rng)
    with connect(path, read_only=False) as conn:
        create_incidents_table(conn)
        conn.executemany(INSERT_SQL, rows)
        conn.execute("CREATE INDEX idx_incidents_timestamp ON incidents(timestamp)")
        conn.commit()
    return len(rows)


if __name__ == "__main__":
    inserted = generate()
    print(f"Inserted {inserted} incidents into {resolve_db_path()}")
