# Cost and total cost of ownership

> **Estimates, not bills.** Prices below are approximate on-demand list prices as remembered
> for EU regions in mid-2026, written without live access to pricing pages. Check each
> provider's pricing page (and calculator) before you apply, and record the date you checked.

## Lab stack, per month if left running

| Cloud | Item | Approximate price | Monthly |
| --- | --- | --- | --- |
| AWS | Fargate API task, 0.25 vCPU + 0.5 GB, 24×7 | ~USD 0.04/vCPU-h, ~0.0045/GB-h | ~USD 9 |
| AWS | Public IPv4 on the task | ~USD 0.005/h | ~USD 3.6 |
| AWS | RDS db.t4g.micro PostgreSQL, single-AZ, 20 GB gp3 | ~USD 0.018/h + storage | ~USD 15 |
| AWS | Daily ingest task (a few minutes), Secrets Manager, logs, ECR | small | ~USD 1–2 |
| **AWS total** | | | **~USD 28–30** |
| Azure | Container Apps API, scale to zero, consumption plan | monthly free grant covers light lab use | ~USD 0–3 |
| Azure | Postgres Flexible Server B1ms + 32 GiB storage | ~USD 12–13 + ~4 | ~USD 16–17 |
| Azure | ACR Basic | ~USD 5 | ~USD 5 |
| Azure | Container Apps Job, Key Vault, Log Analytics | small | ~USD 1 |
| **Azure total** | | | **~USD 22–26** |
| GCP | Cloud Run API, scale to zero | free tier covers light lab use | ~USD 0 |
| GCP | Cloud SQL db-f1-micro + 10 GB HDD | ~USD 8 + ~1 | ~USD 9–10 |
| GCP | Cloud Run job, Cloud Scheduler (≤3 jobs free), Secret Manager, Artifact Registry | small | ~USD 0–1 |
| **GCP total** | | | **~USD 10–12** |

All three stay under the USD 50 per-cloud budget; destroying after each lab keeps the real cost to a few dollars.

## How to compute your own

```text
monthly_compute = hours_running × (vCPU × vCPU_price + GB × GB_price)
monthly_database = hours × instance_price + GB_stored × storage_price
cost_per_run     = run_minutes / 60 × (vCPU × vCPU_price + GB × GB_price)
```

Take `run_minutes` from `/api/v1/runs` (`duration_seconds`) after a real pull, not from estimates.

## Three scenarios for the customer

| Scenario | When it fits | Main cost drivers |
| --- | --- | --- |
| Existing on-prem / OpenShift | Regulated data, platform already paid for | One small pod and a daily job; the database team's time |
| Self-hosted VPS | Small pilots, predictable load | Fixed monthly instance; your time to patch and back up Postgres |
| Hyperscaler (AWS, Azure, GCP) | Managed backups and HA, enterprise procurement | Managed Postgres hours dominate; compute is near zero with scale-to-zero |

The ingest itself is cheap: at the measured ~160k records/min, a daily delta takes seconds of compute. The database is the cost.
