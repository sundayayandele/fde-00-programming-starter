# Cloud labs: AWS, Azure, GCP

Each cloud stack runs the report API on the cheapest managed container service, the ingest job on that cloud's scheduler, and a small managed Postgres. Step-by-step commands are in each stack's README:

- [AWS: ECS Fargate + RDS + EventBridge Scheduler](../../terraform/aws/README.md)
- [Azure: Container Apps + Postgres Flexible Server + Container Apps Job](../../terraform/azure/README.md)
- [GCP: Cloud Run + Cloud SQL + Cloud Scheduler](../../terraform/gcp/README.md)

## Rules

1. **Sandbox only.** Use a dedicated sandbox account, subscription or project.
2. **Budget:** USD 50 per month per cloud, alerts at 50, 80 and 100 percent (created by the stack). The managed database bills by the hour whether or not you use it.
3. **Plan first.** `terraform plan` is free and safe. Read the plan before `apply`.
4. **Destroy every time.** `make tf-<cloud>-destroy` at the end of the lab, then check the console for leftover databases.
5. **Never commit** state files, plans or `.tfvars`. State contains the generated database password.

## Typical lab flow (about 60–90 minutes, most of it waiting for the database)

```bash
docker build -t fde-00-programming:local .          # add --platform linux/amd64 on Apple silicon
make tf-<cloud>-init
# apply 1: registry, database, secret, identity, budget
# push the image to the registry the stack created
# apply 2 (Azure/GCP: deploy_app=true; AWS: force a new deployment)
# run the ingest once: eval "$(terraform -chdir=terraform/<cloud> output -raw run_ingest_now)"
python scripts/smoke_test.py --base-url <url printed by terraform output>
make tf-<cloud>-destroy
```

## Evidence for your portfolio

The `terraform plan` summary, the ingest run log (`/api/v1/runs`), the smoke-test output against the cloud URL, a screenshot of the budget, and the `destroy` output. Record the date and region.
