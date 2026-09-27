# Foundation template. NOT applied/tested in a Google project. Creates billable resources.
terraform {
  required_version = ">= 1.8"
  required_providers {
    google = { source = "hashicorp/google", version = ">= 6.0, < 8.0" }
  }
}
provider "google" {
  project = var.project_id
  region = var.region
}
variable "project_id" { type = string }
variable "region" {
  type = string
  default = "us-central1"
}
variable "name" {
  type = string
  default = "open-source-accounting"
}

locals {
  apis = toset(["run.googleapis.com", "sqladmin.googleapis.com", "storage.googleapis.com",
    "secretmanager.googleapis.com", "aiplatform.googleapis.com", "artifactregistry.googleapis.com",
    "cloudscheduler.googleapis.com", "identitytoolkit.googleapis.com"])
}
resource "google_project_service" "apis" {
  for_each = local.apis
  project = var.project_id
  service = each.key
  disable_on_destroy = false
}
resource "google_service_account" "runtime" {
  account_id = "${var.name}-runtime"
  display_name = "Accounting API and worker runtime"
}
resource "google_project_iam_member" "runtime_roles" {
  for_each = toset(["roles/cloudsql.client", "roles/aiplatform.user"])
  project = var.project_id
  role = each.key
  member = "serviceAccount:${google_service_account.runtime.email}"
}
resource "google_storage_bucket" "documents" {
  name = "${var.project_id}-${var.name}-documents"
  location = var.region
  uniform_bucket_level_access = true
  public_access_prevention = "enforced"
  force_destroy = false
  versioning { enabled = false }
  depends_on = [google_project_service.apis]
}
resource "google_storage_bucket_iam_member" "objects" {
  bucket = google_storage_bucket.documents.name
  role = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.runtime.email}"
}
resource "google_sql_database_instance" "postgres" {
  name = "${var.name}-db"
  database_version = "POSTGRES_16"
  region = var.region
  deletion_protection = true
  settings {
    tier = "db-custom-1-3840"
    availability_type = "ZONAL"
    disk_type = "PD_SSD"
    disk_autoresize = true
    backup_configuration {
      enabled = true
      point_in_time_recovery_enabled = true
    }
    ip_configuration { ipv4_enabled = true }
  }
  depends_on = [google_project_service.apis]
}
resource "google_sql_database" "app" {
  name = "open_accounting"
  instance = google_sql_database_instance.postgres.name
}
resource "google_artifact_registry_repository" "containers" {
  repository_id = var.name
  location = var.region
  format = "DOCKER"
  depends_on = [google_project_service.apis]
}
resource "google_secret_manager_secret" "secrets" {
  for_each = toset(["database-url", "stripe-secret", "stripe-webhook"])
  secret_id = "${var.name}-${each.key}"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}
resource "google_secret_manager_secret_iam_member" "runtime_secret" {
  for_each = google_secret_manager_secret.secrets
  secret_id = each.value.id
  role = "roles/secretmanager.secretAccessor"
  member = "serviceAccount:${google_service_account.runtime.email}"
}
output "runtime_service_account" { value = google_service_account.runtime.email }
output "bucket" { value = google_storage_bucket.documents.name }
output "sql_connection" { value = google_sql_database_instance.postgres.connection_name }
output "image_repository" { value = "${var.region}-docker.pkg.dev/${var.project_id}/${var.name}" }
# Create the restricted DB user, secret versions and Firebase email/password configuration
# separately. Never commit secrets or Terraform state. Set a reviewed remote state backend.

# Revocation checks read the current user record. No account-update/config-admin permission.
resource "google_project_iam_custom_role" "identity_reader" {
  role_id = "osaIdentityReader"
  title = "OSA verified identity reader"
  permissions = ["firebaseauth.users.get"]
}
resource "google_project_iam_member" "identity_reader" {
  project = var.project_id
  role = google_project_iam_custom_role.identity_reader.name
  member = "serviceAccount:${google_service_account.runtime.email}"
}
