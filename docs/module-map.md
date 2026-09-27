# Module map and extension guide

| Capability | Backend | Frontend |
|---|---|---|
| Environment safety | `config.py`, `main.py` | `main.ts` banners |
| Accounts/auth | `auth.py`, `api/core.py` | `api.ts` identity/refresh, `main.ts` sign-in |
| Roles/workspaces | `models.py`, `api/workspaces.py` | `views/work.ts` |
| Free chat | `api/chats.py`, `providers/gemini.py` | `views/chat.ts` |
| Agent products | `agents/catalog.json`, `catalog.py` | `views/research.ts` |
| Intake/CRUD | `schemas.py`, `api/runs.py` | `views/research.ts` wizard |
| Jobs/orchestration | `worker.py`, `agents/orchestrator.py` | run status and polling |
| Prompt contracts | `agents/prompts.py`, `schemas.py` | typed result rendering |
| Retrieval | `services/retrieval.py`, `source_gateway.py` | evidence/source cards |
| Rights | `services/rights.py`, `api/sources.py` | source admin/evidence labels |
| Documents | `services/documents.py`, `parse_worker.py`, `storage.py` | documents/upload dialog |
| Verification | `agents/verification.py` | limitations and claims |
| Calculations | `agents/calculations.py`, `workflows.py` | task forms/results |
| Memo revisions/export | `api/memos.py`, `services/memos.py` | Markdown editor/reviews |
| Paid gates/usage | `services/entitlements.py`, `idempotency.py` | pricing/upgrade/usage |
| Payments | `api/billing.py`, `services/billing.py` | `views/billing.ts` |
| Watches | `services/watches.py`, `api/watches.py` | `views/library.ts` |
| Source/role onboarding | `admin.py` | source administration |
| Migration | `alembic/versions/0001_v040.py` | not applicable |

## Workflow extension pattern

1. Add a workflow with a stable ID in `agents/catalog.json` (copy an existing shape).
2. Specify distinct input requirements, output sections and accounting guardrails.
3. Add input validation/deterministic work in `agents/workflows.py`. Never use model text as code.
4. Add typed schema constraints, then specific intake/result components where needed.
5. Keep acquisition through the rights-filtered retrieval service. Payment does not authorize a source.
6. Add tests for missing facts, no evidence, unsupported conclusions, access changes and expiry.
7. Default new workflows to experimental until separately evaluated.

The shared orchestrator intentionally avoids 16 duplicated agent implementations. Specialization
lives in workflow contracts, prompt instructions, schemas, deterministic tools and task-specific UI.
Mock execution validates plumbing, not the correctness of any workflow's accounting analysis.

## Current pipeline

`draft → queued → planning → retrieving → analyzing → verifying → completed_with_limitations`

An active run can be cancelled; invalid/inaccessible evidence can block release. Failure settles
its reservation as released. The worker checks entitlement and rights at checkpoints and release.
Planning/synthesis use bounded structured model responses; the server owns retrieval and checks.

## API and contracts

`docs/openapi.json` is generated from the running code; it is the authoritative route/request
contract for this handoff, not the older v3 design API. `analysis.schema.json` and
`research-plan.schema.json` are the actual model-response schemas.

Database JSON fields store typed application snapshots. Source text lives only where storage is
allowed. Production users must use migrations. SQLite is for local development; locking semantics
must be load-tested against the actual production PostgreSQL service.


## v0.6.0 content and publication additions

| Capability | Files |
|---|---|
| Original guides, cases, templates, playbooks, study questions | `content/` |
| Item integrity, references, search, unapproved staging CLI | `backend/app/content.py` |
| Public library endpoints and technical-review API | `backend/app/api/library.py` |
| Secondary-content technical gate and hash revalidation | `backend/app/services/rights.py`, `retrieval.py` |
| Library listing, reader, and reviewer UI | `frontend/src/views/open-library.ts` |
| Safe limited Markdown rendering | `frontend/src/markdown.ts` |
| Content consistency and arithmetic checks | `scripts/check_content.py` |
| Isolated browser rendering checks | `scripts/test_library_components.py` |
| Publication manifest and heuristic secret scan | `scripts/release_preflight.py` |
| New public repository creation with authenticated user CLI | `scripts/publish_github.py` |
| Code/content licenses, contributions, security boundaries | `LICENSE`, `content/LICENSE.md`, `NOTICE.md`, `CONTRIBUTING.md`, `SECURITY.md` |

New API routes are `/api/v1/library`, `/api/v1/library/{item_id}`,
`/api/v1/editorial/sources`, and `/api/v1/editorial/sources/{source_id}/review`.
The first two are public and do not require a subscription. Technical review is
restricted to an explicitly assigned role; rights approval remains a different
role/action. No database migration is required for the new content policy fields,
which use the existing JSON column and existing user-role string column.
