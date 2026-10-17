"""Storage: SQLite locally, Postgres in Compose, Kubernetes and the clouds.

One SQLAlchemy Core schema, one upsert that works on both databases.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Engine,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from complaints_ingest.schema import Complaint

metadata = MetaData()

complaints = Table(
    "complaints",
    metadata,
    Column("complaint_id", String(32), primary_key=True),
    Column("date_received", Date, nullable=False, index=True),
    Column("date_sent_to_company", Date),
    Column("product", String(200), nullable=False, index=True),
    Column("sub_product", String(200)),
    Column("issue", String(300), index=True),
    Column("sub_issue", String(300)),
    Column("narrative", Text),
    Column("company_public_response", Text),
    Column("company", String(300), nullable=False, index=True),
    Column("state", String(8)),
    Column("zip_code", String(10)),
    Column("tags", String(200)),
    Column("consumer_consent_provided", String(100)),
    Column("submitted_via", String(50)),
    Column("company_response", String(200)),
    Column("timely", Boolean),
    Column("consumer_disputed", Boolean),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
)

ingest_runs = Table(
    "ingest_runs",
    metadata,
    Column("run_id", Integer, primary_key=True, autoincrement=True),
    Column("source", String(50), nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("finished_at", DateTime(timezone=True)),
    Column("fetched", Integer, default=0),
    Column("stored", Integer, default=0),
    Column("rejected", Integer, default=0),
    Column("pii_masked", Integer, default=0),
    Column("duration_seconds", Float),
    Column("quality_json", Text),
)


def get_engine(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True, future=True)


def init_db(engine: Engine) -> None:
    metadata.create_all(engine)


def upsert_complaints(engine: Engine, records: list[Complaint]) -> int:
    """Insert new complaints and update existing ones (same complaint_id). Returns rows written."""
    if not records:
        return 0
    raise NotImplementedError("TODO week-04 upsert into SQL: see labs/")


def count_complaints(engine: Engine) -> int:
    with engine.connect() as conn:
        return conn.execute(select(func.count()).select_from(complaints)).scalar_one()


def record_run(engine: Engine, **values: object) -> int:
    with engine.begin() as conn:
        result = conn.execute(ingest_runs.insert().values(**values))
        return int(result.inserted_primary_key[0])


def latest_runs(engine: Engine, limit: int = 10) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(select(ingest_runs).order_by(ingest_runs.c.run_id.desc()).limit(limit))
        return [dict(r._mapping) for r in rows]
