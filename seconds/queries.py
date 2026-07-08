"""Core query layer.

Pure, dependency-light functions that turn a validated request into safe,
parameterized SQL and return plain dictionaries.  Both the FastAPI routes
(``api.py``) and the MCP tools (``mcp_server.py``) are thin wrappers over these
functions, so the summarization logic lives in exactly one place.

Safety model:
* Column and aggregation *identifiers* are always validated against the
  whitelist in :mod:`seconds.schema` before they touch a SQL string.
* Filter *values* are passed as bound parameters, never string-formatted.
* Connections are opened read-only.
"""

from __future__ import annotations

from datetime import date, timedelta
from enum import Enum
from typing import Any

from . import schema
from .db import connect


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _norm(value: Any) -> str:
    """Normalize an enum-or-string argument to its plain string value."""
    return value.value if isinstance(value, Enum) else str(value)


def _round(value: Any) -> Any:
    """Round floats to 2 decimals; leave ints / None untouched."""
    return round(value, 2) if isinstance(value, float) else value


def _end_exclusive(day: str) -> str:
    """Return the day *after* ``day`` (YYYY-MM-DD) so ``date_to`` is inclusive.

    Timestamps are full datetimes, so ``timestamp < <day+1>`` includes every
    record on ``day`` itself.
    """
    try:
        parsed = date.fromisoformat(day)
    except ValueError as exc:
        raise ValueError(f"Invalid date {day!r}, expected YYYY-MM-DD.") from exc
    return (parsed + timedelta(days=1)).isoformat()


def _validate_date(day: str) -> str:
    try:
        date.fromisoformat(day)
    except ValueError as exc:
        raise ValueError(f"Invalid date {day!r}, expected YYYY-MM-DD.") from exc
    return day


def _build_where(
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    region: str | None = None,
    urgency: str | None = None,
    vehicle_id: str | None = None,
) -> tuple[str, list[Any]]:
    """Build a parameterized WHERE clause from optional filters."""
    clauses: list[str] = []
    params: list[Any] = []

    if date_from:
        clauses.append(f"{schema.TIMESTAMP_COLUMN} >= ?")
        params.append(_validate_date(date_from))
    if date_to:
        clauses.append(f"{schema.TIMESTAMP_COLUMN} < ?")
        params.append(_end_exclusive(date_to))

    # Categorical equality filters.  Column names are fixed here (not user
    # supplied) but we still assert their role for defence in depth.
    for column, value in (
        ("region", region),
        ("urgency", urgency),
        ("vehicle_id", vehicle_id),
    ):
        if value is not None:
            schema.require_categorical(column)
            clauses.append(f"{column} = ?")
            params.append(value)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


def _agg_expression(metric: str, column: str | None) -> tuple[str, str | None]:
    """Return ``(sql_expression, resolved_column)`` for an aggregate.

    ``count`` counts rows and ignores ``column``; every other metric requires a
    numeric column.
    """
    metric = schema.require_aggregation(_norm(metric))
    if metric == "count":
        return "COUNT(*)", None
    if column is None:
        raise ValueError(f"Metric {metric!r} requires a numeric 'column'.")
    column = schema.require_numeric(column)
    return f"{schema.AGGREGATIONS[metric]}({column})", column


def _group_expression(group_by: str) -> str:
    """Return a safe SQL expression to GROUP BY.

    ``group_by`` may be a time bucket (day/week/month) or a categorical column.
    Both are validated against whitelists, so the result is safe to inline.
    """
    if group_by in schema.TIME_BUCKETS:
        fmt = schema.TIME_BUCKETS[group_by]
        return f"strftime('{fmt}', {schema.TIMESTAMP_COLUMN})"
    schema.require_categorical(group_by)
    return group_by


# --------------------------------------------------------------------------- #
# Public query functions
# --------------------------------------------------------------------------- #
def list_schema(db_path: Any = None) -> dict[str, Any]:
    """Describe the table so an agent can discover what it can query."""
    columns = []
    for name, meta in schema.COLUMNS.items():
        entry: dict[str, Any] = {
            "name": name,
            "type": meta["type"],
            "role": meta["role"],
        }
        if meta["role"] == schema.CATEGORICAL:
            entry["example_values"] = distinct_values(name, db_path=db_path, limit=5)
        columns.append(entry)
    return {
        "table": schema.TABLE,
        "columns": columns,
        "aggregations": list(schema.AGGREGATIONS),
        "time_buckets": list(schema.TIME_BUCKETS),
    }


def distinct_values(
    column: str, *, db_path: Any = None, limit: int | None = None
) -> list[Any]:
    """List the distinct non-null values of a categorical column."""
    column = schema.require_categorical(column)
    sql = (
        f"SELECT DISTINCT {column} AS value FROM {schema.TABLE} "
        f"WHERE {column} IS NOT NULL ORDER BY {column}"
    )
    if limit is not None:
        sql += f" LIMIT {int(limit)}"  # int() guarantees this is numeric
    with connect(db_path) as conn:
        rows = conn.execute(sql).fetchall()
    return [row["value"] for row in rows]


def summarize(
    metric: str,
    column: str | None = None,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    region: str | None = None,
    urgency: str | None = None,
    vehicle_id: str | None = None,
    db_path: Any = None,
) -> dict[str, Any]:
    """Compute a single aggregate over the (optionally filtered) rows."""
    agg, resolved = _agg_expression(metric, column)
    where, params = _build_where(
        date_from=date_from,
        date_to=date_to,
        region=region,
        urgency=urgency,
        vehicle_id=vehicle_id,
    )
    sql = f"SELECT {agg} AS value, COUNT(*) AS count FROM {schema.TABLE}{where}"
    with connect(db_path) as conn:
        row = conn.execute(sql, params).fetchone()
    return {
        "metric": _norm(metric),
        "column": resolved,
        "value": _round(row["value"]),
        "count": row["count"],
    }


def group_by(
    metric: str,
    group_by: str,
    column: str | None = None,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    region: str | None = None,
    urgency: str | None = None,
    vehicle_id: str | None = None,
    db_path: Any = None,
) -> dict[str, Any]:
    """Compute an aggregate grouped by a dimension or time bucket."""
    agg, resolved = _agg_expression(metric, column)
    group_expr = _group_expression(group_by)
    where, params = _build_where(
        date_from=date_from,
        date_to=date_to,
        region=region,
        urgency=urgency,
        vehicle_id=vehicle_id,
    )
    sql = (
        f"SELECT {group_expr} AS grp, {agg} AS value, COUNT(*) AS count "
        f"FROM {schema.TABLE}{where} GROUP BY {group_expr} ORDER BY {group_expr}"
    )
    with connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return {
        "metric": _norm(metric),
        "column": resolved,
        "group_by": group_by,
        "results": [
            {"group": row["grp"], "value": _round(row["value"]), "count": row["count"]}
            for row in rows
        ],
    }


def trend(
    metric: str,
    column: str | None = None,
    *,
    bucket: str = "month",
    moving_average_window: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    region: str | None = None,
    urgency: str | None = None,
    vehicle_id: str | None = None,
    db_path: Any = None,
) -> dict[str, Any]:
    """Compute a time-ordered series with an optional trailing moving average."""
    bucket = schema.require_bucket(_norm(bucket))
    grouped = group_by(
        metric,
        bucket,
        column,
        date_from=date_from,
        date_to=date_to,
        region=region,
        urgency=urgency,
        vehicle_id=vehicle_id,
        db_path=db_path,
    )
    points = [
        {"period": item["group"], "value": item["value"], "count": item["count"]}
        for item in grouped["results"]
    ]
    if moving_average_window and moving_average_window > 1:
        _add_moving_average(points, moving_average_window)
    return {
        "metric": _norm(metric),
        "column": grouped["column"],
        "bucket": bucket,
        "points": points,
    }


def _add_moving_average(points: list[dict[str, Any]], window: int) -> None:
    """Attach a trailing moving average of ``value`` to each point in place."""
    values = [p["value"] for p in points]
    for i, point in enumerate(points):
        chunk = [v for v in values[max(0, i - window + 1) : i + 1] if v is not None]
        point["moving_average"] = _round(sum(chunk) / len(chunk)) if chunk else None
