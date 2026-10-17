# ADR-005: CFPB search API for daily deltas, bulk CSV for backfill

- **Status:** Accepted
- **Date:** 2026-10-12
- **Deciders:** Sunday Ayandele (owner)

## Context

The CFPB publishes the same complaints as a search API (JSON, snake_case fields, paged) and as a bulk CSV of the full history (title-case headers, several GB unzipped). Simple paging on the API stops at 10,000 results per query.

## Options considered

| Option | Pros | Cons |
| --- | --- | --- |
| A. API only | Small daily pulls, filters by date and product | Backfill of millions of rows needs thousands of narrow queries |
| B. CSV only | Complete history in one file | Several GB per refresh; daily refresh wastes bandwidth |
| C. Both, mapped to one canonical record | Each source used where it is strong | Two field maps to maintain |

## Decision

Option C. `schema.py` holds `API_FIELD_MAP` and `CSV_FIELD_MAP`; both map to the same `Complaint`. The scheduled job uses the API with a two-day look-back (`--days 2`) so late-arriving complaints are picked up and upserted; backfills use `make download-csv && make ingest-csv`.

## Consequences

- If CFPB renames a field, the run's quality report shows it under `schema_drift` (an unexpected new field and a missing expected one) instead of silently storing nulls.
- API parameter names must be checked against the live CFPB documentation before production use (see DATASETS).
