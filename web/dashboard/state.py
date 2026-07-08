"""Reflex state for the SECONDS dashboard.

State handlers call the existing ``seconds`` core directly (no HTTP hop): stats
come from :func:`seconds.stats.database_stats`, the reset button re-runs the
sample-data generator, and the logs page reads :mod:`seconds.call_log`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import reflex as rx

from seconds import call_log, stats
from seed.generate_data import generate


class StatsState(rx.State):
    """Live, database-grounded statistics for the Database page."""

    total_incidents: int = 0
    first_call: str = ""
    last_call: str = ""
    avg_response: float = 0.0
    min_response: int = 0
    max_response: int = 0
    distinct_vehicles: int = 0
    pct_transported: float = 0.0

    by_urgency_rows: list[dict[str, str]] = []
    by_region_rows: list[dict[str, str]] = []
    region_chart: list[dict[str, Any]] = []
    urgency_chart: list[dict[str, Any]] = []

    resetting: bool = False
    last_reset: str = ""

    def _apply(self, s: dict[str, Any]) -> None:
        self.total_incidents = s["total_incidents"]
        self.first_call = s["first_call"] or ""
        self.last_call = s["last_call"] or ""
        self.avg_response = s["avg_response_seconds"] or 0.0
        self.min_response = s["min_response_seconds"] or 0
        self.max_response = s["max_response_seconds"] or 0
        self.distinct_vehicles = s["distinct_vehicles"]
        self.pct_transported = s["pct_transported"] or 0.0
        self.by_urgency_rows = [
            {"key": r["key"], "count": str(r["count"]), "avg": str(r["avg_response"])}
            for r in s["by_urgency"]
        ]
        self.by_region_rows = [
            {"key": r["key"], "count": str(r["count"]), "avg": str(r["avg_response"])}
            for r in s["by_region"]
        ]
        self.urgency_chart = [
            {"name": r["key"], "avg": r["avg_response"]} for r in s["by_urgency"]
        ]
        self.region_chart = [
            {"name": r["key"], "avg": r["avg_response"]} for r in s["by_region"]
        ]

    @rx.event
    def load(self):
        self._apply(stats.database_stats())

    @rx.event
    def reset_database(self):
        """Reinitialize the DB with a fresh random dataset, then reload stats."""
        self.resetting = True
        yield
        rows = generate()
        self._apply(stats.database_stats())
        self.last_reset = f"{datetime.now():%Y-%m-%d %H:%M:%S} ({rows} rows)"
        self.resetting = False

    # --- display helpers (metric cards need strings) ---------------------- #
    @rx.var
    def total_display(self) -> str:
        return f"{self.total_incidents:,}"

    @rx.var
    def avg_response_display(self) -> str:
        return f"{self.avg_response:.0f} s ({self.avg_response / 60:.1f} min)"

    @rx.var
    def min_max_display(self) -> str:
        return f"{self.min_response} / {self.max_response} s"

    @rx.var
    def pct_transported_display(self) -> str:
        return f"{self.pct_transported:.1f}%"

    @rx.var
    def vehicles_display(self) -> str:
        return str(self.distinct_vehicles)

    @rx.var
    def date_range_display(self) -> str:
        if not self.first_call or not self.last_call:
            return "—"
        return f"{self.first_call[:10]} → {self.last_call[:10]}"


class LogsState(rx.State):
    """Recent MCP + REST calls for the Logs page."""

    logs: list[dict[str, str]] = []

    def _load(self) -> None:
        rows = call_log.recent(200)
        self.logs = [
            {
                "time": (r["ts"] or "").replace("T", " ").replace("+00:00", ""),
                "source": r["source"],
                "name": r["name"],
                "arguments": r["arguments"] or "",
                "status": r["status"],
                "duration": (
                    f"{r['duration_ms']:.1f} ms" if r["duration_ms"] is not None else ""
                ),
            }
            for r in rows
        ]

    @rx.event
    def load(self):
        self._load()

    @rx.event
    def refresh(self):
        self._load()

    @rx.event
    def clear_logs(self):
        call_log.clear()
        self.logs = []
