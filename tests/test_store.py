from datetime import UTC, date, datetime

import pytest

from complaints_ingest.schema import Complaint
from complaints_ingest.store import (
    count_complaints,
    latest_runs,
    record_run,
    upsert_complaints,
)


def _c(cid: str, product: str = "Credit card") -> Complaint:
    return Complaint(complaint_id=cid, date_received=date(2026, 9, 1), product=product,
                     company="Example Bank")


def test_empty_db_counts_zero(engine):
    assert count_complaints(engine) == 0
    assert upsert_complaints(engine, []) == 0


@pytest.mark.exercise
def test_upsert_inserts_then_updates(engine):
    assert upsert_complaints(engine, [_c("1"), _c("2")]) == 2
    assert upsert_complaints(engine, [_c("2", "Mortgage"), _c("3")]) == 2
    assert count_complaints(engine) == 3
    with engine.connect() as conn:
        product = conn.exec_driver_sql(
            "SELECT product FROM complaints WHERE complaint_id = '2'").scalar_one()
    assert product == "Mortgage"


@pytest.mark.exercise
def test_upsert_dedupes_within_batch(engine):
    assert upsert_complaints(engine, [_c("1"), _c("1", "Mortgage")]) == 1
    assert count_complaints(engine) == 1


def test_record_and_list_runs(engine):
    now = datetime.now(UTC)
    first = record_run(engine, source="synthetic", started_at=now, finished_at=now, fetched=10,
                       stored=9, rejected=1, pii_masked=0, duration_seconds=0.1,
                       quality_json="{}")
    second = record_run(engine, source="cfpb-csv", started_at=now, fetched=5)
    runs = latest_runs(engine, limit=5)
    assert [r["run_id"] for r in runs] == [second, first]
    assert runs[1]["stored"] == 9
