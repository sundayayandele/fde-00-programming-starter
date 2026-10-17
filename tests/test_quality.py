from datetime import date

import pytest

from complaints_ingest.quality import (
    QualityTracker,
    build_report,
    null_counts,
    null_rates,
    schema_drift,
)
from complaints_ingest.schema import API_FIELD_MAP, CANONICAL_FIELDS, Complaint


def _c(cid: str, issue: str | None = None) -> Complaint:
    return Complaint(complaint_id=cid, date_received=date(2026, 9, int(cid)), product="P",
                     company="C", issue=issue)


@pytest.mark.exercise
def test_null_counts():
    counts = null_counts([_c("1", "x"), _c("2"), _c("3"), _c("4", "y")])
    assert set(counts) == set(CANONICAL_FIELDS)
    assert counts["issue"] == 2
    assert counts["product"] == 0
    assert counts["narrative"] == 4


@pytest.mark.exercise
def test_null_counts_empty():
    assert all(v == 0 for v in null_counts([]).values())


def test_null_rates():
    rates = null_rates({"issue": 1, "narrative": 3}, 3)
    assert rates["issue"] == 0.3333
    assert rates["narrative"] == 1.0
    assert rates["product"] == 0.0
    assert all(v == 0.0 for v in null_rates({"issue": 1}, 0).values())


def test_schema_drift_flags_renamed_field():
    drift = schema_drift({"complaint_id", "complaint_narrative_v2"},
                         {"complaint_id": "complaint_id", "complaint_what_happened": "n"})
    assert drift == {"unexpected_fields": ["complaint_narrative_v2"],
                     "missing_fields": ["complaint_what_happened"]}


def test_schema_drift_empty_run():
    assert schema_drift(set(), API_FIELD_MAP, rows_read=0) == {"unexpected_fields": [],
                                                                "missing_fields": []}


@pytest.mark.exercise
def test_build_report():
    records = [_c("1", "x"), _c("1"), _c("3")]
    rejected = [{"row": {}, "reason": "missing required fields: product"}] * 2
    report = build_report([{"complaint_id": "1"}] * 5, records, rejected, API_FIELD_MAP, 4)
    assert report["rows_read"] == 5
    assert report["rows_valid"] == 3
    assert report["rows_rejected"] == 2
    assert report["rejection_reasons"] == {"missing required fields: product": 2}
    assert report["duplicate_ids"] == 1
    assert report["pii_values_masked"] == 4
    assert report["date_received_min"] == "2026-09-01"
    assert report["date_received_max"] == "2026-09-03"
    assert report["null_rates"]["issue"] == 0.6667
    assert report["top_products"] == {"P": 3}


@pytest.mark.exercise
def test_tracker_merges_batches():
    tracker = QualityTracker(API_FIELD_MAP)
    tracker.add([{"complaint_id": "1"}], [_c("2", "x")], [], 0)
    tracker.add([{"complaint_id": "2"}], [_c("2"), _c("5")], [], 1)
    report = tracker.report()
    assert report["duplicate_ids"] == 1           # duplicates across batches are caught
    assert report["null_rates"]["issue"] == 0.6667
    assert (report["date_received_min"], report["date_received_max"]) == ("2026-09-02",
                                                                          "2026-09-05")
