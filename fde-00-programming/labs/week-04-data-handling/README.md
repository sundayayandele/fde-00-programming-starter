# Week 04: Data handling: APIs, CSV, SQL and measured results

**Goal:** pull real complaints from the CFPB, store them idempotently in SQL, report on them, and publish numbers you measured.

## Brief

The pilot needs a daily feed (API) and a one-off backfill (bulk CSV), into Postgres, with a report the complaints team can trust. Your demo to the head of complaints is on Friday; it must show real numbers and how you got them.

## Concepts

HTTP, JSON, paging, retries and back-off, streaming CSV, SQL tables and primary keys, upserts (`INSERT ... ON CONFLICT`), `GROUP BY`, benchmarking with medians, honest reporting.

## Steps

1. `cfpb.py` → `parse_page(payload)`: return the `_source` dicts from `{"hits": {"hits": [...]}}`; tolerate a plain list, empty or malformed payloads. `pytest tests/test_cfpb.py -m exercise`.
2. `store.py` → `upsert_complaints(engine, records)`: build rows with `ingested_at`, de-duplicate within the batch (last one wins), and use the dialect's `insert(...).on_conflict_do_update(...)` keyed on `complaint_id`. Return rows written. `pytest tests/test_store.py tests/test_pipeline.py -m exercise`.
3. `report.py` → `counts_by_product(engine, limit)`: complaints per product, largest first, ties by name. `pytest tests/test_report.py -m exercise`.
4. Everything green: `make exercises`, then `make e2e` and `python scripts/smoke_test.py --include-exercises` against `make run`.
5. Pull real data: `complaints-ingest ingest-api --days 30 --limit 10000`, then `complaints-ingest report` and `complaints-ingest runs`. Run it twice: does the row count change? Why not?
6. Against Postgres: `make up-docker`, then `TEST_POSTGRES_URL=postgresql+psycopg://complaints:complaints-local@127.0.0.1:5432/complaints make test-postgres` (publish port 5432 from the `db` service first, or run the tests inside the network).
7. Measure: `make bench`. Fill the README results table with your numbers, the command, the data and the date (UTC). Add a row for your real CFPB pull: records fetched, duration, records per minute, rejections.

## Check

```bash
make exercises && make e2e && make bench
```

## Evidence

Your README results table, the run log of a real CFPB pull, and two sentences on the difference between synthetic throughput and real API throughput.

## Stretch

Ingest Banking77 or the Bitext support dataset (see [DATASETS](../../docs/datasets/DATASETS.md)) with the same pipeline: write a field map, decide which canonical fields stay empty, and report what the quality report shows.

## Phase 0 exit check

From a fresh clone: `make test`, `make exercises` and `make e2e` pass; the stack runs on one desktop engine with Postgres; a real CFPB pull is stored and reported; your results table holds numbers you measured.
