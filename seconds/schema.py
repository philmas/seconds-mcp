"""Static metadata for the ``incidents`` table.

This module is the single source of truth about which columns exist, what type
they have and what *role* they play (numeric / categorical / temporal).  Every
query is validated against this whitelist before any SQL is built, so column and
aggregation names can never come straight from untrusted input.
"""

from __future__ import annotations

# Column roles.
NUMERIC = "numeric"
CATEGORICAL = "categorical"
TEMPORAL = "temporal"

# The (single) table this API summarizes.
TABLE = "incidents"

# The temporal column used for date filters and time-bucketing.
TIMESTAMP_COLUMN = "timestamp"

# name -> (sql type, role).  ``None`` role = identifier column, not summarizable.
COLUMNS: dict[str, dict[str, str | None]] = {
    "id": {"type": "INTEGER", "role": None},
    "call_id": {"type": "TEXT", "role": None},
    "timestamp": {"type": "TEXT", "role": TEMPORAL},
    "region": {"type": "TEXT", "role": CATEGORICAL},
    "urgency": {"type": "TEXT", "role": CATEGORICAL},
    "response_time_seconds": {"type": "INTEGER", "role": NUMERIC},
    "on_scene_seconds": {"type": "INTEGER", "role": NUMERIC},
    "transport_seconds": {"type": "INTEGER", "role": NUMERIC},
    "vehicle_id": {"type": "TEXT", "role": CATEGORICAL},
    "destination": {"type": "TEXT", "role": CATEGORICAL},
}

# Aggregation name -> SQL function.  ``count`` maps to COUNT(*) and is handled
# separately because it does not need a numeric column.
AGGREGATIONS: dict[str, str] = {
    "avg": "AVG",
    "sum": "SUM",
    "min": "MIN",
    "max": "MAX",
    "count": "COUNT",
}

# Supported time buckets for group-by / trend, mapped to a strftime format.
TIME_BUCKETS: dict[str, str] = {
    "day": "%Y-%m-%d",
    "week": "%Y-W%W",
    "month": "%Y-%m",
}


def all_columns() -> list[str]:
    return list(COLUMNS)


def columns_with_role(role: str) -> list[str]:
    return [name for name, meta in COLUMNS.items() if meta["role"] == role]


def numeric_columns() -> list[str]:
    return columns_with_role(NUMERIC)


def categorical_columns() -> list[str]:
    return columns_with_role(CATEGORICAL)


def require_column(column: str) -> str:
    if column not in COLUMNS:
        raise ValueError(
            f"Unknown column {column!r}. Available columns: {', '.join(all_columns())}."
        )
    return column


def require_numeric(column: str) -> str:
    require_column(column)
    if COLUMNS[column]["role"] != NUMERIC:
        raise ValueError(
            f"Column {column!r} is not numeric. Numeric columns: "
            f"{', '.join(numeric_columns())}."
        )
    return column


def require_categorical(column: str) -> str:
    require_column(column)
    if COLUMNS[column]["role"] != CATEGORICAL:
        raise ValueError(
            f"Column {column!r} is not categorical. Categorical columns: "
            f"{', '.join(categorical_columns())}."
        )
    return column


def require_aggregation(metric: str) -> str:
    if metric not in AGGREGATIONS:
        raise ValueError(
            f"Unknown metric {metric!r}. Available metrics: "
            f"{', '.join(AGGREGATIONS)}."
        )
    return metric


def require_bucket(bucket: str) -> str:
    if bucket not in TIME_BUCKETS:
        raise ValueError(
            f"Unknown time bucket {bucket!r}. Available buckets: "
            f"{', '.join(TIME_BUCKETS)}."
        )
    return bucket
