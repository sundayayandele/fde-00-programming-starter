# Learning guide: Phase 0, programming foundations (weeks 1–4)

## Outcomes

By the end of this phase you can:

1. Write typed, tested Python that turns messy real-world records into validated objects.
2. Use the developer toolchain every later phase assumes: virtual environments, `make`, `pytest`, `ruff`, Git, CI, containers.
3. Read from an HTTP API politely (paging, retries, back-off) and stream large files.
4. Store data in SQL with an idempotent upsert and query it with `GROUP BY`.
5. Ship the same service to a desktop engine and explain how it would run on a cloud.

## Weekly plan

| Week | Lab | Concepts | Exercises (in the starter) |
| --- | --- | --- | --- |
| 0 | [Set up](../../labs/week-00-setup/README.md) | venv, make, Git, Docker/Podman/Rancher | none |
| 1 | [Python basics](../../labs/week-01-python-basics/README.md) | strings, `None`, regex, dates, functions, parametrised tests | `normalise_text`, `parse_bool`, `parse_date` |
| 2 | [Python for real work](../../labs/week-02-python-for-real-work/README.md) | dicts, comprehensions, dataclasses, pydantic, error handling | `mask_pii`, `to_complaint` |
| 3 | [Developer tooling](../../labs/week-03-developer-tooling/README.md) | pytest fixtures, coverage, ruff, CI, Dockerfile, Compose | `null_counts` |
| 4 | [Data handling](../../labs/week-04-data-handling/README.md) | HTTP + JSON, CSV streaming, SQL upsert, aggregation, benchmarks | `parse_page`, `upsert_complaints`, `counts_by_product`, results table |

Budget about 10–12 hours per week.

## Exit check

From a fresh clone of your repo:

```bash
make install && make test && make exercises && make e2e
make up-docker   # or up-podman / up-rancher
make ingest-docker ARGS="ingest-api --days 7"
curl -s http://127.0.0.1:8000/api/v1/summary | python -m json.tool
```

…and your README results table holds throughput and coverage numbers **you** measured, with the command and date.

## How to use the repos

1. Start from the **starter repo** (`fde-00-programming-starter`): "Use this template" on GitHub, then clone your copy.
2. Work through the labs in order. `make exercises` shows what is left; `make test` stays green throughout.
3. Compare with the **reference repo** only after you have tried each exercise yourself.

## Portfolio evidence a hiring manager will look for

- The results table with real numbers and how they were produced.
- One desktop run and one cloud `plan` (or apply + destroy) with smoke-test output.
- A quality report from a real CFPB pull, and one paragraph on what it told you.
- The customer brief and decision memo in your own words.
