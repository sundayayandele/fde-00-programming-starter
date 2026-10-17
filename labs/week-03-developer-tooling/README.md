# Week 03: Developer tooling: tests, lint, CI, containers

**Goal:** work like a professional team: tests with fixtures and coverage, a linter, CI on every push, and a container image that runs anywhere.

## Brief

The bank's platform team will only run code that passes CI and ships as a non-root container. They also want a data-quality report with every load.

## Concepts

pytest fixtures (`conftest.py`), markers, coverage, `ruff`, GitHub Actions, multi-stage Dockerfiles, non-root containers, Compose services and health checks.

## Steps

1. In `src/complaints_ingest/quality.py`, implement `null_counts(records)`: a dict with every name in `CANONICAL_FIELDS` and how many records have `None` for it. Run `pytest tests/test_quality.py -m exercise`.
2. Read `tests/conftest.py`. Explain how the API tests get their own database without touching yours.
3. Run `make test` and read the coverage table. Find one uncovered line in `cfpb.py` and write a test that covers it.
4. Run `make lint`, then break a rule on purpose (an unused import) and see CI fail on a branch push.
5. Read the `Dockerfile`: which user does the container run as, and why is group 0 used? Build it, then run `make up-docker` (or Podman/Rancher) and `make ingest-docker ARGS="ingest-synthetic --count 5000"`.
6. Open `docker compose ... ps` and explain why `api` waits for `db` to be healthy.

## Check

```bash
make lint && make test && make exercises
make up-docker && make ingest-docker ARGS="ingest-synthetic --count 5000"
```

## Evidence

A green CI run on GitHub (screenshot or link), the coverage percentage, and the JSON quality report of one run (`SELECT quality_json FROM ingest_runs ...` or `/api/v1/runs`).

## Stretch

Add `mypy` to the dev dependencies and a `make typecheck` target; fix what it finds in `src/`.
