# Security

## Reporting

Open a private security advisory on the GitHub repository. Do not file public issues for vulnerabilities.

## Controls in this repo

| Area | Control |
| --- | --- |
| Secrets | `DATABASE_URL` comes from the environment: Compose env, Kubernetes Secret, AWS Secrets Manager, Azure Key Vault (managed identity), GCP Secret Manager. Nothing secret is committed; `.env`, state and `.tfvars` are git-ignored. Lab-only default passwords (`complaints-local`) exist for unexposed desktop databases and are labelled as such. |
| Personal data | Narratives are PII-masked at ingest (ADR-007). Only stored fields are those in `Complaint`. |
| Least privilege | Containers run as UID 10001, no capabilities, no privilege escalation, read-only root filesystem (API and job), restricted Pod Security Standard. Postgres on desktop clusters runs as UID 70. |
| Network | Desktop ports bind to 127.0.0.1. NetworkPolicy limits API ingress to port 8000 and Postgres ingress to the API and job pods. RDS is private; Cloud SQL has no authorised networks; Azure Postgres requires TLS. |
| Input validation | Query parameters validated by FastAPI (limits, dates); every row validated by pydantic before storage. |
| SQL | SQLAlchemy Core with bound parameters only; no string-built SQL. |
| Supply chain | `security` workflow: pip-audit, gitleaks, Trivy (dependencies, secrets, image). |
| Read-only API | The API has no write endpoints; only the job writes. |

See [THREAT-MODEL](THREAT-MODEL.md) for threats and accepted lab trade-offs.
