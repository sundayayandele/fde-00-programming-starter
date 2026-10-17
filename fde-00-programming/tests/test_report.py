import pytest

from complaints_ingest.report import (
    counts_by_month,
    counts_by_product,
    summary,
    timely_response_rate,
    top_companies,
    top_issues,
)


def test_counts_by_month(seeded):
    assert counts_by_month(seeded) == [
        {"month": "2026-07", "complaints": 2},
        {"month": "2026-08", "complaints": 2},
        {"month": "2026-09", "complaints": 1},
    ]


def test_top_issues_skips_nulls(seeded):
    issues = top_issues(seeded)
    assert issues[0] == {"issue": "Fees or interest", "complaints": 2}
    assert all(i["issue"] is not None for i in issues)


def test_top_companies(seeded):
    assert top_companies(seeded, limit=1) == [{"company": "Alpha Bank", "complaints": 3}]


def test_timely_rate_ignores_unknown(seeded):
    assert timely_response_rate(seeded) == 0.75


def test_timely_rate_empty(engine):
    assert timely_response_rate(engine) is None


@pytest.mark.exercise
def test_counts_by_product(seeded):
    assert counts_by_product(seeded) == [
        {"product": "Credit card", "complaints": 3},
        {"product": "Debt collection", "complaints": 1},
        {"product": "Mortgage", "complaints": 1},
    ]


@pytest.mark.exercise
def test_summary(seeded):
    data = summary(seeded)
    assert data["total_complaints"] == 5
    assert data["date_received_min"] == "2026-07-03"
    assert data["date_received_max"] == "2026-09-02"
    assert data["by_product"][0]["product"] == "Credit card"


@pytest.mark.exercise
def test_summary_empty(engine):
    data = summary(engine)
    assert data["total_complaints"] == 0
    assert data["date_received_min"] is None
    assert data["by_product"] == []
