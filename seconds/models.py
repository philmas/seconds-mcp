"""Pydantic request/response models for the REST API.

These give the API typed validation and a self-documenting OpenAPI schema at
``/docs``.  The core :mod:`seconds.queries` layer stays free of these models so
it can be reused without a web framework.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Metric(str, Enum):
    avg = "avg"
    sum = "sum"
    min = "min"
    max = "max"
    count = "count"


class Bucket(str, Enum):
    day = "day"
    week = "week"
    month = "month"


class Filters(BaseModel):
    """Optional filters applied before aggregation."""

    date_from: str | None = Field(
        None, description="Inclusive lower bound on the call timestamp (YYYY-MM-DD)."
    )
    date_to: str | None = Field(
        None, description="Inclusive upper bound on the call timestamp (YYYY-MM-DD)."
    )
    region: str | None = Field(None, description="Filter to a single region.")
    urgency: str | None = Field(None, description="Filter to an urgency class (A1/A2/B).")
    vehicle_id: str | None = Field(None, description="Filter to a single vehicle.")


class SummarizeRequest(BaseModel):
    metric: Metric
    column: str | None = Field(
        None, description="Numeric column to aggregate. Optional only for 'count'."
    )
    filters: Filters = Field(default_factory=Filters)

    model_config = {
        "json_schema_extra": {
            "example": {
                "metric": "avg",
                "column": "response_time_seconds",
                "filters": {"urgency": "A1", "date_from": "2025-09-01", "date_to": "2025-09-30"},
            }
        }
    }


class GroupByRequest(BaseModel):
    metric: Metric
    group_by: str = Field(
        ..., description="A categorical column (e.g. region) or a time bucket (day/week/month)."
    )
    column: str | None = Field(None, description="Numeric column to aggregate.")
    filters: Filters = Field(default_factory=Filters)


class TrendRequest(BaseModel):
    metric: Metric
    column: str | None = Field(None, description="Numeric column to aggregate.")
    bucket: Bucket = Bucket.month
    moving_average_window: int | None = Field(
        None, ge=2, description="Window (in buckets) for a trailing moving average."
    )
    filters: Filters = Field(default_factory=Filters)


# --- Response models ------------------------------------------------------- #
class SummarizeResponse(BaseModel):
    metric: str
    column: str | None
    value: float | None
    count: int


class GroupResult(BaseModel):
    group: str | None
    value: float | None
    count: int


class GroupByResponse(BaseModel):
    metric: str
    column: str | None
    group_by: str
    results: list[GroupResult]


class TrendPoint(BaseModel):
    period: str
    value: float | None
    count: int
    moving_average: float | None = None


class TrendResponse(BaseModel):
    metric: str
    column: str | None
    bucket: str
    points: list[TrendPoint]
