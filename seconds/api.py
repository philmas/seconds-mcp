"""FastAPI application exposing the summarization endpoints.

Routes are deliberately thin: they unpack the validated request and delegate to
:mod:`seconds.queries`.  Any ``ValueError`` raised by the query layer (unknown
column, non-numeric aggregation, bad date, ...) is turned into an HTTP 400.
"""

from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from seed.generate_data import generate

from . import call_log, queries, stats
from .models import (
    GroupByRequest,
    GroupByResponse,
    SummarizeRequest,
    SummarizeResponse,
    TrendRequest,
    TrendResponse,
)

app = FastAPI(
    title="SECONDS Data Summary API",
    version="0.1.0",
    description=(
        "Summarize ambulance-dispatch data: schema discovery, aggregations, "
        "group-by and time-series trends. Designed to be driven by an AI agent "
        "(see the companion MCP server)."
    ),
)

# Paths that are too noisy / uninteresting to record in the trace log.
_SKIP_LOG_PREFIXES = ("/health", "/docs", "/openapi", "/redoc", "/favicon")


@app.middleware("http")
async def _log_requests(request: Request, call_next):
    """Record every meaningful REST call in the shared trace log."""
    start = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    if not path.startswith(_SKIP_LOG_PREFIXES):
        call_log.record(
            source="api",
            name=f"{request.method} {path}",
            arguments=dict(request.query_params),
            status="ok" if response.status_code < 400 else "error",
            duration_ms=round((time.perf_counter() - start) * 1000, 2),
            result={"status_code": response.status_code},
        )
    return response


@app.exception_handler(ValueError)
async def _value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
    """Validation errors from the query layer become clean 400 responses."""
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/schema", tags=["discovery"])
def get_schema() -> dict:
    """List columns, their roles, example values and available operations."""
    return queries.list_schema()


@app.get("/stats", tags=["discovery"])
def get_stats() -> dict:
    """Headline statistics computed live from the incidents table."""
    return stats.database_stats()


@app.post("/reset", tags=["admin"])
def reset_database() -> dict:
    """Reinitialize the incidents database with the deterministic sample data.

    Destructive: drops and recreates the incidents table, restoring a known
    ground-truth dataset for validating agent / MCP answers.
    """
    rows = generate()
    return {"status": "reset", "rows": rows}


@app.get("/columns/{column}/values", tags=["discovery"])
def column_values(column: str) -> dict:
    """List the distinct values of a categorical column."""
    return {"column": column, "values": queries.distinct_values(column)}


@app.post("/summarize", response_model=SummarizeResponse, tags=["summarize"])
def summarize(req: SummarizeRequest) -> dict:
    return queries.summarize(
        req.metric.value, req.column, **req.filters.model_dump(exclude_none=True)
    )


@app.post("/group-by", response_model=GroupByResponse, tags=["summarize"])
def group_by(req: GroupByRequest) -> dict:
    return queries.group_by(
        req.metric.value,
        req.group_by,
        req.column,
        **req.filters.model_dump(exclude_none=True),
    )


@app.post("/trend", response_model=TrendResponse, tags=["summarize"])
def trend(req: TrendRequest) -> dict:
    return queries.trend(
        req.metric.value,
        req.column,
        bucket=req.bucket.value,
        moving_average_window=req.moving_average_window,
        **req.filters.model_dump(exclude_none=True),
    )
