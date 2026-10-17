output "registry_login_server" {
  description = "Push the image here: az acr login -n <name>; docker push <server>/fde-00-programming:<tag>"
  value       = azurerm_container_registry.lab.login_server
}

output "registry_name" {
  value = azurerm_container_registry.lab.name
}

output "app_url" {
  description = "Public HTTPS URL of the Container App (after deploy_app=true)"
  value       = var.deploy_app ? "https://${azurerm_container_app.app[0].ingress[0].fqdn}" : "not deployed yet"
}

output "database_fqdn" {
  value = azurerm_postgresql_flexible_server.db.fqdn
}

output "run_ingest_now" {
  description = "Start the ingest job once, without waiting for the schedule"
  value       = var.deploy_app ? "az containerapp job start -n ${azurerm_container_app_job.ingest[0].name} -g ${azurerm_resource_group.lab.name}" : "not deployed yet"
}
