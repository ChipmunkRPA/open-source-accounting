# Verified source scopes (#7)

Source-operation permission, publisher-seat entitlement, jurisdiction and provider retention remain separate from workspace membership and Agent payment. This implementation adds immutable, independently approved user/workspace scope records. No actual publisher seat or jurisdiction/retention approval is included in the release.

## Operator workflow

Start with an independently approved source policy. If it restricts `seat_id`, `jurisdiction` or `retention`, an administrator submits `POST /api/v1/admin/sources/{source_id}/scope-grants` with:

- Exact rights revision and policy version, subject user and existing workspace membership.
- Every protected scope required by that source, with each value inside its approved policy. Partial grants cannot be combined to manufacture a complete assignment.
- Explicit operations, limited to operations the source policy grants. The assignment can narrow those operations.
- Explicit model provider, Cloud project, region and model ID, plus an effective timestamp and mandatory expiry.
- An opaque `ev_…` reference and SHA-256 for the operator's restricted verification evidence. Do not submit publisher passwords, session tokens, license text, legal advice or client documents.

A different authorized `rights_approver` must verify the actual evidence, use the exact record digest and attest `confirm_actual_entitlement_verification` at `/scope-grants/{id}/approve`. The source author, grant submitter and beneficiary cannot approve the assignment themselves, including after a role change. The API does not fetch or independently validate the evidence file or professional qualifications. Operator identity/provisioning and actual evidence remain prerequisites.

Routes require server-verified signed-in identity and MFA; changes require recent authentication. Only scoped administrators can inspect records or revoke them. Restricted GET responses include source policy and grant metadata but not source text. The dedicated administration UI remains work under #35; OpenAPI defines the request/response routes.

Only one approved assignment may exist for a source/user/workspace. Approval atomically supersedes the previous record under a source-row lock and a partial unique index on both PostgreSQL and SQLite. Superseded/revoked records cannot be reapproved. A future-effective replacement withholds access until its effective time; it does not keep the previous assignment silently active. Revocation is idempotent and does not change the global source policy or another collaborator's grant. Renewals and replacements require a new independent verification; they do not reset cumulative output ledgers.

## Runtime boundary

Protected values are resolved on each existing source-operation check from one fresh database record. The internal runtime context binds the database session, server-selected actor, current workspace membership and server settings. Plain dictionaries, run context, input fields, subscription status, detached source objects and copied contexts cannot supply these protected values. Scope records are reloaded even in a long-lived worker session.

The record must match work/revision/version, actor, workspace, requested operation, approval separation, integrity digest and time interval. Current configured provider/project/region/model must match exactly. Changing any of them withholds access until new verification. Scope values never substitute for the source-operation Boolean grant, counsel decision, technical/applicability approval, membership or subscription gate. Retrieval, every structured model call, source evidence, saved result, memo and export paths use the same checks.

Saved artifact access uses the current viewer's assignment. An owner losing a seat cannot borrow a collaborator's grant, and a remaining licensed collaborator need not lose access just because the original run owner lost theirs. Fresh AI work still requires Agent and editing authority; retained artifacts still follow current source rights independently of subscription expiry.

The current assignment route is `hosted_agent`, audience `workspace`. Anonymous public reads and intake/service contexts do not borrow a user assignment. A source requiring protected context stays reference-only in those paths until separately verified public/service scope is implemented. Neither request accounting jurisdiction nor a user IP is treated as verified legal scope.

## Limits and remaining gates

An attested retention label bound to a model/project is not remote-provider retention enforcement or a completed privacy review. Actual provider endpoint/SDK/settings/terms, retention behavior, region availability, requested `gemini-3.8-flash` availability and costs remain under #26/#28/#29. Records expire or can be revoked when that evidence changes; the app does not silently infer new contract terms. Storage deletion schedules, historical grants, audit retention and backup policies remain #34/#38 work.

No publisher login, license purchase, real reviewer approval, source acquisition, live model or deployment occurred. Synthetic test grants do not authorize production content. Public metadata and general audit details omit private evidence references and scope values; the database and privileged record API remain private operational data.

Cross-corpus aliases, disguised copies, broader provenance, output-limit amendments, service/public scope records and physical derived-data deletion remain open. A provider request already sent and a user download cannot be recalled by revoking a row.
