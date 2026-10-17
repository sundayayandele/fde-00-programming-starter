# Infrastructure

| Target | API | Ingest | Database | Secrets | Manifests |
| --- | --- | --- | --- | --- | --- |
| Local Python | `make run` | `complaints-ingest ...` | SQLite `artifacts/complaints.db` | `.env` | — |
| Docker / Rancher Desktop | Compose `api` | Compose `ingest` (profile `jobs`) | Compose `db` (postgres:16-alpine, named volume) | env from `.env` | `deploy/compose/compose.yaml` |
| Podman Desktop | pod container `api` | `podman exec ... complaints-ingest` | pod container `db` + named volume | pod env (lab) / podman secret | `deploy/podman/pod.yaml` |
| Desktop Kubernetes (Docker, Rancher, kind) | Deployment + HPA + PDB | CronJob (suspended; run with `make k8s-ingest`) | StatefulSet + PVC (component `_shared`) | Secret `fde-00-programming-db` | `deploy/kubernetes/overlays/*` |
| OpenShift | Deployment + Route | CronJob | Managed / operator Postgres | Secret created by you | `deploy/openshift` |
| Helm | Deployment (+ Ingress/Route) | CronJob | External | `database.existingSecret` | `deploy/helm/fde-00-programming` |
| AWS | ECS Fargate service | EventBridge Scheduler → ECS task | RDS PostgreSQL 16 | Secrets Manager | `terraform/aws` |
| Azure | Container App | Container Apps Job | Postgres Flexible Server 16 | Key Vault + managed identity | `terraform/azure` |
| GCP | Cloud Run service | Cloud Scheduler → Cloud Run job | Cloud SQL PostgreSQL 16 | Secret Manager | `terraform/gcp` |

Schedule everywhere: daily 06:15 UTC, ingest the last two days (`ingest-api --days 2 --limit 5000`). Overlap is safe because the load is an upsert.

Monitoring: `monitoring/prometheus.yml` scrapes `/metrics/`; `alerts.yml` adds `IngestStale` (no finished run for 26 h) and `DatabaseUnreachable`; Grafana dashboard "FDE service overview" shows requests, latency, complaints stored and hours since the last ingest.
