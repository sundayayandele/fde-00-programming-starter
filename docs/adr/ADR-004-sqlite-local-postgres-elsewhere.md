# ADR-004: SQLite locally, Postgres everywhere else, one code path

- **Status:** Accepted
- **Date:** 2026-10-12
- **Deciders:** Sunday Ayandele (owner)

## Context

Learners must be able to run the pipeline in five minutes with no services installed, yet the deployed system needs a real multi-client database that the API and a scheduled job can share. Every cloud offers managed Postgres; all three desktops can run the official `postgres:16-alpine` image.

## Options considered

| Option | Pros | Cons | Cost / effort |
| --- | --- | --- | --- |
| A. SQLite everywhere | Zero setup | One writer, file on a volume; no managed offering in any cloud | Lowest |
| B. Postgres everywhere | One engine to test | Every lab needs a running database first | Higher setup |
| C. SQLite locally, Postgres elsewhere, via SQLAlchemy Core | Fast start; production-like deployments | Two dialects to keep working | Medium; tests on both |
| D. DuckDB | Fast analytics | Not a shared service; no managed cloud offering | Low |

## Decision

Option C. The only dialect-specific code is the upsert (`on_conflict_do_update` from the matching dialect module) and the month function in `counts_by_month`. Both are covered by `tests/test_postgres.py`, which CI runs against a Postgres 16 service container.

## Consequences

- `DATABASE_URL` is the single switch; every deployment sets it from its secret store.
- Postgres runs as an in-cluster StatefulSet only on desktop clusters; OpenShift and clouds use a managed database.
- Revisit if analytics queries outgrow Postgres (then add a warehouse export, not a new primary store).
