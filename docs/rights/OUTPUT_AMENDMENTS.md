# Reviewed output-term amendments (#7)

This workflow changes a registered work group's limits while preserving its cumulative accounting. It cannot create a license, reset usage, move work to another group, approve content, renew a seat or replace a counsel decision. No actual rights amendment is included in this release.

## Prepare and review

A scoped administrator reads `GET /api/v1/admin/output-groups/{group_id}/amendments`. The response includes current terms hash/revision, accumulated canonical-character count, registered source metadata/revisions, a source-set digest and prior amendment records. It exposes no source body. The administrator submits on the same path with expected terms hash/revision and source-set digest, typed new `OutputControl` terms using the **same group ID**, an opaque restricted evidence reference/hash, and a mandatory review deadline. The proposal snapshots the registered source set and the count at submission. Unchanged terms and reset/regrouping fields are rejected.

A different `rights_approver` reviews the actual restricted authorization and proposed accounting units, then posts `/amendments/{id}/review` with the exact record digest, the **current** expected release count, an apply/reject decision and explicit actual-review/counter-preservation attestations. Neither the submitter nor an author of an affected source may approve. A changed count, work/source revision, source set, term revision or expired review deadline rejects application until the reviewer reloads the changed state. A rejected or applied proposal cannot be replayed. The review deadline limits when this one-time transition can be applied; underlying source-license effective/expiry dates remain unchanged and independently enforced.

All routes use server-side account/MFA checks; mutations require recent authentication. Private evidence stays in the restricted review system. Stored references/hashes are attested by the actual authorized reviewer, not fetched or independently authenticated by this API. Operator identities, qualifications, private evidence and a dedicated review UI remain prerequisites/work outside these synthetic tests.

## Apply without resetting history

Application locks registered sources in ID order, then the shared group ledger and proposal. In one transaction it:

1. Rechecks the full review snapshot, deadline and current usage count.
2. Changes the ledger's limits hash and increments its monotonic `terms_revision`.
3. Replaces output terms on all registered group sources, increments each source policy version and withholds its reviewed status.
4. Records actor, timestamp, applied terms revision and unchanged character count.

It never edits or deletes `released_chars` or any release receipt. Existing hashes/counts/timestamps survive, including transitions to explicit unrestricted rights terms. Unrestricted rights terms are unrelated to the Agent product's unapproved usage allowance. They still accumulate release counts so a later bounded policy does not start from zero.

Every affected source requires independent source-rights re-review. The reviewer must inspect the group's applied amendment and its restricted evidence alongside the underlying source agreement. Counsel and user/workspace scope records bound to the prior revision cannot be reused. Technical annotations are preserved rather than fabricated; unchanged prose does not acquire a new technical review. Intake descendants bound to an older parent policy remain withheld and require the intake version/review workflow. Saved evidence tied to older source versions remains withheld. There is no automatic approval or automatic restoration of historical artifacts.

A lower total may be below already released content. History remains unchanged, and further output—including identical retries—is withheld while historical usage exceeds the current total. When history is within the limit, identical payloads remain idempotent, subject to the current per-response limit. New unique output consumes the existing remaining balance. A decrease cannot recall transmitted text or user downloads.

For a group without a ledger, the first proposal initializes zero usage only when its existing source controls agree; it creates no source approval. Existing ledgers are never recreated or zeroed. A previously unregistered or concurrently joining source with old terms conflicts with the current ledger and cannot obtain model-input/quote/display/export permission merely through its old per-source approval. Work-group identity/alias detection beyond registered sources remains a separate provenance task; do not create a new group ID as a workaround.

## Races and storage

Bulk Topics/editorial reader responses reserve the complete response batch under globally ordered source/group locks, avoiding inverse lock order between individual items. Output release also locks source rows before group rows and compares the caller's authorized snapshot with fresh source revision/status. A pre-amendment caller cannot publish after terms change, including an A→B→A transition. Model/quote/display/export permission checks compare per-source terms with the current ledger before use. An already transmitted provider request cannot be recalled; existing checkpoint and output controls withhold subsequent work/output after a change.

A concurrent release either commits before amendment (so the expected usage check detects drift) or loses to the amendment (so its stale source snapshot is rejected). Competing amendments cannot both apply from the same term revision. PostgreSQL serializes on row locks; SQLite acquires its write lock before source mutation. There is no counter-delete/reset endpoint. Backup/restore, retention and physical deletion designs must preserve this reconstruction history.

Migration `0006_amendments` adds amendment history and initializes the existing ledger's term revision to one without touching counters or receipts. The CI migration check now creates a synthetic ledger at `0005_scopes`, upgrades, verifies exact preservation, then performs schema parity and full downgrade/re-upgrade checks on the disposable database.

## Validation and remaining scope

`reports/amendments/` and `progress.md` contain actual commands/results for ledger preservation, source/counsel/scope invalidation, increases/decreases/unrestricted transitions, stale/replayed/expired proposals, identity separation, privacy and PostgreSQL races. All records and reviewers in these tests are synthetic.

Actual work grouping, licenses/counsel/entitlement evidence, public/service context, cross-corpus provenance, physical deletion/retention, complete content review/indexing, administration UI, live provider verification and GCP deployment remain open. No numerical limit or passing test is a legal safe harbor or independent human approval.
