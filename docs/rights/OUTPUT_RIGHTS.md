# Source output controls — issue #7

This implementation enforces explicitly reviewed output terms and renders required
source notices. It is not a fair-use determination, publisher permission, substantive
review or guarantee against all copyright misuse. No default legal quotation allowance
is invented, and these limits do not change the $89.99/year Agent plan or its unapproved
usage allowance.

## Policy and accounting units

`SourcePolicy.output_control` accepts `mode`, `group_id`, and, for `bounded` mode,
`max_chars_per_response` and `max_chars_total`. Limits are strict nonnegative integers;
a per-response limit cannot exceed the total. `unrestricted` is an explicit reviewed
choice and cannot carry numerical limits. A licensed/reviewed-use source without
valid output terms is denied for model input, quotation, full display and export;
separately granted acquisition/storage operations remain independent. Original and
government-work records may retain their existing reviewed operation grants without
a numerical output cap. No source was assigned real permissions by this change.

The accounting unit is **NFC-normalized canonical JSON characters in the entire
source-dependent content payload**, including its server-supplied notices. This is a
conservative upper bound on source reproduction, not a detector of exact quotations
or a legal conversion from words/pages. A reviewer must explicitly approve these
units and limits for the actual purpose. Do not populate arbitrary numbers or infer
permission from a short passage. When a deliverable uses multiple controlled works,
the whole payload is charged against each work. Generated results, evidence bodies,
source bodies, topic excerpts, editorial body views, memo bodies/revisions and exports
pass through the same ledger. Generated results are reserved before release.

`group_id` identifies the rights holder's work across editions, passage records and
aliases. It is global across users, workspaces, runs and channels. Intake passages
inherit their parent's policy and ancestor controls are included. An independent
reviewer must establish the correct grouping; this system does not automatically
recognize disguised copies, translations or unrelated uploads. That unresolved
cross-corpus provenance work must not be treated as complete reconstruction prevention.

An identical canonical payload is counted once per group, so rereads and repeated
exports of the same memo do not consume another allowance. Different analyses, edits,
fragments and representation payloads add their full sizes. The model-result-to-memo
conversion can conservatively consume another allocation because its payload differs.
There is no calendar reset, per-account reset, or reset on approval. The group binds
its original output terms; a conflicting later group policy is blocked. Legal changes
to a group's limits need a future explicit migration/review workflow and must not be
worked around by inventing a new group for the same work.

Migration `0003_output` creates `source_output_budgets` and `source_output_releases`.
Receipts contain only group ID, payload digest, character count and timestamp, never
a second copy of the body. PostgreSQL upsert/row locks serialize all replicas and
sorted group order avoids inconsistent lock order. SQLite writes serialize local
processes. All reservations and the corresponding release are committed before
response delivery; failure rolls back the transaction. A committed response lost in
transit may remain charged, while its identical retry is idempotent. Retention/backup
restore must preserve the ledger; deleting it would erase reconstruction history.
No reset/delete endpoint is supplied.

Adding output terms to the rights revision changes existing approval digests.
Pre-upgrade bound approvals require independent re-review. No migration manufactures
reviewer approval or carries old authorization forward automatically.

## Required notices

Source and ancestor attribution text, title, publisher, version and URL are supplied
by the server as `source_attributions`. Generated results, evidence, source/topic
views, memo editor and revision history render the notices separately from editable
content. Markdown, HTML, DOCX and PDF exports append current notices. The editable
memo body cannot remove that appended notice. HTML/DOCX/PDF text is escaped by the
existing safe export renderers; browser notice text uses DOM text nodes. Registered
source-backed exports cannot omit their current authorized database session.

Existing permission checks still apply independently at model input and each output.
A quota does not grant an operation, source seat, workspace membership, technical
approval or historical applicability. Model requests already transmitted cannot be
recalled, and this ledger does not delete delivered files from user devices.

## Validation and remaining gates

See `reports/output-rights/` and `progress.md` for observed tests, including output
limits, retries, shared editions, source revision invalidation, all four export
formats, rollback and real PostgreSQL process races. All data, licenses and reviewers
in those tests are synthetic. The local Topics page displayed a required synthetic
notice as literal text with zero script elements in its notice container. Browser
activation of the source-inspection dialog did not produce a dialog or diagnostic;
that interaction is unverified and remains a #35 UI follow-up. API source/evidence
and export behavior is covered by the backend tests.

Still open: real grouping/terms/counsel evidence, verified seats/retention/jurisdiction,
independent content/applicability review, manual-upload/cross-corpus provenance and
reconstruction attacks, full derived-data deletion, broader UI validation, live
provider and GCP deployment. Restricted grants must not be enabled merely because
these synthetic tests pass.
