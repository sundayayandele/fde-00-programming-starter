import pytest

from complaints_ingest.cfpb import iter_csv, parse_page
from complaints_ingest.pipeline import ingest
from complaints_ingest.schema import API_FIELD_MAP, CSV_FIELD_MAP
from complaints_ingest.store import count_complaints, latest_runs
from complaints_ingest.synthetic import make_complaints

pytestmark = pytest.mark.exercise


def test_ingest_api_page(engine, api_page):
    result = ingest(engine, parse_page(api_page), API_FIELD_MAP, source="fixture")
    assert (result["fetched"], result["stored"], result["rejected"]) == (3, 2, 1)
    assert result["pii_masked"] == 2
    assert result["quality"]["schema_drift"]["unexpected_fields"] == []
    assert count_complaints(engine) == 2
    assert latest_runs(engine)[0]["run_id"] == result["run_id"]


def test_ingest_csv_is_idempotent(engine, csv_path):
    first = ingest(engine, iter_csv(csv_path), CSV_FIELD_MAP, source="cfpb-csv")
    second = ingest(engine, iter_csv(csv_path), CSV_FIELD_MAP, source="cfpb-csv")
    assert first["quality"]["duplicate_ids"] == 1
    assert count_complaints(engine) == 3        # 8800101 twice, 8800104 rejected
    assert second["stored"] == first["stored"]
    assert len(latest_runs(engine)) == 2


def test_ingest_synthetic_in_batches(engine):
    result = ingest(engine, make_complaints(250, seed=7), API_FIELD_MAP, source="synthetic",
                    batch_size=100)
    assert result["stored"] == 250
    assert result["records_per_minute"] > 0
    assert count_complaints(engine) == 250


def test_synthetic_is_reproducible():
    assert make_complaints(5, seed=1) == make_complaints(5, seed=1)
    assert make_complaints(5, seed=1) != make_complaints(5, seed=2)
