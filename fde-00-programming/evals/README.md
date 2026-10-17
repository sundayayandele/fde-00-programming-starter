# Evals

Phase 0 has no model. Its evaluation is about the pipeline:

| What | How | Output |
| --- | --- | --- |
| Throughput | `make bench` / `scripts/benchmark.py` (50,000 seeded synthetic rows, 3 repeats, median; insert and re-ingest) | `evals/results/benchmark-<db>-<date>.json` |
| Memory | `ingest-csv` on a large CSV, peak RSS | `evals/results/memory-csv-<date>.json` |
| Correctness on Postgres | `tests/test_postgres.py` | CI `ci` job |
| Data quality | Report per run | `ingest_runs.quality_json` |

The `evals` workflow re-runs the benchmark weekly on GitHub runners and uploads the JSON as an artifact. Numbers in the README come from the committed files, which record the machine and date.
