# Deployment

Every path runs the same image with two entry points: the report API (`uvicorn app.main:app`) and the ingest job (`complaints-ingest`). Every path needs `DATABASE_URL`.

| Path | Start | Load data | Details |
| --- | --- | --- | --- |
| Local Python | `make run` / `make e2e` | `make ingest-synthetic`, `make ingest-api` | SQLite in `artifacts/` |
| Docker Desktop | `make up-docker` | `make ingest-docker ARGS="ingest-api --days 7"` | [Desktop labs](learning/DESKTOP-LABS.md#1a-docker-desktop) |
| Podman Desktop | `make up-podman` | `make ingest-podman ARGS="ingest-api --days 7"` | [Desktop labs](learning/DESKTOP-LABS.md#1b-podman-desktop) |
| Rancher Desktop | `make up-rancher` | `make ingest-rancher ARGS="ingest-api --days 7"` | [Desktop labs](learning/DESKTOP-LABS.md#1c-rancher-desktop) |
| Desktop Kubernetes | `make k8s-docker` / `k8s-rancher` / `k8s-kind` | `make k8s-ingest` | In-cluster Postgres; CronJob suspended |
| Managed Kubernetes | Create Secret `fde-00-programming-db`, then `kubectl apply -k deploy/kubernetes/overlays/cloud` | CronJob runs daily; `make k8s-ingest` | Set the image with `kustomize edit set image` |
| Helm | `helm upgrade --install complaints deploy/helm/fde-00-programming` | CronJob; `--set ingest.args=...` | `--set route.enabled=true` on OpenShift |
| OpenShift | Create the DB Secret, then `oc apply -k deploy/openshift` | CronJob | Route with edge TLS |
| AWS / Azure / GCP | `make tf-<cloud>-plan`, then the stack README | Scheduled; `terraform output run_ingest_now` | [Cloud labs](learning/CLOUD-LABS.md) |

## Release

1. Update `CHANGELOG.md`; bump the version in `pyproject.toml`, `src/complaints_ingest/__init__.py`, `Chart.yaml`, the cloud overlay `newTag` and Terraform `image_tag` defaults.
2. Tag `vX.Y.Z` and push the tag. The `publish-starter` workflow regenerates the starter repo.
3. Build and push the image to each registry you deploy to, tagged with the same version.

## Operations

| Task | Command |
| --- | --- |
| See recent runs | `complaints-ingest runs` or `GET /api/v1/runs` |
| Inspect one run's quality report | `SELECT quality_json FROM ingest_runs ORDER BY run_id DESC LIMIT 1;` |
| Re-load a date window | `complaints-ingest ingest-api --since 2026-09-01 --until 2026-09-30 --limit 10000` (safe: upsert) |
| Backfill full history | `make download-csv && make ingest-csv` (from a machine that can reach the database) |

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `/health/ready` returns 503 `database unavailable` | `DATABASE_URL` set? Database up (`pg_isready`)? NetworkPolicy allows the pod? Cloud: secret value and firewall/connector |
| Pod `CreateContainerConfigError` | Secret `fde-00-programming-db` missing (required on OpenShift, Helm and cloud overlay) |
| Postgres pod `CrashLoopBackOff` on desktop Kubernetes | PVC not bound (`kubectl get pvc`); delete the namespace and re-apply to re-initialise |
| `IngestStale` alert | Job history: `kubectl get jobs`, ECS stopped tasks, `az containerapp job execution list`, `gcloud run jobs executions list`; CFPB API reachable from the job? |
| Run shows many rejections | `rejection_reasons` in the run's quality report; a new reason usually means a source change |
| `schema_drift.unexpected_fields` not empty | CFPB added or renamed a field; update `schema.py` field maps and tests |
| CFPB returns 429 / 5xx | The client backs off and retries; reduce `--limit` or page size (`CFPB_PAGE_SIZE`) |
| Budget alert received | `make tf-<cloud>-destroy`; check for orphaned databases in the console |
