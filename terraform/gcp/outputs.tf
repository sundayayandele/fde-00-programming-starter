output "image_repository" {
  description = "Push the image here: gcloud auth configure-docker <region>-docker.pkg.dev; docker push <repo>/fde-00-programming:<tag>"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}

output "app_url" {
  description = "Cloud Run URL (after deploy_app=true)"
  value       = var.deploy_app ? google_cloud_run_v2_service.app[0].uri : "not deployed yet"
}

output "database_connection_name" {
  value = google_sql_database_instance.db.connection_name
}

output "run_ingest_now" {
  description = "Start the ingest job once, without waiting for the schedule"
  value       = var.deploy_app ? "gcloud run jobs execute ${google_cloud_run_v2_job.ingest[0].name} --region ${var.region} --wait" : "not deployed yet"
}
