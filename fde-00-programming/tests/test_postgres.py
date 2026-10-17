"""The same storage and report paths against a real Postgres.

Skipped unless TEST_POSTGRES_URL is set, e.g.
    TEST_POSTGRES_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/complaints
CI sets it with a postgres:16 service container (.github/workflows/ci.yml).
"""

import os
from datetime import date

import pytest

from complaints_ingest.pipeline import ingest
from complaints_ingest.report import counts_by_month, summary, timely_response_rate
from complaints_ingest.schema import API_FIELD_MAP
from complaints_ingest.store import count_complaints, get_engine, init_db, metadata
from complaints_ingest.synthetic import make_complaints
from tests.conftest import insert_rows, make_row

URL = os.environ.get("TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_POSTGRES_URL not set")


@pytest.fixture
def pg():
    eng = get_engine(URL)
    metadata.drop_all(eng)
    init_db(eng)
    yield eng
    metadata.drop_all(eng)
    eng.dispose()


def test_month_and_timely_on_postgres(pg):
    insert_rows(pg, [make_row("1", date(2026, 7, 3)),
                     make_row("2", date(2026, 8, 3), timely=False)])
    assert counts_by_month(pg) == [{"month": "2026-07", "complaints": 1},
                                   {"month": "2026-08", "complaints": 1}]
    assert timely_response_rate(pg) == 0.5


@pytest.mark.exercise
def test_ingest_is_idempotent_on_postgres(pg):
    rows = make_complaints(1200, seed=3)
    first = ingest(pg, rows, API_FIELD_MAP, source="synthetic", batch_size=500)
    ingest(pg, rows, API_FIELD_MAP, source="synthetic", batch_size=500)
    assert first["stored"] == 1200
    assert count_complaints(pg) == 1200
    assert summary(pg)["total_complaints"] == 1200
