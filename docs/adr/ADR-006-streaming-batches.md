# ADR-006: Stream in batches and keep quality counters, not row lists

- **Status:** Accepted
- **Date:** 2026-10-12
- **Deciders:** Sunday Ayandele (owner)

## Context

The first version collected every raw row, record and rejection in lists to build the quality report at the end. That is fine for a 5,000-row API pull and fails for the multi-gigabyte bulk CSV on a 512 MiB container.

## Options considered

| Option | Pros | Cons |
| --- | --- | --- |
| A. Load everything, then report | Simple | Memory grows with input size |
| B. Batches of N rows; per-run counters (`QualityTracker`) | Flat memory; report covers the whole run | Duplicate-ID set still grows with unique IDs |
| C. pandas chunks | Familiar to analysts | Heavier dependency; same counter problem |

## Decision

Option B, batch size 1,000. Measured: a 300,000-row CSV ingest peaked at 97 MB RSS (README results).

## Consequences

- The duplicate-ID count needs a set of IDs seen in the run. If runs reach tens of millions of rows, replace it with a database-side check or a probabilistic counter.
- Batch size is a tuning knob (`--batch-size` in `scripts/benchmark.py`); SQLite's bound-parameter limit caps it near 1,700 rows for 19 columns.
