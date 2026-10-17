"""Command-line interface: `complaints-ingest <command>`.

    complaints-ingest init-db
    complaints-ingest ingest-api --days 30 --limit 5000
    complaints-ingest ingest-csv complaints.csv
    complaints-ingest ingest-synthetic --count 10000
    complaints-ingest report [--json]
    complaints-ingest runs
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from complaints_ingest.cfpb import CFPBClient, iter_csv
from complaints_ingest.config import get_settings
from complaints_ingest.pipeline import ingest
from complaints_ingest.report import summary
from complaints_ingest.schema import API_FIELD_MAP, CSV_FIELD_MAP
from complaints_ingest.store import get_engine, init_db, latest_runs
from complaints_ingest.synthetic import make_complaints


def _engine(url: str | None):
    url = url or get_settings().database_url
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    return get_engine(url)


def _print_ingest(result: dict) -> None:
    q = result["quality"]
    print(f"run {result['run_id']} [{result['source']}]: fetched {result['fetched']}, "
          f"stored {result['stored']}, rejected {result['rejected']}, "
          f"PII masked {result['pii_masked']}, {result['duration_seconds']}s "
          f"({result['records_per_minute']} records/min)")
    print(f"  dates {q['date_received_min']} to {q['date_received_max']}; "
          f"duplicate ids {q['duplicate_ids']}; "
          f"schema drift {q['schema_drift']}")
    if q["rejection_reasons"]:
        print(f"  rejection reasons: {q['rejection_reasons']}")


def _print_report(data: dict) -> None:
    print(f"Complaints: {data['total_complaints']:,} "
          f"({data['date_received_min']} to {data['date_received_max']})")
    if data["timely_response_rate"] is not None:
        print(f"Timely response rate: {data['timely_response_rate']:.1%}")
    print("\nBy product:")
    for row in data["by_product"]:
        print(f"  {row['complaints']:>8,}  {row['product']}")
    print("\nTop issues:")
    for row in data["top_issues"]:
        print(f"  {row['complaints']:>8,}  {row['issue']}")
    print("\nTop companies:")
    for row in data["top_companies"]:
        print(f"  {row['complaints']:>8,}  {row['company']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="complaints-ingest", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database-url", help="override DATABASE_URL")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="create tables")

    api = sub.add_parser("ingest-api", help="pull complaints from the CFPB API")
    api.add_argument("--days", type=int, default=7, help="look back this many days")
    api.add_argument("--since", type=date.fromisoformat, help="YYYY-MM-DD (overrides --days)")
    api.add_argument("--until", type=date.fromisoformat)
    api.add_argument("--product")
    api.add_argument("--limit", type=int, default=5000)

    csv_cmd = sub.add_parser("ingest-csv", help="load a CFPB bulk CSV (or a sample of it)")
    csv_cmd.add_argument("path", type=Path)

    syn = sub.add_parser("ingest-synthetic", help="load seeded synthetic complaints (offline)")
    syn.add_argument("--count", type=int, default=5000)
    syn.add_argument("--seed", type=int, default=42)

    rep = sub.add_parser("report", help="print the summary report")
    rep.add_argument("--json", action="store_true")

    sub.add_parser("runs", help="show recent ingest runs")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = _engine(args.database_url)

    if args.command == "init-db":
        init_db(engine)
        print("tables ready")
    elif args.command == "ingest-api":
        settings = get_settings()
        since = args.since or (date.today() - timedelta(days=args.days))
        client = CFPBClient(settings.cfpb_api_url, page_size=settings.cfpb_page_size)
        try:
            rows = client.iter_complaints(since=since, until=args.until, product=args.product,
                                          limit=args.limit)
            _print_ingest(ingest(engine, rows, API_FIELD_MAP, source="cfpb-api"))
        finally:
            client.close()
    elif args.command == "ingest-csv":
        _print_ingest(ingest(engine, iter_csv(args.path), CSV_FIELD_MAP, source="cfpb-csv"))
    elif args.command == "ingest-synthetic":
        rows = make_complaints(args.count, seed=args.seed)
        _print_ingest(ingest(engine, rows, API_FIELD_MAP, source="synthetic"))
    elif args.command == "report":
        init_db(engine)
        data = summary(engine)
        print(json.dumps(data, indent=2)) if args.json else _print_report(data)
    elif args.command == "runs":
        init_db(engine)
        for run in latest_runs(engine):
            print(f"{run['run_id']:>4}  {run['started_at']:%Y-%m-%d %H:%M}  {run['source']:<10} "
                  f"fetched {run['fetched']:>7}  stored {run['stored']:>7}  "
                  f"rejected {run['rejected']:>5}  {run['duration_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
