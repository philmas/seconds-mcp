"""Grounded database statistics for the dashboard.

``database_stats`` computes headline numbers straight from the incidents table so
the "Database" page always reflects the live data (and, after a reset, the known
ground-truth data used to validate MCP answers).
"""

from __future__ import annotations

from typing import Any

from . import schema
from .db import connect


def _round(value: Any) -> Any:
    return round(value, 2) if isinstance(value, float) else value


def database_stats(db_path: Any = None) -> dict[str, Any]:
    """Return headline statistics computed live from the incidents table."""
    with connect(db_path) as conn:
        totals = conn.execute(
            f"""
            SELECT
                COUNT(*)                          AS total,
                MIN(timestamp)                    AS first_call,
                MAX(timestamp)                    AS last_call,
                AVG(response_time_seconds)        AS avg_response,
                MIN(response_time_seconds)        AS min_response,
                MAX(response_time_seconds)        AS max_response,
                COUNT(DISTINCT vehicle_id)        AS vehicles,
                100.0 * SUM(CASE WHEN destination IS NOT NULL THEN 1 ELSE 0 END)
                    / COUNT(*)                    AS pct_transported
            FROM {schema.TABLE}
            """
        ).fetchone()

        by_urgency = conn.execute(
            f"""
            SELECT urgency AS key, COUNT(*) AS count,
                   AVG(response_time_seconds) AS avg_response
            FROM {schema.TABLE} GROUP BY urgency ORDER BY urgency
            """
        ).fetchall()

        by_region = conn.execute(
            f"""
            SELECT region AS key, COUNT(*) AS count,
                   AVG(response_time_seconds) AS avg_response
            FROM {schema.TABLE} GROUP BY region ORDER BY region
            """
        ).fetchall()

    def _breakdown(rows: list) -> list[dict[str, Any]]:
        return [
            {
                "key": r["key"],
                "count": r["count"],
                "avg_response": _round(r["avg_response"]),
            }
            for r in rows
        ]

    return {
        "total_incidents": totals["total"],
        "first_call": totals["first_call"],
        "last_call": totals["last_call"],
        "avg_response_seconds": _round(totals["avg_response"]),
        "min_response_seconds": totals["min_response"],
        "max_response_seconds": totals["max_response"],
        "distinct_vehicles": totals["vehicles"],
        "pct_transported": _round(totals["pct_transported"]),
        "by_urgency": _breakdown(by_urgency),
        "by_region": _breakdown(by_region),
    }
