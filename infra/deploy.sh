#!/usr/bin/env bash
# Reviewed deployment template. No cloud calls were executed in the handoff.
set -euo pipefail
: "${DEPLOY_APPROVED:?Set DEPLOY_APPROVED=yes after reviewing resources and costs}"
[[ "$DEPLOY_APPROVED" == yes ]] || exit 1
: "${PROJECT_ID:?}" "${REGION:?}" "${IMAGE:?}" "${RUNTIME_SERVICE_ACCOUNT:?}"
: "${SQL_CONNECTION:?}" "${DATABASE_SECRET:?}" "${RUNTIME_ENV_FILE:?}"
NAME=${NAME:-open-source-accounting}
if grep -q 'REPLACE_' "$RUNTIME_ENV_FILE"; then echo 'Replace all runtime placeholders.' >&2; exit 1; fi
# Scanner reachability/private networking must be separately configured for your environment.
# Supply any reviewed --network/--subnet or --vpc-connector flags in CLOUD_NETWORK_FLAGS.
read -r -a NETWORK_ARGS <<< "${CLOUD_NETWORK_FLAGS:-}"
COMMON=(--project "$PROJECT_ID" --region "$REGION" --image "$IMAGE"
  --service-account "$RUNTIME_SERVICE_ACCOUNT" --set-cloudsql-instances "$SQL_CONNECTION"
  --env-vars-file "$RUNTIME_ENV_FILE" --set-secrets "DATABASE_URL=${DATABASE_SECRET}:latest")
gcloud run jobs deploy "${NAME}-migrate" "${COMMON[@]}" "${NETWORK_ARGS[@]}" \
  --command python --args=-m,alembic,upgrade,head --max-retries 0 --task-timeout 600s
# Do not execute a migration without database backup and explicit approval.
: "${MIGRATION_APPROVED:?Set MIGRATION_APPROVED=yes after backup and migration review}"
[[ "$MIGRATION_APPROVED" == yes ]] || exit 1
gcloud run jobs execute "${NAME}-migrate" --project "$PROJECT_ID" --region "$REGION" --wait
gcloud run jobs deploy "${NAME}-worker" "${COMMON[@]}" "${NETWORK_ARGS[@]}" \
  --command python --args=-m,app.worker,--once --tasks 1 --max-retries 0 \
  --task-timeout 3600s --memory 2Gi --cpu 1
gcloud run deploy "$NAME" "${COMMON[@]}" "${NETWORK_ARGS[@]}" \
  --port 8080 --memory 2Gi --cpu 1 --concurrency 16 --max-instances 3 \
  --timeout 180s --no-allow-unauthenticated
printf '\nDeployed privately. Test first; intentionally configure public invocation and production auth later.\n'
printf 'Configure a Scheduler service account to invoke %s-worker via jobs:run.\n' "$NAME"
printf 'No Scheduler job, public IAM binding, domain, scanner, or payment activation was created by this script.\n'
