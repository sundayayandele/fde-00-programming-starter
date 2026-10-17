variable "project_id" {
  description = "GCP project for the lab (use a sandbox project)."
  type        = string
}

variable "region" {
  description = "Region. europe-west1 (Belgium) or europe-west4 (Netherlands) keep data in the EU."
  type        = string
  default     = "europe-west4"
}

variable "app_name" {
  description = "Name used for every resource."
  type        = string
  default     = "fde-00-programming"
}

variable "image_tag" {
  description = "Image tag pushed to the Artifact Registry repository created here."
  type        = string
  default     = "1.0.0"
}

variable "deploy_app" {
  description = "Create the Cloud Run service. Set false on the first apply, push the image, then set true."
  type        = bool
  default     = false
}

variable "allow_public" {
  description = "Allow unauthenticated calls (lab only)."
  type        = bool
  default     = true
}

variable "ingest_cron" {
  description = "Cron expression (UTC) for Cloud Scheduler to start the ingest job."
  type        = string
  default     = "15 6 * * *"
}

variable "ingest_args" {
  description = "Arguments for the scheduled `complaints-ingest` job."
  type        = list(string)
  default     = ["ingest-api", "--days", "2", "--limit", "5000"]
}

variable "billing_account" {
  description = "Billing account ID for the budget (XXXXXX-XXXXXX-XXXXXX). Leave empty to skip the budget."
  type        = string
  default     = ""
}

variable "monthly_budget_usd" {
  description = "Monthly budget; alerts at 50, 80 and 100 percent go to billing admins."
  type        = number
  default     = 50
}
