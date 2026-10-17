#!/usr/bin/env python3
"""Repeatable ingest throughput benchmark on seeded synthetic data.

Synthetic data measures the pipeline (clean, mask, upsert), not the CFPB API. Real-data
throughput is network-bound; measure it with `complaints-ingest ingest-api` on your machine.

    python scripts/benchmark.py --count 50000 --repeats 3
    python scripts/benchmark.py --database-url postgresql+psycopg://...  --count 50000
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from complaints_ingest import __version__
from complaints_ingest.pipeline import ingest
from complaints_ingest.schema import API_FIELD_MAP
from complaints_ingest.store import get_engine, metadata
from complaints_ingest.synthetic import make_complaints

ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database-url", help="default: a fresh SQLite file per run")
    parser.add_argument("--count", type=int, default=50_000)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--out", type=Path, default=ROOT / "evals" / "results")
    args = parser.parse_args(argv)

    rows = make_complaints(args.count, seed=42)
    cold, warm = [], []
    for i in range(args.repeats):
        with tempfile.TemporaryDirectory() as tmp:
            url = args.database_url or f"sqlite:///{tmp}/bench.db"
            engine = get_engine(url)
            metadata.drop_all(engine)
            first = ingest(engine, rows, API_FIELD_MAP, source="bench", batch_size=args.batch_size)
            again = ingest(engine, rows, API_FIELD_MAP, source="bench", batch_size=args.batch_size)
            metadata.drop_all(engine)
            engine.dispose()
        cold.append(first["records_per_minute"])
        warm.append(again["records_per_minute"])
        print(f"run {i + 1}: insert {first['records_per_minute']:,}/min, "
              f"re-ingest (upsert) {again['records_per_minute']:,}/min, "
              f"PII masked {first['pii_masked']:,}")

    dialect = (args.database_url or "sqlite").split(":")[0].split("+")[0]
    result = {
        "date": datetime.now(UTC).date().isoformat(),
        "version": __version__,
        "dataset": f"synthetic seed=42 n={args.count}",
        "database": dialect,
        "batch_size": args.batch_size,
        "repeats": args.repeats,
        "insert_records_per_minute_median": statistics.median(cold),
        "upsert_records_per_minute_median": statistics.median(warm),
        "python": platform.python_version(),
        "machine": f"{platform.system()} {platform.machine()}, {_cpus()} CPUs",
    }
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / f"benchmark-{dialect}-{result['date']}.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print(f"written {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    return 0


def _cpus() -> int:
    import os
    return os.cpu_count() or 1


if __name__ == "__main__":
    sys.exit(main())
