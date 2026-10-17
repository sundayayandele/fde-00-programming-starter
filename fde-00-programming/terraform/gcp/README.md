# GCP lab stack

Artifact Registry; **Cloud Run** service for the report API (1 vCPU, 512 MiB, scale to zero);
a **Cloud Run job** for ingest, started daily by **Cloud Scheduler**; **Cloud SQL for
PostgreSQL 16** (Enterprise edition, `db-f1-micro`, 10 GB HDD, no authorised networks, TLS
only); Secret Manager holding `DATABASE_URL`; dedicated service accounts; and an optional
billing budget with alerts at 50, 80 and 100 percent of USD 50.

Cloud Run connects to Cloud SQL through the built-in Cloud SQL connector, mounted at
`/cloudsql`; the `DATABASE_URL` uses `?host=/cloudsql/<connection-name>`.

```bash
gcloud auth application-default login && gcloud config set project <sandbox-project>
make tf-gcp-init

# 1) APIs, registry, Cloud SQL, secret, service accounts, budget (Cloud SQL takes ~10 minutes)
terraform -chdir=terraform/gcp apply -var project_id=<project> -var billing_account=<id>

# 2) Push the image
REPO=$(terraform -chdir=terraform/gcp output -raw image_repository)
gcloud auth configure-docker ${REPO%%/*}
docker tag fde-00-programming:local $REPO/fde-00-programming:1.0.0
docker push $REPO/fde-00-programming:1.0.0

# 3) Deploy Cloud Run service, job and schedule; load data; smoke test; destroy
terraform -chdir=terraform/gcp apply -var project_id=<project> -var billing_account=<id> -var deploy_app=true
eval "$(terraform -chdir=terraform/gcp output -raw run_ingest_now)"
python scripts/smoke_test.py --base-url $(terraform -chdir=terraform/gcp output -raw app_url)
make tf-gcp-destroy
```

Notes:

- Cloud Scheduler must be available in your region; `europe-west1` and `europe-west4` support it.
- `db-f1-micro` is a shared-core tier for labs only; it has no SLA.
- Budget alerts go to the billing account's admins by default. Build for `linux/amd64` on Apple silicon.
