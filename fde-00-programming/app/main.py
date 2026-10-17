"""Report API for ingested complaints: health, metrics, summary, search, runs."""

from __future__ import annotations

import time
from datetime import date
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query, Request
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app
from sqlalchemy import Engine, func, select, text

from complaints_ingest import __version__
from complaints_ingest.config import get_settings
from complaints_ingest.report import counts_by_month, summary
from complaints_ingest.store import complaints, get_engine, ingest_runs, init_db, latest_runs

settings = get_settings()
app = FastAPI(title="Complaints report API", version=__version__,
              description="Read-only API over CFPB complaints ingested by complaints-ingest.")
app.mount("/metrics", make_asgi_app())

REQUESTS = Counter("http_requests_total", "HTTP requests handled", ["method", "route", "status"])
LATENCY = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "route"])
STORED = Gauge("complaints_stored", "Complaints currently stored")
LAST_INGEST = Gauge("complaints_last_ingest_timestamp_seconds",
                    "Unix time the most recent ingest run finished (0 if none)")


@lru_cache
def engine() -> Engine:
    eng = get_engine(settings.database_url)
    init_db(eng)
    return eng


def _scalar(stmt) -> float:
    """Read one number for a gauge at scrape time; a database outage reads as -1."""
    try:
        with engine().connect() as conn:
            value = conn.execute(stmt).scalar()
    except Exception:  # noqa: BLE001 - a scrape must never fail because the DB is down
        return -1.0
    if value is None:
        return 0.0
    return value.timestamp() if hasattr(value, "timestamp") else float(value)


STORED.set_function(lambda: _scalar(select(func.count()).select_from(complaints)))
LAST_INGEST.set_function(lambda: _scalar(select(func.max(ingest_runs.c.finished_at))))


@app.middleware("http")
async def observe(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    route = getattr(request.scope.get("route"), "path", "unmatched")
    REQUESTS.labels(request.method, route, str(response.status_code)).inc()
    LATENCY.labels(request.method, route).observe(time.perf_counter() - started)
    return response


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    try:
        with engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:  # noqa: BLE001 - readiness must report any database failure
        detail = f"database unavailable: {type(e).__name__}"
        raise HTTPException(status_code=503, detail=detail) from None
    return {"status": "ready", "version": __version__, "environment": settings.environment,
            "database": engine().dialect.name}


@app.get("/api/v1/summary")
def get_summary() -> dict:
    return summary(engine())


@app.get("/api/v1/by-month")
def get_by_month() -> list[dict]:
    return counts_by_month(engine())


@app.get("/api/v1/complaints")
def search(
    product: str | None = None,
    company: str | None = None,
    state: str | None = Query(default=None, max_length=8),
    received_from: date | None = None,
    received_to: date | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    stmt = select(complaints).order_by(complaints.c.date_received.desc(),
                                       complaints.c.complaint_id)
    if product:
        stmt = stmt.where(complaints.c.product == product)
    if company:
        stmt = stmt.where(complaints.c.company == company)
    if state:
        stmt = stmt.where(complaints.c.state == state)
    if received_from:
        stmt = stmt.where(complaints.c.date_received >= received_from)
    if received_to:
        stmt = stmt.where(complaints.c.date_received <= received_to)
    with engine().connect() as conn:
        rows = [dict(r._mapping) for r in conn.execute(stmt.limit(limit).offset(offset))]
    return {"count": len(rows), "limit": limit, "offset": offset, "items": rows}


@app.get("/api/v1/runs")
def runs(limit: int = Query(default=10, ge=1, le=100)) -> list[dict]:
    return latest_runs(engine(), limit=limit)
