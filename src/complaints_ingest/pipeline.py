"""Ingest pipeline: read -> clean -> upsert -> quality report -> run log.

Rows stream through in batches; nothing holds the whole source in memory, so the
same code handles a 50-row fixture and the multi-gigabyte CFPB bulk CSV.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterable
from datetime import UTC, datetime
from itertools import islice

from sqlalchemy import Engine

from complaints_ingest.clean import clean_rows
from complaints_ingest.quality import QualityTracker
from complaints_ingest.store import init_db, record_run, upsert_complaints


def _batches(rows: Iterable[dict], size: int) -> Iterable[list[dict]]:
    iterator = iter(rows)
    while batch := list(islice(iterator, size)):
        yield batch


def ingest(engine: Engine, rows: Iterable[dict], field_map: dict[str, str], *, source: str,
           batch_size: int = 1000) -> dict:
    """Ingest rows in batches and return a run summary with a data-quality report."""
    init_db(engine)
    started_at = datetime.now(UTC)
    t0 = time.perf_counter()
    tracker = QualityTracker(field_map)
    stored = 0
    for batch in _batches(rows, batch_size):
        result = clean_rows(batch, field_map)
        stored += upsert_complaints(engine, result.records)
        tracker.add(batch, result.records, result.rejected, result.pii_masked)
    duration = time.perf_counter() - t0

    report = tracker.report()
    summary = {
        "source": source,
        "fetched": report["rows_read"],
        "stored": stored,
        "rejected": report["rows_rejected"],
        "pii_masked": report["pii_values_masked"],
        "duration_seconds": round(duration, 3),
        "records_per_minute": round(report["rows_read"] / duration * 60) if duration > 0 else None,
        "quality": report,
    }
    summary["run_id"] = record_run(
        engine, source=source, started_at=started_at, finished_at=datetime.now(UTC),
        fetched=summary["fetched"], stored=stored, rejected=summary["rejected"],
        pii_masked=summary["pii_masked"], duration_seconds=duration,
        quality_json=json.dumps(report, default=str),
    )
    return summary
