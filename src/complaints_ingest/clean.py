"""Turn raw source rows into validated Complaint records.

Weeks 1 and 2 exercises live here: text normalisation, type parsing, PII masking
and the mapping from a raw row to a Complaint.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

from pydantic import ValidationError

from complaints_ingest.schema import REQUIRED_FIELDS, Complaint

_WHITESPACE = re.compile(r"\s+")

# Defence in depth: CFPB already redacts narratives (XXXX), but a pipeline that may
# later receive a bank's own complaint data must not rely on the source doing it.
_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("[EMAIL]", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("[SSN]", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("[CARD]", re.compile(r"\b\d(?:[ -]?\d){12,18}\b")),
    ("[PHONE]", re.compile(r"(?:\+?1[ .-]?)?\(?\b\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b")),
    ("[ACCOUNT]", re.compile(r"\b\d{8,12}\b")),
)


def normalise_text(value: object) -> str | None:
    """Collapse whitespace and turn empty or placeholder values into None.

    >>> normalise_text("  Credit   card ")
    'Credit card'
    >>> normalise_text("") is None and normalise_text("None") is None
    True
    """
    raise NotImplementedError("TODO week-01 normalise text: see labs/")


def parse_bool(value: object) -> bool | None:
    """Parse CFPB yes/no style values. Unknown values become None, never a guess."""
    raise NotImplementedError("TODO week-01 parse booleans: see labs/")


def parse_date(value: object) -> date | None:
    """Parse ISO dates, ISO timestamps (API) and MM/DD/YY or MM/DD/YYYY dates (CSV)."""
    raise NotImplementedError("TODO week-01 parse dates: see labs/")


def mask_pii(text: str | None) -> tuple[str | None, int]:
    """Replace emails, SSNs, card, phone and account numbers. Returns (text, count)."""
    raise NotImplementedError("TODO week-02 mask PII: see labs/")


@dataclass
class CleanResult:
    """Outcome of cleaning one batch."""

    records: list[Complaint] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    pii_masked: int = 0


def to_complaint(row: dict, field_map: dict[str, str]) -> tuple[Complaint | None, str | None, int]:
    """Map one raw row to a Complaint. Returns (record, rejection_reason, pii_masked)."""
    raise NotImplementedError("TODO week-02 map a raw row to a Complaint: see labs/")


def clean_rows(rows: list[dict], field_map: dict[str, str]) -> CleanResult:
    """Clean a batch; keep rejected rows with a reason so the quality report can explain them."""
    result = CleanResult()
    for row in rows:
        record, reason, masked = to_complaint(row, field_map)
        if record is None:
            result.rejected.append({"row": row, "reason": reason})
        else:
            result.records.append(record)
            result.pii_masked += masked
    return result
