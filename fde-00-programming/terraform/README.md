# Cloud lab stacks

| Cloud | API | Scheduled ingest | Database | Secrets | Budget |
| --- | --- | --- | --- | --- | --- |
| [AWS](aws/README.md) | ECS Fargate (public IP, no load balancer) | EventBridge Scheduler → ECS task | RDS PostgreSQL 16, db.t4g.micro, private | Secrets Manager | AWS Budgets, email at 50/80/100% |
| [Azure](azure/README.md) | Container Apps, scale to zero | Container Apps Job (cron) | Postgres Flexible Server 16, B1ms | Key Vault (RBAC) + managed identity | Consumption budget, email at 50/80/100% |
| [GCP](gcp/README.md) | Cloud Run, scale to zero | Cloud Scheduler → Cloud Run job | Cloud SQL PostgreSQL 16, db-f1-micro | Secret Manager | Billing budget at 50/80/100% |

Rules for every lab:

1. Use a sandbox account, subscription or project; never production.
2. Budget is USD 50 per month per cloud. Each stack creates its own budget alert. The managed
   database is the main running cost: **destroy the stack at the end of every lab**.
3. `plan` is safe; `fmt` runs in CI everywhere and `validate`/`tflint` in the `iac` workflow (no
   credentials). `apply` is a manual lab step.
4. Never commit state, plans or `.tfvars` (all ignored by `.gitignore`). State holds the generated
   database password.

State is local by default. For a team, add a remote backend (S3, Azure Storage, GCS) in a
`backend.tf` that is not committed with real names.
