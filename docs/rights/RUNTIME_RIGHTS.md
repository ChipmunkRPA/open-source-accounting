# Runtime permission checks — issue #7

This slice carries trusted source scope through Agent retrieval, every structured
model call (including correction and verification), saved evidence, results and memo
exports. It does not grant any license or approve any content.

## Trusted context

The authenticated API session stores the verified actor ID and server settings in
SQLAlchemy session info. The worker uses the run's execution owner and server settings.
`runtime_context` checks current workspace membership; worker checkpoints additionally
require an owner/editor role and current Agent entitlement. Output readers use their
own verified membership, so a remaining collaborator can read an authorized retained
artifact even after the execution owner leaves. Source permissions still apply.

| Scope | Trusted origin / behavior |
| --- | --- |
| `workspace_id` | The persisted run workspace, checked against current membership |
| `route` | Server constant `hosted_agent` for this application lane |
| `audience` | Server constant `workspace` |
| `provider` | Configured `model_provider`, never a prompt or client field |
| `region` | Configured `model_location`; this does not prove endpoint availability |
| `seat_id` | Verified per-source/user/workspace assignment; membership/payment alone is insufficient |
| `retention` | Verified assignment bound to configured provider/project/region/model; actual provider/storage review remains required |
| `jurisdiction` | Verified assignment; user-supplied accounting jurisdiction is not trusted |

Absent scope values deny a corresponding scoped grant. No client `Run.context`,
workflow inputs, header or generated plan can assert one of these rights. Explicit
service callers may pass an already server-derived context; it is not an HTTP input.
Public library display and intake are separate routes with separate permissions.
Intake keeps its `official_http`/`internal_ingestion` context. A rights policy covering
multiple routes must explicitly allow them; this code does not widen a grant.

## Provider boundary

Every structured Agent call opens a fresh database transaction before transmission,
checks the job owner/cancellation, current edit membership and subscription, then
rechecks source-operation rights and the recursive saved-memo dependency chain.
The selected in-memory evidence must match persisted evidence, its current source
body/policy version or its selected document's current chunk and locator. Reference
metadata cannot contain body text under a `reference_only` label.

A fingerprint binds preprocessed documents and input memos to the versions actually
examined. Changed input content stops the next call or output release. Selected
files are checked even when absent from the bounded retrieval subset, because a
comparison/workpaper may still contain deterministic data from them. Output reads,
evidence views, memo access and export also recheck the current permissions. Parent
source changes and previously implemented policy-version revocation remain effective.

These are checks immediately before each request, not a distributed transaction with
the provider. A request already transmitted cannot be recalled after a concurrent
revocation. No claim of zero race interval or provider deletion is made. Provider
retention and physical removal of derived data remain separate unfinished work.
The free-chat lane has no registered-source retrieval and is unchanged here.

## Tests and remaining gates

`backend/tests/test_runtime_rights.py` uses synthetic original sources, review
attestations and a deterministic mocked provider. It exercises successful correction,
revocation/expiry at all post-retrieval boundaries, membership changes before and
between calls, trusted/mismatched scopes, document/memo revision changes, metadata
body smuggling, current-viewer access and cross-workspace document rejection.
These tests are not professional review, live inference, or proof of a license.

Still required: actual publisher/provider/jurisdiction evidence, reviewed output-limit
amendments, public/service context records, broader provenance and reconstruction
defenses, revocation/deletion across all caches/indexes and article dependencies,
independent content/applicability reviews, actual endpoint and live deployment validation.
See `progress.md` for current commands and counts.

Subsequent slices implement [counsel decisions](COUNSEL_RECORDS.md), [output accounting/notices](OUTPUT_RIGHTS.md) and [verified user/workspace scopes](VERIFIED_SCOPES.md). Earlier observations above are historical validation, not new test results. Actual provider evidence, output amendments, public/service scope, cross-corpus provenance and physical deletion remain open.
