# Evaluation: how this phase is measured

There is no model to evaluate. The pipeline is judged on correctness, quality evidence, throughput and memory.

| What | Method | Where |
| --- | --- | --- |
| Correctness | 108 unit, API, CLI and integration tests; coverage gate 80% (measured 97%) | `make test`; CI `ci` |
| Same behaviour on Postgres | `tests/test_postgres.py` against Postgres 16 | CI service container; `make test-postgres` |
| End to end | Smoke checks against a running API with data | `make e2e`; CI `e2e` (process, Compose, kind) |
| Throughput | `scripts/benchmark.py`: 50,000 seeded synthetic rows, 3 repeats, median; fresh database per repeat; insert then re-ingest | `evals/results/benchmark-*.json` |
| Memory | Peak RSS of `ingest-csv` on a 300,000-row CSV | `evals/results/memory-csv-*.json` |
| Data quality | Report per run: rows read/valid/rejected, reasons, duplicate IDs, null rates, schema drift, PII masked | `ingest_runs.quality_json`; `complaints-ingest runs` |

## Reproduce

```bash
make bench
python scripts/benchmark.py --database-url postgresql+psycopg://complaints:complaints-local@127.0.0.1:5432/complaints
```

Results depend on CPU, disk and where Postgres runs. Always record machine, versions and date next to the number.
