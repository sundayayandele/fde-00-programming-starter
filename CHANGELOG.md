# Changelog

All notable changes. Versions follow semantic versioning; the starter repo is republished on every `v*` tag.

## [Unreleased]

## [1.1.0] - 2026-10-21

Repository and CI fixes; no change to the system's behaviour.

### Fixed
- Restored the files dropped on the first upload: GitHub Actions workflows, `.gitignore`, `.dockerignore`, `.env.example` and the starter configuration.
- Security workflow: `aquasecurity/trivy-action` pinned to the v0.36.0 commit (the `0.28.0` tag no longer resolves).
- Desktop Kubernetes overlays (kind, Docker Desktop, Rancher Desktop) now deploy Postgres into the `fde` namespace; the kind e2e job was failing.

## [1.0.0] - 2026-10-12

### Added
- `complaints_ingest` package and `complaints-ingest` CLI: CFPB search API client (paging, retries, back-off), streamed bulk-CSV reader, canonical `Complaint` schema with field maps for both sources, cleaning (text, booleans, dates), PII masking, validation with rejection reasons, idempotent upsert for SQLite and Postgres, run log, streaming data-quality report (null rates, duplicate IDs, rejection reasons, schema drift, PII masked), seeded synthetic data.
- Report API: `/api/v1/summary`, `/by-month`, `/complaints` (search with filters and paging), `/runs`; readiness checks the database; gauges `complaints_stored` and `complaints_last_ingest_timestamp_seconds`; alerts `IngestStale` and `DatabaseUnreachable`; Grafana panels.
- Deployment: Postgres + API + ingest job on Compose (Docker, Rancher), Podman pod, Kubernetes (CronJob in base; in-cluster Postgres StatefulSet for desktop overlays; external DB Secret on cloud and OpenShift), Helm CronJob; Terraform with RDS + EventBridge Scheduler (AWS), Postgres Flexible Server + Container Apps Job (Azure), Cloud SQL + Cloud Run job + Cloud Scheduler (GCP).
- Tests (108, coverage 97%) including Postgres integration tests run in CI against a service container; `scripts/benchmark.py`; committed benchmark and memory results.
- Docs: architecture, C4, ADR-004 to ADR-007, customer brief and decision memo, security and threat model, data card, evaluation, datasets, infrastructure, capacity, cost, deployment, desktop and cloud labs; labs weeks 0–4.

### Changed
- Created from `fde-template` 0.1.0; hello endpoint removed. The LLM client is kept for later phases and is not used here.
