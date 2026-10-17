from datetime import date

import pytest

from complaints_ingest.clean import (
    clean_rows,
    mask_pii,
    normalise_text,
    parse_bool,
    parse_date,
    to_complaint,
)
from complaints_ingest.schema import API_FIELD_MAP, CSV_FIELD_MAP

pytestmark = pytest.mark.exercise


@pytest.mark.parametrize(("raw", "expected"), [
    ("  Credit   card ", "Credit card"),
    ("line\nbreak\ttab", "line break tab"),
    ("", None), ("   ", None), (None, None), ("None", None), ("N/A", None), ("nan", None),
    (42, "42"),
])
def test_normalise_text(raw, expected):
    assert normalise_text(raw) == expected


@pytest.mark.parametrize(("raw", "expected"), [
    ("Yes", True), ("yes", True), ("Y", True), (True, True),
    ("No", False), ("n", False), (False, False),
    ("N/A", None), ("", None), (None, None), ("maybe", None),
])
def test_parse_bool(raw, expected):
    assert parse_bool(raw) is expected


@pytest.mark.parametrize(("raw", "expected"), [
    ("2026-09-02", date(2026, 9, 2)),
    ("2026-09-02T12:00:00-05:00", date(2026, 9, 2)),
    ("2026-09-02T12:00:00Z", date(2026, 9, 2)),
    ("09/05/26", date(2026, 9, 5)),
    ("09/05/2026", date(2026, 9, 5)),
    (date(2026, 1, 1), date(2026, 1, 1)),
    ("not a date", None), ("", None), (None, None),
])
def test_parse_date(raw, expected):
    assert parse_date(raw) == expected


@pytest.mark.parametrize(("raw", "masked", "count"), [
    ("mail me at a.b+c@example.co.uk now", "mail me at [EMAIL] now", 1),
    ("SSN 123-45-6789", "SSN [SSN]", 1),
    ("card 4111 1111 1111 1111 used", "card [CARD] used", 1),
    ("call 555-201-3344 or (555) 201-3344", "call [PHONE] or [PHONE]", 2),
    ("account 123456789012", "account [ACCOUNT]", 1),
    ("I paid {$200.00} on XX/XX/2026", "I paid {$200.00} on XX/XX/2026", 0),
])
def test_mask_pii(raw, masked, count):
    assert mask_pii(raw) == (masked, count)


def test_mask_pii_none():
    assert mask_pii(None) == (None, 0)


def test_to_complaint_api_row(api_page):
    row = api_page["hits"]["hits"][0]["_source"]
    record, reason, masked = to_complaint(row, API_FIELD_MAP)
    assert reason is None
    assert record.complaint_id == "8800001"
    assert record.date_received == date(2026, 9, 2)
    assert record.timely is True
    assert record.consumer_disputed is None
    assert masked == 2
    assert "[PHONE]" in record.narrative and "[EMAIL]" in record.narrative
    assert "  " not in record.narrative


def test_to_complaint_rejects_bad_date(api_page):
    row = api_page["hits"]["hits"][2]["_source"]
    record, reason, _ = to_complaint(row, API_FIELD_MAP)
    assert record is None
    assert "date_received" in reason


def test_to_complaint_rejects_overlong_state():
    row = {"complaint_id": "1", "date_received": "2026-01-01", "product": "P", "company": "C",
           "state": "X" * 20}
    record, reason, _ = to_complaint(row, API_FIELD_MAP)
    assert record is None
    assert reason.startswith("invalid state")


def test_to_complaint_joins_list_tags():
    row = {"complaint_id": "1", "date_received": "2026-01-01", "product": "P", "company": "C",
           "tags": ["Older American", "Servicemember"]}
    record, _, _ = to_complaint(row, API_FIELD_MAP)
    assert record.tags == "Older American, Servicemember"


def test_clean_rows_csv(csv_path):
    import csv
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    result = clean_rows(rows, CSV_FIELD_MAP)
    assert len(result.records) == 4          # one row lacks a product
    assert len(result.rejected) == 1
    assert "product" in result.rejected[0]["reason"]
    assert result.pii_masked == 1            # the account number
    assert {r.date_received for r in result.records} >= {date(2026, 9, 5), date(2026, 9, 6)}
