variable "subscription_id" {
  description = "Azure subscription for the lab (use a sandbox subscription)."
  type        = string
}

variable "location" {
  description = "Azure region. westeurope (Netherlands) or northeurope (Ireland) keep data in the EU."
  type        = string
  default     = "westeurope"
}

variable "app_name" {
  description = "Name used for every resource."
  type        = string
  default     = "fde-00-programming"
}

variable "image_tag" {
  description = "Image tag pushed to the registry created here."
  type        = string
  default     = "1.0.0"
}

variable "deploy_app" {
  description = "Create the Container App. Set false on the first apply, push the image, then set true."
  type        = bool
  default     = false
}

variable "ingest_cron" {
  description = "Cron expression (UTC) for the ingest Container Apps Job."
  type        = string
  default     = "15 6 * * *"
}

variable "ingest_args" {
  description = "Arguments for the scheduled `complaints-ingest` job."
  type        = list(string)
  default     = ["ingest-api", "--days", "2", "--limit", "5000"]
}

variable "monthly_budget_usd" {
  description = "Monthly budget for the lab resource group; alerts at 50, 80 and 100 percent."
  type        = number
  default     = 50
}

variable "budget_start_date" {
  description = "First day of the current month, RFC 3339 (Azure requires the first of a month)."
  type        = string
  default     = "2026-10-01T00:00:00Z"
}

variable "alert_email" {
  description = "Email that receives budget alerts."
  type        = string
}
