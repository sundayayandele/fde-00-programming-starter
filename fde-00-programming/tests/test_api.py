from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app, engine
from tests.conftest import insert_rows, make_row

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _seed():
    insert_rows(engine(), [
        make_row("101", date(2026, 7, 1), "Credit card", "Alpha Bank"),
        make_row("102", date(2026, 8, 1), "Mortgage", "Beacon"),
        make_row("103", date(2026, 9, 1), "Credit card", "Beacon"),
    ])


def test_live():
    assert client.get("/health/live").json() == {"status": "ok"}


def test_ready_reports_database():
    body = client.get("/health/ready").json()
    assert body["status"] == "ready"
    assert body["database"] == "sqlite"


def test_ready_returns_503_when_db_down(monkeypatch):
    class Broken:
        def connect(self):
            raise ConnectionError("down")

    monkeypatch.setattr("app.main.engine", lambda: Broken())
    r = client.get("/health/ready")
    assert r.status_code == 503
    assert "ConnectionError" in r.json()["detail"]


def test_metrics_exposed():
    client.get("/health/live")
    r = client.get("/metrics/")
    assert r.status_code == 200
    assert "http_requests_total" in r.text


def test_data_gauges_exposed():
    text = client.get("/metrics/").text
    assert "complaints_stored 3.0" in text
    assert "complaints_last_ingest_timestamp_seconds 0.0" in text


def test_gauge_reports_minus_one_when_db_down(monkeypatch):
    from app import main

    class Broken:
        def connect(self):
            raise ConnectionError("down")

    monkeypatch.setattr(main, "engine", lambda: Broken())
    assert main._scalar(main.select(main.func.count())) == -1.0


def test_by_month():
    assert client.get("/api/v1/by-month").json() == [
        {"month": "2026-07", "complaints": 1},
        {"month": "2026-08", "complaints": 1},
        {"month": "2026-09", "complaints": 1},
    ]


def test_search_filters_and_orders():
    body = client.get("/api/v1/complaints", params={"product": "Credit card"}).json()
    assert body["count"] == 2
    assert [i["complaint_id"] for i in body["items"]] == ["103", "101"]
    body = client.get("/api/v1/complaints", params={"company": "Beacon",
                                                    "received_from": "2026-08-15"}).json()
    assert [i["complaint_id"] for i in body["items"]] == ["103"]
    body = client.get("/api/v1/complaints", params={"state": "NY", "received_to": "2026-07-31",
                                                    "limit": 1, "offset": 0}).json()
    assert body["count"] == 1 and body["limit"] == 1


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 501}, {"offset": -1},
                                    {"received_from": "yesterday"}])
def test_search_validation(params):
    assert client.get("/api/v1/complaints", params=params).status_code == 422


def test_runs_empty_list():
    assert client.get("/api/v1/runs").json() == []


@pytest.mark.exercise
def test_summary():
    body = client.get("/api/v1/summary").json()
    assert body["total_complaints"] == 3
    assert body["by_product"][0] == {"product": "Credit card", "complaints": 2}
