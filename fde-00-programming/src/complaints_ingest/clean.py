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
    # >>> SOLUTION: week-01 normalise text
    if value is None:
        return None
    text = _WHITESPACE.sub(" ", str(value)).strip()
    if text == "" or text.lower() in {"none", "null", "n/a", "nan"}:
        return None
    return text
    # <<< SOLUTION


def parse_bool(value: object) -> bool | None:
    """Parse CFPB yes/no style values. Unknown values become None, never a guess."""
    # >>> SOLUTION: week-01 parse booleans
    if isinstance(value, bool):
        return value
    text = normalise_text(value)
    if text is None:
        return None
    lowered = text.lower()
    if lowered in {"yes", "y", "true", "1"}:
        return True
    if lowered in {"no", "n", "false", "0"}:
        return False
    return None
    # <<< SOLUTION


def parse_date(value: object) -> date | None:
    """Parse ISO dates, ISO timestamps (API) and MM/DD/YY or MM/DD/YYYY dates (CSV)."""
    # >>> SOLUTION: week-01 parse dates
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = normalise_text(value)
    if text is None:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for fmt in ("%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None
    # <<< SOLUTION


def mask_pii(text: str | None) -> tuple[str | None, int]:
    """Replace emails, SSNs, card, phone and account numbers. Returns (text, count)."""
    # >>> SOLUTION: week-02 mask PII
    if text is None:
        return None, 0
    total = 0
    for placeholder, pattern in _PII_PATTERNS:
        text, n = pattern.subn(placeholder, text)
        total += n
    return text, total
    # <<< SOLUTION


@dataclass
class CleanResult:
    """Outcome of cleaning one batch."""

    records: list[Complaint] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    pii_masked: int = 0


def to_complaint(row: dict, field_map: dict[str, str]) -> tuple[Complaint | None, str | None, int]:
    """Map one raw row to a Complaint. Returns (record, rejection_reason, pii_masked)."""
    # >>> SOLUTION: week-02 map a raw row to a Complaint
    canonical: dict[str, object] = {}
    for source_key, target in field_map.items():
        if source_key in row:
            canonical[target] = row[source_key]

    data: dict[str, object] = {}
    for key, value in canonical.items():
        if key in {"date_received", "date_sent_to_company"}:
            data[key] = parse_date(value)
        elif key in {"timely", "consumer_disputed"}:
            data[key] = parse_bool(value)
        elif key == "tags" and isinstance(value, list):
            data[key] = normalise_text(", ".join(str(v) for v in value))
        else:
            data[key] = normalise_text(value)

    missing = [f for f in REQUIRED_FIELDS if data.get(f) is None]
    if missing:
        return None, f"missing required fields: {', '.join(missing)}", 0

    narrative, masked = mask_pii(data.get("narrative"))  # type: ignore[arg-type]
    data["narrative"] = narrative
    try:
        return Complaint(**data), None, masked
    except ValidationError as e:
        first = e.errors()[0]
        return None, f"invalid {first['loc'][0]}: {first['msg']}", 0
    # <<< SOLUTION


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
