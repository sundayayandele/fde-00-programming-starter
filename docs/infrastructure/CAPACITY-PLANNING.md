# Capacity planning

## Measured inputs (README results, 2026-10-12, 2 vCPU host)

| Measure | Value |
| --- | --- |
| Pipeline throughput into Postgres | ~160k records/min (synthetic) |
| Pipeline throughput into SQLite | ~220k records/min (synthetic) |
| Peak memory, streaming CSV | 97 MB for 300k rows |

## Sizing

| Workload | Estimate | Sizing |
| --- | --- | --- |
| Daily API delta (a few thousand complaints) | Seconds of CPU; dominated by CFPB paging (0.5 s pause per 500-row page) | 0.25 vCPU / 512 MiB job is ample |
| Full-history CSV backfill (several million rows) | Millions ÷ 160k/min ≈ tens of minutes of pipeline time, plus download and disk I/O | Run once from a laptop or a 1 vCPU job; raise `activeDeadlineSeconds` above 1,800 s |
| Report API | Aggregations over the full table; indexed on date, product, issue, company | 1 replica handles lab traffic; HPA 2–5 on CPU |
| Storage | Narratives dominate row size; expect a few GB for the full history including indexes | 20 GB (RDS), 32 GB (Azure), 10 GB HDD (GCP) for labs; grow before a full backfill on GCP |

Estimates (not measured) are labelled; replace them with your own numbers after a real backfill.

## Scaling triggers

- Summary endpoint p95 > 1 s → add a materialised summary table refreshed by the job.
- Backfill exceeds the job deadline → use date windows (`ingest-api --since ... --until ...`) or run the CSV path outside the scheduled job.
- Duplicate-ID set memory matters (tens of millions of rows per run) → see ADR-006.
