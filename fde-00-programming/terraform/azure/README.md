# Azure lab stack

Container Registry (Basic); **Container Apps** running the report API (0.25 vCPU, 0.5 GiB,
scale to zero); a **Container Apps Job** on a cron schedule for ingest; **Azure Database for
PostgreSQL Flexible Server 16** (Burstable `B_Standard_B1ms`, 32 GiB); Key Vault (RBAC) holding
`DATABASE_URL`, read through a user-assigned managed identity; Log Analytics; and a monthly
budget with alerts at 50, 80 and 100 percent of USD 50.

```bash
az login && az account set -s <sandbox-subscription-id>
make tf-azure-init

# 1) Registry, identity, Key Vault, Postgres and budget (no app yet)
terraform -chdir=terraform/azure apply -var subscription_id=<id> -var alert_email=you@example.com

# 2) Push the image
ACR=$(terraform -chdir=terraform/azure output -raw registry_name)
az acr login -n $ACR
docker tag fde-00-programming:local $ACR.azurecr.io/fde-00-programming:1.0.0
docker push $ACR.azurecr.io/fde-00-programming:1.0.0

# 3) Create the Container App and the ingest job, load data, smoke test, destroy
terraform -chdir=terraform/azure apply -var subscription_id=<id> -var alert_email=you@example.com \
  -var deploy_app=true
eval "$(terraform -chdir=terraform/azure output -raw run_ingest_now)"
python scripts/smoke_test.py --base-url $(terraform -chdir=terraform/azure output -raw app_url)
make tf-azure-destroy
```

Notes:

- Lab trade-off: Postgres allows connections from Azure services (firewall rule `0.0.0.0`) rather
  than VNet integration, and requires TLS (`sslmode=require`). For production, use a VNet-integrated
  Container Apps environment and private access. Recorded in `docs/security/THREAT-MODEL.md`.
- If the region rejects the B1ms SKU or has no capacity, use `-var location=northeurope`.
- Set `budget_start_date` to the first day of the current month. Build for `linux/amd64` on Apple
  silicon.
