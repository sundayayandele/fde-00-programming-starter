# Lab deployment on GCP for the complaints ingestion service:
#   Artifact Registry, Cloud Run service (report API, scale to zero), Cloud Run job
#   (ingest) triggered by Cloud Scheduler, Cloud SQL for PostgreSQL 16 (db-f1-micro,
#   Enterprise edition), Secret Manager holding DATABASE_URL, dedicated service
#   accounts, and an optional billing budget.
# Cloud Run reaches Cloud SQL through the built-in Cloud SQL connector (unix socket
# under /cloudsql); the instance has no authorised networks, so nothing else can
# connect without IAM. The generated password is in Terraform state.
# Two-step apply: first with deploy_app=false, push the image, then deploy_app=true.
# Destroy at the end of every lab: `make tf-gcp-destroy`.

data "google_project" "this" {}

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com", "artifactregistry.googleapis.com", "secretmanager.googleapis.com",
    "billingbudgets.googleapis.com", "sqladmin.googleapis.com", "cloudscheduler.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = var.app_name
  format        = "DOCKER"
  description   = "FDE series images"
  depends_on    = [google_project_service.apis]
}

resource "google_service_account" "run" {
  account_id   = "${var.app_name}-run"
  display_name = "Cloud Run runtime for ${var.app_name}"
}

resource "google_project_iam_member" "run_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.run.email}"
}

# ---- Database --------------------------------------------------------------

resource "random_password" "db" {
  length  = 32
  special = false
}

resource "google_sql_database_instance" "db" {
  name                = "${var.app_name}-pg"
  region              = var.region
  database_version    = "POSTGRES_16"
  deletion_protection = false

  settings {
    edition                     = "ENTERPRISE"
    tier                        = "db-f1-micro"
    availability_type           = "ZONAL"
    disk_type                   = "PD_HDD"
    disk_size                   = 10
    deletion_protection_enabled = false

    ip_configuration {
      ipv4_enabled = true # reached only through the IAM-authorised Cloud SQL connector
      ssl_mode     = "ENCRYPTED_ONLY"
    }

    backup_configuration {
      enabled = false # lab data is re-ingestable from CFPB; enable for anything real
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "complaints" {
  name     = "complaints"
  instance = google_sql_database_instance.db.name
}

resource "google_sql_user" "complaints" {
  name     = "complaints"
  instance = google_sql_database_instance.db.name
  password = random_password.db.result
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "${var.app_name}-database-url"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "postgresql+psycopg://complaints:${random_password.db.result}@/complaints?host=/cloudsql/${google_sql_database_instance.db.connection_name}"
}

resource "google_secret_manager_secret_iam_member" "run_reads_secret" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.run.email}"
}

locals {
  image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}/${var.app_name}:${var.image_tag}"
}

# ---- Report API ------------------------------------------------------------

resource "google_cloud_run_v2_service" "app" {
  count               = var.deploy_app ? 1 : 0
  name                = var.app_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.run.email
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.db.connection_name]
      }
    }
    containers {
      image = local.image
      ports {
        container_port = 8000
      }
      resources {
        limits   = { cpu = "1", memory = "512Mi" }
        cpu_idle = true
      }
      env {
        name  = "ENVIRONMENT"
        value = "gcp"
      }
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
      startup_probe {
        http_get {
          path = "/health/live"
        }
      }
      liveness_probe {
        http_get {
          path = "/health/live"
        }
      }
    }
  }

  depends_on = [
    google_secret_manager_secret_iam_member.run_reads_secret,
    google_secret_manager_secret_version.database_url,
    google_project_iam_member.run_sql_client,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.deploy_app && var.allow_public ? 1 : 0
  name     = google_cloud_run_v2_service.app[0].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ---- Scheduled ingest ------------------------------------------------------

resource "google_cloud_run_v2_job" "ingest" {
  count               = var.deploy_app ? 1 : 0
  name                = "${var.app_name}-ingest"
  location            = var.region
  deletion_protection = false

  template {
    task_count = 1
    template {
      service_account = google_service_account.run.email
      timeout         = "1800s"
      max_retries     = 1
      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [google_sql_database_instance.db.connection_name]
        }
      }
      containers {
        image   = local.image
        command = ["complaints-ingest"]
        args    = var.ingest_args
        resources {
          limits = { cpu = "1", memory = "512Mi" }
        }
        env {
          name  = "ENVIRONMENT"
          value = "gcp"
        }
        env {
          name = "DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.database_url.secret_id
              version = "latest"
            }
          }
        }
        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }
    }
  }

  depends_on = [
    google_secret_manager_secret_iam_member.run_reads_secret,
    google_secret_manager_secret_version.database_url,
    google_project_iam_member.run_sql_client,
  ]
}

resource "google_service_account" "scheduler" {
  account_id   = "${var.app_name}-sched"
  display_name = "Cloud Scheduler trigger for ${var.app_name}-ingest"
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_runs_job" {
  count    = var.deploy_app ? 1 : 0
  name     = google_cloud_run_v2_job.ingest[0].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "ingest" {
  count     = var.deploy_app ? 1 : 0
  name      = "${var.app_name}-ingest"
  region    = var.region
  schedule  = var.ingest_cron
  time_zone = "Etc/UTC"

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.ingest[0].name}:run"
    oauth_token {
      service_account_email = google_service_account.scheduler.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }

  depends_on = [google_cloud_run_v2_job_iam_member.scheduler_runs_job]
}

# ---- Budget ----------------------------------------------------------------

resource "google_billing_budget" "lab" {
  count           = var.billing_account == "" ? 0 : 1
  billing_account = var.billing_account
  display_name    = "${var.app_name}-monthly"

  budget_filter {
    projects = ["projects/${data.google_project.this.number}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget_usd)
    }
  }

  dynamic "threshold_rules" {
    for_each = [0.5, 0.8, 1.0]
    content {
      threshold_percent = threshold_rules.value
    }
  }

  depends_on = [google_project_service.apis]
}
