"""Unit tests for the core query layer against known sample data."""

from __future__ import annotations

import pytest

from seconds import queries

SEPTEMBER = {"date_from": "2025-09-01", "date_to": "2025-09-30"}


def test_summarize_avg_a1_in_september(sample_db):
    result = queries.summarize(
        "avg", "response_time_seconds", urgency="A1", **SEPTEMBER
    )
    # A1 September response times: 600, 800, 400, 700 -> avg 625, 4 rows.
    assert result["value"] == 625.0
    assert result["count"] == 4
    assert result["column"] == "response_time_seconds"


def test_date_to_is_inclusive(sample_db):
    # The 2025-09-30T20:45 row must be counted.
    result = queries.summarize("count", urgency="A1", **SEPTEMBER)
    assert result["count"] == 4


def test_summarize_min_and_max(sample_db):
    assert queries.summarize("min", "response_time_seconds", urgency="A1", **SEPTEMBER)["value"] == 400
    assert queries.summarize("max", "response_time_seconds", urgency="A1", **SEPTEMBER)["value"] == 800


def test_count_ignores_column(sample_db):
    result = queries.summarize("count", **SEPTEMBER)
    assert result["count"] == 5  # all September rows
    assert result["column"] is None


def test_group_by_region(sample_db):
    result = queries.group_by(
        "avg", "region", "response_time_seconds", urgency="A1", **SEPTEMBER
    )
    by_group = {r["group"]: r for r in result["results"]}
    assert by_group["Utrecht"]["value"] == 700.0  # (600+800+700)/3
    assert by_group["Utrecht"]["count"] == 3
    assert by_group["Rotterdam-Rijnmond"]["value"] == 400.0


def test_group_by_month_bucket(sample_db):
    result = queries.group_by("count", "month", "response_time_seconds")
    by_group = {r["group"]: r["count"] for r in result["results"]}
    assert by_group["2025-09"] == 5
    assert by_group["2025-10"] == 1


def test_trend_monthly(sample_db):
    result = queries.trend("avg", "response_time_seconds", bucket="month")
    periods = [p["period"] for p in result["points"]]
    assert periods == ["2025-09", "2025-10"]
    assert result["bucket"] == "month"


def test_trend_moving_average(sample_db):
    result = queries.trend(
        "count", "response_time_seconds", bucket="month", moving_average_window=2
    )
    points = result["points"]
    assert points[0]["moving_average"] == points[0]["value"]  # first bucket
    # Second bucket = mean of counts 5 and 1 = 3.0
    assert points[1]["moving_average"] == 3.0


def test_distinct_values(sample_db):
    assert queries.distinct_values("urgency") == ["A1", "A2"]


@pytest.mark.parametrize(
    "call",
    [
        lambda: queries.summarize("avg", "region"),  # not numeric
        lambda: queries.summarize("avg", "nonexistent"),  # unknown column
        lambda: queries.summarize("median", "response_time_seconds"),  # bad metric
        lambda: queries.summarize("avg"),  # missing column
        lambda: queries.group_by("avg", "unknown_dim", "response_time_seconds"),
        lambda: queries.distinct_values("response_time_seconds"),  # not categorical
        lambda: queries.summarize("count", date_from="09-01-2025"),  # bad date
    ],
)
def test_invalid_inputs_raise_value_error(sample_db, call):
    with pytest.raises(ValueError):
        call()
