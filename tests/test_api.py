"""API tests via FastAPI's TestClient against known sample data."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from seconds.api import app


@pytest.fixture()
def client(sample_db) -> TestClient:
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_schema_lists_columns(client):
    resp = client.get("/schema")
    assert resp.status_code == 200
    body = resp.json()
    names = {c["name"] for c in body["columns"]}
    assert "response_time_seconds" in names
    assert "avg" in body["aggregations"]


def test_column_values(client):
    resp = client.get("/columns/urgency/values")
    assert resp.status_code == 200
    assert resp.json()["values"] == ["A1", "A2"]


def test_summarize_avg_a1_september(client):
    resp = client.post(
        "/summarize",
        json={
            "metric": "avg",
            "column": "response_time_seconds",
            "filters": {"urgency": "A1", "date_from": "2025-09-01", "date_to": "2025-09-30"},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == 625.0


def test_group_by_region(client):
    resp = client.post(
        "/group-by",
        json={"metric": "avg", "group_by": "region", "column": "response_time_seconds"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["results"]) >= 1


def test_trend(client):
    resp = client.post(
        "/trend",
        json={"metric": "avg", "column": "response_time_seconds", "bucket": "month"},
    )
    assert resp.status_code == 200
    assert [p["period"] for p in resp.json()["points"]] == ["2025-09", "2025-10"]


def test_bad_column_returns_400(client):
    resp = client.post("/summarize", json={"metric": "avg", "column": "region"})
    assert resp.status_code == 400
    assert "not numeric" in resp.json()["detail"]


def test_unknown_metric_returns_422(client):
    # 'median' is rejected by Pydantic enum validation before reaching the query.
    resp = client.post("/summarize", json={"metric": "median", "column": "response_time_seconds"})
    assert resp.status_code == 422
