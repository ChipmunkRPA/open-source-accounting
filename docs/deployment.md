# Deployment procedure and boundaries

## Local Docker

`docker compose up --build` builds the UI/API image and starts an API plus separate polling worker
with shared local storage. It binds to 127.0.0.1:8000 and uses only mock/dev modes. Docker was not
available for validation in the authoring environment. Validate volume permissions and healthcheck
behavior on your machine. Do not reuse local settings for a publicly reachable service.

## Google Cloud target

The deployment design is a Cloud Run API service + PostgreSQL-backed durable queue + Cloud Run
worker Job. The worker's `--once` mode drains currently available work and exits. A reviewed
Cloud Scheduler job can invoke `jobs:run` (OAuth service-account authentication) on a cadence.
This implementation does not secretly run a persistent process after an HTTP response. Scheduled
execution introduces waiting time; immediate queue-driven launch is future work.

1. Review source/provider rights, privacy, authentication, storage retention, usage limits and costs.
2. Create a Google Cloud project with billing and verify Gemini 3.8 Flash access in the chosen location.
3. Review/initialize `infra/main.tf`. It creates billable foundation resources only; it has not been
   applied or provider-validated here. Pin a reviewed provider version and a secured state backend.
4. Provision a restricted PostgreSQL user, database credentials/secret versions, Firebase email/password
   auth, and private reachable malware scanner. Do not put database passwords in Terraform variables/state.
5. Build/push the Docker image through your approved CI/Artifact Registry pipeline. Vulnerability-scan it.
6. Set a database secret to a URL like `postgresql+psycopg://USER:URL_ENCODED_PASSWORD@/open_accounting?host=/cloudsql/PROJECT:REGION:INSTANCE`.
   The runtime service account needs Cloud SQL connection rights and database-level credentials. Verify
   pool/connection behavior; this handoff used SQLite, not a live PostgreSQL instance.
7. Configure environment values from `runtime.env.yaml.example`; inject database and payment secrets
   through Secret Manager. Keep billing disabled. Configure correct app origin/CORS, not wildcard origins.
8. Configure scanner private-network connectivity for both service and jobs. The template does not
   create or secure a ClamAV deployment, VPC connector, subnet, or monitoring for it.
9. Back up the DB; run the reviewed initial migration. Deploy the API/job templates privately first.
10. Test live Firebase, GCS, Gemini, scanner, task lease/recovery, exports and deletions. Provision source
    administrators with `python -m app.admin`; independently approve original/licensed content.
11. Add Scheduler IAM/job invocation, alerts and backup/restore procedures. Validate long-running jobs,
    overlapping scheduled executions, idempotency, instance caps and database connection limits.
12. Test Stripe in test mode: all success/failure/cancellation/refund/recovery paths, real webhook
    signatures, correct API version, price and invoice shape. Publish actual purchase and privacy terms.
13. Conduct production security, accessibility and technical-accounting evaluation. Only then enable
    public invocation, configure the domain and activate paid subscriptions with approved limits.

`infra/deploy.sh` intentionally does not add public IAM, enable payments, create a Scheduler job, or
configure scanner networking. It requires explicit approval environment variables and valid existing
resources. Its Cloud CLI commands were checked against official documentation but not executed.

## Rollback and recovery

Keep immutable image tags and versioned migrations. Roll back application images only when the old
code is compatible with the current schema. Do not downgrade production migrations blindly. Test
restoration from backups; ensure deletion promises include backup expiration. Worker retry/leases
are bounded but cannot guarantee exactly-once model charges. Source disable blocks dependent new
reads/exports but is not a complete legal retention/purge tool for every previously stored artifact.

## Unimplemented deployment work

Cloud Tasks adapter, private networking/scanner resources, central log redaction policy, audit export,
budget alert automation, penetration testing, CI dependency lockfiles, external email delivery,
comprehensive disaster recovery, and multi-region failover are not implemented in this handoff.
