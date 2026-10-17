"""Shared fixtures. DATABASE_URL points at a throwaway SQLite file before the app is imported."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="complaints-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP / 'api.db'}"

from complaints_ingest.store import complaints, get_engine, init_db  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def api_page() -> dict:
    return json.loads((FIXTURES / "cfpb_api_page.json").read_text())


@pytest.fixture
def csv_path() -> Path:
    return FIXTURES / "cfpb_sample.csv"


@pytest.fixture
def engine(tmp_path):
    eng = get_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(eng)
    return eng


def make_row(complaint_id: str, received: date, product: str = "Credit card",
             company: str = "Example Bank", issue: str | None = "Fees or interest",
             timely: bool | None = True) -> dict:
    """A storage-ready row, inserted directly so report tests do not depend on exercises."""
    return {"complaint_id": complaint_id, "date_received": received, "product": product,
            "company": company, "issue": issue, "timely": timely, "state": "NY",
            "ingested_at": datetime.now(UTC)}


def insert_rows(eng, rows: list[dict]) -> None:
    with eng.begin() as conn:
        conn.execute(complaints.insert(), rows)


@pytest.fixture
def seeded(engine):
    insert_rows(engine, [
        make_row("1", date(2026, 7, 3), "Credit card", "Alpha Bank", "Fees or interest", True),
        make_row("2", date(2026, 7, 9), "Credit card", "Alpha Bank", "Fees or interest", False),
        make_row("3", date(2026, 8, 1), "Mortgage", "Beacon", "Struggling to pay mortgage", True),
        make_row("4", date(2026, 8, 15), "Debt collection", "Alpha Bank", None, None),
        make_row("5", date(2026, 9, 2), "Credit card", "Cedar", "Getting a credit card", True),
    ])
    return engine
