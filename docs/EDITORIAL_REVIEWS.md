# Technical review records (#23)

Rights, technical correctness and historical applicability are separate decisions. A content import or model pass cannot supply an independent human review. Original commentary remains commentary after technical approval.

An assigned technical reviewer opens **Content review**, inspects the source and listed reference limitations, and records a decision against the displayed revision. The source author cannot review their own submission. Independent rights approval comes first; approval also requires current permission to inspect the full source body. Real accounts continue to require server-verified email and MFA. Local demonstration identities are test fixtures only.

Each decision requires a scope, findings, a private supporting-record identifier (`ev_…`) and SHA-256, an explicit future expiry, checked reference IDs and an attestation that the review actually occurred. The identifier/hash binds the submitted assertion; it does not prove the supporting document exists, verify a license or establish reviewer competence. Keep the actual evidence in an approved private channel. Do not put confidential legal advice or restricted source text in public issues.

`POST /editorial/sources/{id}/review` accepts approved, changes_requested, rejected or revoked. Approved decisions must address every listed reference. The service checks policy version, actual body hash and a canonical revision containing title, publisher, URL, edition, framework, kind, reference IDs and retained citation/provenance fields. Referenced publication bodies are not automatically fetched or reviewed. Applicability dates have their own review and are excluded from the technical fingerprint.

Decisions append to `editorial_reviews`; there is no edit/delete API. Each new decision increments the source policy version and replaces the current-record pointer while preserving prior records. Source-row locks prevent a stale concurrent decision overwriting a newer decision. Corrections require another decision against the current revision. Revocation or expiry immediately denies uses that require technical approval. The runtime also checks the selected record's payload hash, source binding and revision. This is application-level immutable history, not a cryptographically signed or database-administrator-proof archive.

**Review history** calls `GET /editorial/sources/{id}/reviews`, returning the latest 100 records. It requires a technical-reviewer role and current full-display permission; the output-rights ledger also applies because findings may quote a source. Findings are stored in the private ledger instead of public source-policy metadata. Disabled sources are inaccessible through this view.

Migration `0010_editorial` adds the ledger. It does not backfill approval records from old flags: a legacy approved flag alone no longer permits Agent use or SEC applicability approval. Real reviewers must submit fresh revision-bound records. Public educational display remains a separate rights-controlled operation. Apply the normal Alembic migration before running the new API.

Remaining #23 work includes reviewer evidence packets, linked-reference revision snapshots, parser decisions, broader applicability workflows, coverage reconciliation and independent human reviews. The synthetic tests and UI fixture do not advance real-content approval counts.
