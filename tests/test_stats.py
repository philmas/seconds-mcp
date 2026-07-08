"""Tests for grounded database statistics."""

from __future__ import annotations

from seconds import stats


def test_database_stats_headline(sample_db):
    s = stats.database_stats()
    assert s["total_incidents"] == 6
    assert s["first_call"].startswith("2025-09-01")
    assert s["last_call"].startswith("2025-10-05")
    # 5 of 6 rows have a destination.
    assert s["pct_transported"] == round(500 / 6, 2)
    # Vehicles: UTR-01, UTR-02, UTR-03, ROT-01
    assert s["distinct_vehicles"] == 4
    # Overall avg = (600+800+1000+400+700+1200)/6
    assert s["avg_response_seconds"] == round(4700 / 6, 2)


def test_database_stats_breakdowns(sample_db):
    s = stats.database_stats()
    urgency = {row["key"]: row for row in s["by_urgency"]}
    assert urgency["A1"]["count"] == 5
    assert urgency["A2"]["count"] == 1
    # A1 avg = (600+800+400+700+1200)/5
    assert urgency["A1"]["avg_response"] == round(3700 / 5, 2)

    regions = {row["key"]: row["count"] for row in s["by_region"]}
    assert regions["Utrecht"] == 5
    assert regions["Rotterdam-Rijnmond"] == 1
