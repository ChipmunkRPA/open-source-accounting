# Progress — Open Accounting v0.5.0

**Snapshot:** September 27, 2026. This records completed work and remaining tasks,
not scheduled/background development. Prior detail is preserved in
[docs/archive/progress-v0.4.md](docs/archive/progress-v0.4.md).

## Product decisions retained

- [x] General AI chat remains free of subscription charges.
- [x] Agent work requires **US$89.99/year** in the hosted-service configuration.
- [x] Reading/downloading the original library does not require an Agent subscription.
- [x] Gemini 3.8 Flash remains the configured live model; mock is the safe local default.
- [x] Payment, source rights, workspace access, and technical content approval are independent.
- [ ] Approve production quotas/terms. The 30-task monthly cap remains a proposal.

## Content release — built, not professionally approved

| ID | Deliverable | Status | Next work |
|---|---|---|---|
| CONTENT-01 | 14 original research guides | Drafted with provenance and limitations | Independent technical review |
| CONTENT-02 | 5 fictional worked cases | Drafted; stipulated arithmetic checked | Accounting/applicability review |
| CONTENT-03 | 6 reusable templates | Drafted | Practitioner usability review |
| CONTENT-04 | 16 task-specific Agent playbooks | Drafted; core/experimental labels retained | Evaluate actual workflow outcomes |
| CONTENT-05 | 30 Q&A records plus readable guide | Drafted, not gold-standard labels | Review every answer before benchmark use |
| CONTENT-06 | 22 source/license reference records | Metadata and links only | Ongoing source/version/access review |
| CONTENT-07 | Manifest, hashes, cross-references | Implemented and tested | Expand content without changing immutable versions |
| CONTENT-08 | Public original-content license | CC BY 4.0 notice included | Contributor license/provenance diligence |
| CONTENT-09 | Full primary accounting/audit corpus | **Not included** | Obtain/review rights and acquire permitted sources |

There are **42 library items and approximately 16,800 words**. All are AI-assisted
editorial drafts. A source page examined for background is not equivalent to
verification of current ASC paragraphs. No current ASC/IFRS text is bundled or
represented as directly verified. No real technical reviewer has approved this pack.

## Content functionality

| Module | Implementation | Validation |
|---|---|---|
| Public reader/search | Public API, filters, pagination, body/source detail | API and component tests |
| Markdown reader | Safe DOM nodes; no HTML execution or remote images | Component HTML/link safety check |
| Original Markdown download | Browser download control, no paywall | Code/typecheck; live download navigation not tested |
| Import CLI | Idempotent, immutable versions, all sources staged unapproved | Unit tests and local staging |
| Rights approval | Existing independent rights-approver route | Current regression tests |
| Technical review | Separate role, explicit action, sources checked, note/hash/version | Review-gate and role tests |
| Agent admission | Blocks pending review and changed content hashes | Retrieval and policy tests |
| Database | Uses existing Source policy JSON and User role columns | SQLite test suite; no new migration required |
| Container content mount | Content copied and CONTENT_DIR configured | Template updated, Docker not built |

Public release files retain their release review status. Database approvals do not
silently rewrite those files. Publish a new reviewed content version when actual
editorial review is completed.

## Existing application baseline

The v0.4 free chat, workspaces, document parsing, memo revisions/exports, durable
worker, mock/live provider boundary, subscription rules, billing adapters, and
experimental workflows are retained. The complete backend regression suite runs
against this combined release. The initial live-provider, production-auth, payment,
PostgreSQL/concurrency, source-ingestion, and deployment limitations remain open.

## Validation executed in this release

- [x] **155 Python tests passed**: the original 100 regression tests, 39 content/
  review tests, and 16 publication-script tests.
- [x] Application statement coverage: approximately **81.6%**. This is not a
  security audit or accounting-accuracy score.
- [x] TypeScript typecheck and compiled frontend build passed.
- [x] **11 offline library-component checks passed**: listing, pagination, filters,
  empty state, tables, provenance, draft status, mobile overflow and inert markup.
- [x] Library/manifest integrity, Q&A references and stipulated arithmetic checked.
- [x] API schemas regenerated: **53 paths / 64 operations**.
- [x] Release preflight and exact-manifest publisher dry-run prepared/tested.
- [ ] Clean dependency install / dependency vulnerability audit.
- [ ] Normal deployed-origin browser E2E, auth, checkout and download testing.
- [ ] Live Gemini, Firebase, Stripe, GCS, Postgres and Google Cloud tests.
- [ ] Human accounting review and adjudicated accounting benchmark.

Evidence: `reports/content-tests.log`, `reports/content-tests.xml`,
`reports/content-coverage.json`, `reports/content-validation.json`,
`reports/library-components.json`, and `reports/library-*.png`.

Browser navigation to local URLs was blocked by environment policy. No policy was
changed. The new UI checks render compiled components with a local content fixture,
not a deployed server session. A direct Python HTTP smoke check reached the library
API successfully. The publication script's GitHub writes were **mocked only**.

## Open-source packaging and GitHub status

- [x] MIT license for application code; CC BY 4.0 for original educational content.
- [x] Notice, contribution guide, security status, issue/PR templates and CI updates.
- [x] File manifest and heuristic checks for common secrets, sensitive filenames,
  unwanted history/data, symlinks and unsupported binaries.
- [x] Safe CLI publisher: fresh snapshot, account check, no overwrite/private
  conversion/force-push; remote visibility/commit verification after creation.
- [x] Connected GitHub account identified: **ChipmunkRPA**.
- [x] Target `ChipmunkRPA/open-accounting` checked: **404 / unavailable to connector**.
- [ ] **GitHub repository creation and publication — not completed.** The connector
  does not expose repository creation. No unrelated repository was modified.
- [ ] GitHub Actions run, branch rules, private vulnerability reporting and release tag.
- [ ] Hosted website deployment.

See [PUBLISHING.md](PUBLISHING.md). Run the publisher from your authenticated local
GitHub CLI, or create/initialize a suitable public repository and make it available
to the connected GitHub tool. An archive is not a published repository.

## Next development sequence

1. Complete the public GitHub push and run clean-install CI.
2. Professionally review the five core topic families and correct/version the drafts.
3. Acquire a small cleared primary-source corpus with exact versions and locators.
4. Approve content through independent rights and technical gates; run real Gemini evaluations.
5. Expand revenue, lease and stock-compensation cases and improve semantic retrieval.
6. Validate production privacy/auth/billing/retention and then launch the hosted service.
