# Durable model attempts — #26 / parent #5

Every application chat and Agent model step now commits a pending receipt before
calling the provider. Settlement uses a separate transaction before returning an
answer to the caller. The receipt survives later source checks, output-policy
failure, cancellation, job failure and application rollback. Failure to create
the receipt prevents dispatch; failure to settle withholds the answer and leaves
an explicitly unresolved receipt. No historical token usage is invented.

## Recorded facts and privacy

`model_attempts` records an opaque operation hash, nullable user/workspace/chat/run
references, execution ID/revision, phase, configured provider/project/location/model,
resolved model version when supplied, prompt version, thinking/output settings,
timestamps, safe outcome/error category, HTTP status, validated token counters and
a dated standard-rate estimate. It stores no prompt, response, document, title,
email, credential, source excerpt, request-body hash or raw provider error.

Known usage from an HTTP 200 is retained even when schema or output validation
fails. Reasoning tokens are included by the existing dated estimator. Missing or
invalid usage after a potentially billed request remains unknown. Explicit
pre-dispatch failure or a non-200 response is distinguished from an ambiguous
timeout. Mock receipts are labeled mock, never live Cloud measurements. See
[the verified contract and pricing sources](GEMINI_CONTRACT.md).

The receipt's cost date is the UTC application start date. Amounts are estimates,
not invoice reconciliation, and price-boundary/clock differences still require
provider billing evidence. An unresolved process death has no invented finish
time, zero-dollar assumption or automatic expiry. No generic TTL can prove that
a provider did not charge for a request.

Deleting a chat sets its receipt reference to null. Other parent foreign keys
also use SET NULL; deleting a result cannot silently erase provider costs.
Receipts still contain operational/pseudonymous metadata and are **not anonymous**.
Account erasure, private receipt retention, invoice reconciliation and operator
retention approval remain separate work; this change makes no indefinite-retention
or zero-retention promise. No public receipt listing or mutation API is added.

## Retries and worker recovery

The database's unique operation hash owns dispatch. Agent keys bind run/execution
and one of planning, synthesis, verification, correction or reverification. A
confirmed start/restart creates a new execution ID; a repeated HTTP idempotency
key does not. Worker lease recovery keeps that execution ID and cannot repeat a
previously recorded phase, including a pending phase with unknown cost. The job
fails with `MODEL_ATTEMPT_ALREADY_RECORDED` rather than issuing another call.
Restart also clears the old worker lease owner so it cannot release into the new
execution. Source, workspace and subscription checks still precede every call.

A caller can explicitly start a failed run again, subject to existing admission
and rights checks. This may incur additional provider cost. It does not reuse a
stored model reply: replies are intentionally absent from this ledger. Durable
stage-result recovery, budget reservations, approved retry policy and in-flight
cancellation still need implementation. This receipt layer is not a hard spend
cap and does not change the annual price or approve a monthly task allowance.

## Operational report

`GET /api/v1/admin/model-usage?start_at=<UTC epoch>&end_at=<UTC epoch>` requires an
authenticated operations administrator; members and rights approvers cannot
read it. Windows are positive, end-exclusive and at most 31 days. Each attempt
window and complete Agent cohort is bounded to 10,000 rows; larger reports fail
explicitly instead of silently truncating a cost total.

The report returns known estimated subtotal and unresolved/pending/mock counts.
It returns no complete total while a live cost is unknown. The Agent cohort
contains tracked runs whose first live receipt starts in the selected window,
including their later attempts outside that window. All failed/cancelled/retried
attempts for those runs contribute costs. The denominator is the number of those
runs currently completed with limitations. Zero completions, active runs,
unknown costs or orphaned Agent receipts withhold the cost-per-completion ratio.
Deleted-run receipts still contribute to the attempt-window subtotal; they cannot
silently improve the completion ratio. Mock and legacy untracked runs are excluded.

PostgreSQL uses a fresh repeatable-read snapshot; SQLite explicitly begins its
read transaction. A concurrent job completion cannot be combined with an older
cost snapshot. Typed response schemas are exported in `docs/openapi.json`.
Numbers are model-only estimates: infrastructure, billing differences and human
review costs are excluded. This endpoint does not make billing, quality or
professional-approval assertions.

## Migration and remaining work

`0007_attempts` adds the receipt table and nullable run execution ID, preserving
all prior rows. Existing queued jobs without an execution ID use a stable legacy
revision key; new confirmed starts receive an ID. No backfill or approval grant
is generated. Migration downgrade removes receipts, so production rollback must
preserve/export accounting records under an approved recovery procedure; the
round-trip test only uses an empty disposable database with synthetic fixtures.

Next: approved, immutable operator budget records and atomic admission/reservations
against known plus unresolved liabilities; bounded retry/backoff/total deadlines;
documented reconciliation of unknown outcomes and actual invoice costs. Keep
default mock mode and all paid calls/resources disabled until authorized staging.
The GCP project, approved region/spend, identity, retention evidence and live model
acceptance are still missing. Continue independent all-family content work under
#8 while those operator/reviewer gates remain.
