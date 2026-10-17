# Threat model (STRIDE)

## Assets

Complaint records (may contain personal data in narratives), the database credentials, the run log.

## Trust boundaries

CFPB API → ingest job; job → database; user → report API; scheduler → job; secret store → containers.

## Threats

| STRIDE | Threat | Mitigation | Residual |
| --- | --- | --- | --- |
| Spoofing | Fake CFPB endpoint via DNS or proxy | HTTPS with certificate verification (httpx default) | Low |
| Tampering | Malformed or hostile rows (huge fields, bad dates) | Pydantic validation, length limits, rejection with reason | Low |
| Tampering | SQL injection through search parameters | Bound parameters only (SQLAlchemy Core) | Low |
| Repudiation | Unknown who/what loaded data | `ingest_runs` row per run with source, timings, counts | Medium (no user identity; jobs only) |
| Information disclosure | PII in narratives stored or served | Regex masking at ingest; API is unauthenticated **in labs** | Names and addresses are not masked; add auth before real data |
| Information disclosure | Database password leak | Secret stores; generated passwords; not in Git | In Terraform state: keep state private |
| Denial of service | Large `limit`/`offset` queries | `limit` ≤ 500; indexed filter columns | Deep offsets are slow; add keyset paging if needed |
| Denial of service | CFPB rate limiting | Back-off on 429/5xx, page pause, two-day window | Low |
| Elevation of privilege | Container escape | Non-root, no capabilities, seccomp RuntimeDefault, read-only FS | Low |

## Accepted lab trade-offs (Trivy misconfiguration findings are non-blocking for these)

| Trade-off | Why | Production fix |
| --- | --- | --- |
| Report API reachable without authentication | Keeps labs simple | Put behind the platform's SSO/ingress auth or API gateway |
| AWS task has a public IP, no load balancer | Stays inside USD 50 | ALB with TLS, private subnets, NAT |
| Azure Postgres open to Azure services (0.0.0.0 rule), TLS required | VNet integration needs a larger environment | VNet-integrated Container Apps + private access |
| Cloud SQL `ipv4_enabled` (no authorised networks) | Cloud Run connector needs no VPC setup | Private IP + Serverless VPC access |
| Egress open from pods | Job needs the CFPB API | Egress policy to CFPB and DNS only (fde-05) |
| Desktop Postgres uses a fixed lab password | No secret tooling on laptops | External Secrets / sealed secrets |
| No customer-managed encryption keys | Cost and complexity | CMK in KMS / Key Vault / Cloud KMS |
