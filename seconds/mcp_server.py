"""MCP server exposing the summarization tools to an AI agent.

Each tool is a thin wrapper over :mod:`seconds.queries`.  Docstrings and typed
arguments become the tool schema the model sees, so keep them descriptive.

Run it directly for stdio transport::

    python -m seconds.mcp_server

or, during development, with the MCP Inspector::

    mcp dev seconds/mcp_server.py
"""

from __future__ import annotations

from typing import Any

try:  # MCP Python SDK 1.x
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - SDK 2.x renamed the class
    from mcp.server.mcpserver import MCPServer as FastMCP

from . import queries
from .call_log import logged

mcp = FastMCP("SECONDS")


@mcp.tool()
@logged("mcp")
def list_schema() -> dict[str, Any]:
    """Describe the incidents table: columns, their type/role, example values,
    and the available aggregations and time buckets. Call this first to discover
    what can be queried."""
    return queries.list_schema()


@mcp.tool()
@logged("mcp")
def list_column_values(column: str) -> dict[str, Any]:
    """List the distinct values of a categorical column (e.g. 'region',
    'urgency', 'vehicle_id') so you can build valid filters."""
    return {"column": column, "values": queries.distinct_values(column)}


@mcp.tool()
@logged("mcp")
def summarize(
    metric: str,
    column: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    region: str | None = None,
    urgency: str | None = None,
    vehicle_id: str | None = None,
) -> dict[str, Any]:
    """Compute one aggregate (metric = avg | sum | min | max | count) over a
    numeric column, with optional filters. Dates are YYYY-MM-DD and both bounds
    are inclusive. 'count' ignores 'column'.

    Example — average A1 response time in September:
        summarize(metric="avg", column="response_time_seconds", urgency="A1",
                  date_from="2025-09-01", date_to="2025-09-30")
    """
    return queries.summarize(
        metric,
        column,
        date_from=date_from,
        date_to=date_to,
        region=region,
        urgency=urgency,
        vehicle_id=vehicle_id,
    )


@mcp.tool()
@logged("mcp")
def group_by(
    metric: str,
    group_by: str,
    column: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    region: str | None = None,
    urgency: str | None = None,
    vehicle_id: str | None = None,
) -> dict[str, Any]:
    """Compute an aggregate grouped by a dimension or time bucket. 'group_by'
    can be a categorical column (e.g. 'region', 'urgency') or a time bucket
    ('day', 'week', 'month').

    Example — average response time per region in 2025:
        group_by(metric="avg", group_by="region",
                 column="response_time_seconds",
                 date_from="2025-01-01", date_to="2025-12-31")
    """
    return queries.group_by(
        metric,
        group_by,
        column,
        date_from=date_from,
        date_to=date_to,
        region=region,
        urgency=urgency,
        vehicle_id=vehicle_id,
    )


@mcp.tool()
@logged("mcp")
def trend(
    metric: str,
    column: str | None = None,
    bucket: str = "month",
    moving_average_window: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    region: str | None = None,
    urgency: str | None = None,
    vehicle_id: str | None = None,
) -> dict[str, Any]:
    """Compute a time-ordered series (bucket = day | week | month) with an
    optional trailing moving average over the last 'moving_average_window'
    buckets.

    Example — monthly A1 response-time trend with a 3-month moving average:
        trend(metric="avg", column="response_time_seconds", bucket="month",
              moving_average_window=3, urgency="A1")
    """
    return queries.trend(
        metric,
        column,
        bucket=bucket,
        moving_average_window=moving_average_window,
        date_from=date_from,
        date_to=date_to,
        region=region,
        urgency=urgency,
        vehicle_id=vehicle_id,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
