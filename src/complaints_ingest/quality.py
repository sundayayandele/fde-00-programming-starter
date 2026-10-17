"""Data-quality report for an ingest run: nulls, duplicates, rejections, schema drift.

`QualityTracker` keeps only counters, so a multi-gigabyte bulk CSV can be profiled in
constant memory while it streams through the pipeline batch by batch.
"""

from __future__ import annotations

from collections import Counter
from datetime import date

from complaints_ingest.schema import CANONICAL_FIELDS, Complaint


def null_counts(records: list[Complaint]) -> dict[str, int]:
    """Number of records with a missing value, per canonical field."""
    raise NotImplementedError("TODO week-03 count missing values: see labs/")


def null_rates(counts: dict[str, int], total: int) -> dict[str, float]:
    """Turn null counts into shares (0.0 to 1.0, 4 decimals)."""
    return {f: round(counts.get(f, 0) / total, 4) if total else 0.0 for f in CANONICAL_FIELDS}


def schema_drift(seen_fields: set[str], field_map: dict[str, str],
                 rows_read: int = 1) -> dict[str, list[str]]:
    """Compare the source's keys with the expected mapping."""
    expected = set(field_map)
    return {
        "unexpected_fields": sorted(seen_fields - expected),
        "missing_fields": sorted(expected - seen_fields) if rows_read else [],
    }


class QualityTracker:
    """Accumulate quality counters batch by batch; `report()` renders the summary."""

    def __init__(self, field_map: dict[str, str]) -> None:
        self.field_map = field_map
        self.rows_read = 0
        self.rows_valid = 0
        self.pii_masked = 0
        self.seen_fields: set[str] = set()
        self.nulls: Counter[str] = Counter()
        self.reasons: Counter[str] = Counter()
        self.products: Counter[str] = Counter()
        self.ids: Counter[str] = Counter()
        self.date_min: date | None = None
        self.date_max: date | None = None

    def add(self, raw_rows: list[dict], records: list[Complaint], rejected: list[dict],
            pii_masked: int) -> None:
        self.rows_read += len(raw_rows)
        self.rows_valid += len(records)
        self.pii_masked += pii_masked
        for row in raw_rows:
            self.seen_fields.update(row.keys())
        self.nulls.update(null_counts(records))
        self.reasons.update(item["reason"] for item in rejected)
        self.products.update(r.product for r in records)
        self.ids.update(r.complaint_id for r in records)
        for r in records:
            if self.date_min is None or r.date_received < self.date_min:
                self.date_min = r.date_received
            if self.date_max is None or r.date_received > self.date_max:
                self.date_max = r.date_received

    def report(self) -> dict:
        return {
            "rows_read": self.rows_read,
            "rows_valid": self.rows_valid,
            "rows_rejected": sum(self.reasons.values()),
            "rejection_reasons": dict(self.reasons.most_common()),
            "duplicate_ids": sum(n - 1 for n in self.ids.values() if n > 1),
            "pii_values_masked": self.pii_masked,
            "date_received_min": self.date_min.isoformat() if self.date_min else None,
            "date_received_max": self.date_max.isoformat() if self.date_max else None,
            "null_rates": null_rates(dict(self.nulls), self.rows_valid),
            "schema_drift": schema_drift(self.seen_fields, self.field_map, self.rows_read),
            "top_products": dict(self.products.most_common(5)),
        }


def build_report(raw_rows: list[dict], records: list[Complaint], rejected: list[dict],
                 field_map: dict[str, str], pii_masked: int) -> dict:
    """One-shot report for a single in-memory batch."""
    tracker = QualityTracker(field_map)
    tracker.add(raw_rows, records, rejected, pii_masked)
    return tracker.report()
