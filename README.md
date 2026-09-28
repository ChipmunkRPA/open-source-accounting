# open-source-accounting

**Free general AI chat. Evidence-first Agent work. An open educational accounting library.**

Public repository: https://github.com/ChipmunkRPA/open-source-accounting

This is a runnable **development release, v0.7.0**, not a deployed or professionally validated accounting service. It includes a TypeScript interface, FastAPI backend, database models, job worker, source-permission controls, document analysis, memo editor, subscription adapters, and an original draft-content library.

## Product and hosting model

| Experience | Hosted-service policy |
|---|---|
| General AI chat | Free; abuse/cost limits are separate from payment |
| Public educational library | Free to read and download without an account |
| Agent workflows | US$89.99 per year |
| Existing saved deliverables after subscription expiry | Read/manual edit/export remain available, subject to retention and source permissions |
| Signed-in users | Verified email plus Google Authenticator-compatible TOTP **or SMS** |

The requested generation model is **Gemini 3.8 Flash (`gemini-3.8-flash`)**. Its Cloud availability, endpoint, region and cost remain unverified; local tests use an explicit mock provider. A subscription unlocks application operations, not permission to ingest copyrighted standards. The 30-task monthly allowance remains a proposed operating policy; approve and publish actual limits before enabling real billing.

Application code is MIT-licensed. Original educational content is CC BY 4.0. Hosted pricing does not add a restriction to these open licenses. Third-party standards, brands, and source publications retain their own rights.

## What is included

- Persistent free chat, workspaces, evidence cards and source references.
- Five primary Agent workflows: deep research, memo preparation, uploaded documents + guidance analysis, contract comparison, and memo critique.
- Experimental policy, disclosure, workpaper, benchmarking, audit-preparation, control-review, close-package and framework-comparison workflows.
- Private text-based PDF/DOCX/Markdown/TXT and [literal XLSX/CSV parsing](docs/SPREADSHEET_EXTRACTION.md), document access controls and deletion handling. Spreadsheet formulas are not recalculated and caches remain unverified.
- A durable job engine with scope confirmation, quotas, cancellation, retries, research limitations and claim/evidence relationships.
- Memo revisions, manual editing, review records, Markdown/DOCX/PDF export, and deterministic illustrative calculations.
- Stripe checkout/portal/webhook adapters with backend annual-plan enforcement.
- Source rights and technical-content approval as independent, revision-bound gates.
- **63 original library items, 58 educational Q&A records, and 26 source/license reference records.** All library items remain unreviewed editorial drafts.
- Mandatory Identity Platform MFA, an enrollment/challenge interface, backup-factor setup, a bounded session lifetime and fresh sign-in requirements for sensitive changes.

See [progress.md](progress.md) for the generated topic inventory, actual status, gaps and next work. See [docs/archive/readme-v0.5.md](docs/archive/readme-v0.5.md) for earlier module walkthroughs; current authentication instructions supersede that version.

## Local quick start

Prerequisites: Python 3.11+, Node 22+ for rebuilding the frontend, and a virtual environment. The default mode is an explicitly insecure **local-only demonstration**, with deterministic mock model output and simulated subscriptions. Never expose it publicly.

```bash
python3 -m pip install uv==0.10.9
uv sync --project backend --extra dev --frozen
source backend/.venv/bin/activate
cp backend/.env.example backend/.env

# The source repository does not require generated JS to be committed.
cd frontend
npm ci --ignore-scripts
npm run build
cd ..
bash scripts/dev.sh
```

Open `http://localhost:8000`; API documentation is at `/docs`. The downloadable development archive may include a compiled demo interface. The application persists local data under its configured `data` directory, which must not be committed.

The local identity selector is not MFA and does not simulate security certification. Production configuration rejects dev authentication, mock models, demo billing, SQLite, missing private storage/scanning configuration, and missing compiled identity assets.

## Production authentication: Google Cloud Identity Platform

Read [docs/gcp-mfa-setup.md](docs/gcp-mfa-setup.md) before deployment. Use a dedicated GCP project with Identity Platform enabled. Real authentication uses the Firebase modular browser SDK and Firebase Admin server verification.

```dotenv
AUTH_MODE=firebase
MFA_REQUIRED=true
FIREBASE_PROJECT_ID=YOUR_PROJECT_ID
FIREBASE_API_KEY=YOUR_PUBLIC_CLIENT_IDENTIFIER
FIREBASE_AUTH_DOMAIN=YOUR_PROJECT_ID.firebaseapp.com
FIREBASE_TENANT_ID=
AUTH_SESSION_MAX_AGE_SECONDS=43200
AUTH_RECENT_SECONDS=300
```

New users verify email and enroll TOTP or SMS, then sign in again with that second factor. The API checks SDK-verified reserved sign-in claims; client booleans or mere enrollment do not grant access. `/auth/status` permits a limited setup status response without provisioning a private workspace. Every normal private API continues to require completed MFA.

The Security page supports adding a backup method after reauthentication. QR generation stays in the browser. Phone verification uses Google reCAPTCHA and requires consent. Tokens, passwords, OTPs and setup secrets are not put into application local/session storage or telemetry. Recovery is an operator process; there is no email-only or recovery-code bypass implemented.

Build the actual production identity bundle:

```bash
cd frontend
npm ci --ignore-scripts
npm run typecheck
npm run test:auth
npm run build
```

`build:demo` deliberately does not produce the real identity bundle. Production fails closed without it. A clean dependency install, lockfile review, vulnerability scan and actual SDK integration test are required before public launch.

Preview project configuration without creating cloud resources:

```bash
python scripts/configure_identity_platform.py \
  --project YOUR_PROJECT_ID --domain app.example.com --sms-region US
```

The separate explicit apply command is documented in the MFA guide. SMS availability/costs, region policies, identity recovery, email delivery, quotas and authorized domains require operator configuration. No cloud change or live phone message is made by a local build or unit test.

## Gemini and other external services

```dotenv
MODEL_PROVIDER=google_cloud
MODEL_ID=gemini-3.8-flash
MODEL_LOCATION=us
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

Backend credentials use Google workload identity/ADC. Do not expose model keys to the browser. The adapter has no silent provider/model/region fallback. Confirm the chosen model endpoint and retention configuration in your project. No live model call is required for local mock tests.

Use Cloud Run, Cloud SQL/PostgreSQL, private GCS and Secret Manager with the templates under `infra/`. Those templates are not an applied production deployment. Review networking, scanner availability, migrations, database users, service-account permissions, backup policies, task scheduling and spending controls. Keep billing disabled until purchase terms, usage limits and actual Stripe configuration are approved.

## Build and maintain the content pack

Original v0.5 item files retain their immutable versions. This release adds fourteen research workbooks, three worked cases, three templates and a second Q&A set. It does not bundle proprietary ASC/DART/AICPA/IFRS full text. A link is not evidence that the Agent read current primary text.

```bash
python scripts/check_content.py
python scripts/content_progress.py          # Refresh the inventory in progress.md
python scripts/content_progress.py --check  # CI freshness gate

cd backend
python -m app.content validate
python -m app.content import --author admin # Local demo example only
```

Import stages items unapproved. It does not grant source rights, professional technical approval or permission to use an article in Agent responses. A real author/reviewer must confirm actual review and the exact content hash. When changing an already imported item, publish a new version instead of silently replacing its source text.

For each addition: identify the topic gap; use original prose and examples; identify source references and inaccessible primary text; update metadata and SHA-256; add case/QA tests; regenerate the inventory; obtain independent review. Do not upload client documents, private contracts, copyrighted databases or unapproved source text as contributions.

## Tests and current limits

```bash
cd backend
python -m pytest
cd ../frontend
npm run typecheck
npm run test:auth
npm run build
cd ..
python scripts/check_content.py
python scripts/content_progress.py --check
python scripts/release_preflight.py --check
```

Local tests exercise mock provider and SDK boundaries. A passing test suite does not establish accounting accuracy, real SMS delivery, successful Google Authenticator scanning, or production authorization. Current bootstrap results are under `reports/bootstrap/`; all other bundled reports are historical and are not new test receipts.

Known gaps include live cloud/payment/model integration, production identity and recovery exercises, security review, vector retrieval, OCR, spreadsheet ingestion, rich collaborative editing, comprehensive accounting calculation engines, and professional review of the content pack. No audit opinion, autonomous financial posting, tax-law certification or regulatory filing is produced.

## Important files

| Path | Purpose |
|---|---|
| `backend/app/auth.py` | Verified identity, MFA gate and fresh-auth dependency |
| `frontend/vendor/machine.mjs` | Testable enrollment/challenge state machine |
| `frontend/vendor/identity.mjs` | Firebase/QR SDK adapter |
| `frontend/src/authentication.ts` | Enrollment, QR, SMS, challenge and recovery UI |
| `scripts/configure_identity_platform.py` | Preview/apply Identity Platform configuration |
| `content/manifest.json` | Versioned article metadata and hashes |
| `scripts/content_progress.py` | Deterministic content inventory for progress.md |
| `progress.md` | Feature state, content coverage and remaining release gates |
| `docs/gcp-mfa-setup.md` | Cloud/MFA setup, security and recovery checklist |
| `CONTRIBUTING.md` / `SECURITY.md` | Contribution and security requirements |

## Publishing and releases

The canonical repository is `ChipmunkRPA/open-source-accounting`. Keep validated work on main, following the operator update in AGENTS.md. Use a short-lived branch/PR only when needed; integrate it before starting the next task. Do not recreate the repository, force-push unrelated history, or publish data/secrets. The legacy `scripts/publish_github.py` is only for a new absent target and refuses this existing repository; use normal Git for subsequent releases.

GitHub publication is not public website deployment. The repository's current remote files and CI results, rather than this source archive, establish publication status. See [PUBLISHING.md](PUBLISHING.md).


## Publishing into the existing renamed GitHub repository

Target: `ChipmunkRPA/open-source-accounting`. The complete remote source import is **not yet verified**; use the preview-first publisher rather than the older create-repository script.

```bash
gh auth login
python3 scripts/publish_existing_repository.py
# Review the file list and hashes, then explicitly apply:
python3 scripts/publish_existing_repository.py --apply
```

The script requires Git/GitHub CLI authentication, refuses unexpected existing application code, never force-pushes, and verifies the remote commit. It is syntax-checked but not live-run in the development environment. Publishing source does not configure Google Cloud or enable live MFA.

## ASU tracking

Open `/asu-tracking` for the free rolling two-year ASU register and company filing disclosures. Search by ASU/topic, then filter materials by company/CIK and reported adoption status. The starter catalog has 16 ASU references and 12 filing links across two companies; it is not a complete issuance or filer universe.

The worker refreshes identifiers from authorized staged SEC filing passages daily, with resumable batches and immediate rights-revocation checks. It does not automatically discover or acquire new external filings. Reference links and automatic mentions remain distinct from retained artifacts and approved evidence. See [ASU tracking operations and coverage](docs/ASU_TRACKING.md) and [observed validation](reports/asu/VALIDATION.md).

## SEC Core starter integration — v0.7.0

The public **/sec-core** screen provides searchable selected official excerpts and an explicit acquisition inventory. New code implements controlled intake, raw/normalized hashes, conservative XML/HTML/PDF parsing, exact locators and existing-source review integration. The original 63-item educational manifest is unchanged; **34 SEC targets, 7 excerpted sources and 28 excerpts** are tracked separately. No complete source documents or original HTTP bytes are bundled, and no SEC passage is automatically approved for Agent evidence.

Read [the SEC Core guide](docs/sec/README.md) for commands and limits. Run `PYTHONPATH=backend python -m app.sec_core validate` and `python scripts/sec_core_progress.py --check`. The machine-readable queue is `content/sec_core/work_queue.json`: [Core #1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1) is active; [Practice #2](https://github.com/ChipmunkRPA/open-source-accounting/issues/2) has an in-progress [submissions metadata pilot](docs/ASU_FILING_PILOT.md); [Audit & Enforcement #3](https://github.com/ChipmunkRPA/open-source-accounting/issues/3) remains queued. Neither is an activated external crawler.

The complete local release integrates the API, frontend and existing Agent pipeline. The GitHub SEC addon can be published independently of the earlier full-application bootstrap; do not infer that the full application has been uploaded from addon publication. See the delivery report for the verified remote commit.


## SEC Core publication receipt — September 27, 2026

- Native SEC addon published on `feat/sec-core-0-7`; [draft PR #4](https://github.com/ChipmunkRPA/open-source-accounting/pull/4) is open and **not merged**.
- Verified head: `4ac0b7a539ecaf21ca78695f264d916772be2dfb`. The six Python addon modules, two source-data files and standalone unit-test file match the tested local Git blob hashes. See `reports/sec-core-publication-hashes.json`.
- GitHub issues [#1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1), [#2](https://github.com/ChipmunkRPA/open-source-accounting/issues/2) and [#3](https://github.com/ChipmunkRPA/open-source-accounting/issues/3) record Core, Practice and Audit & Enforcement respectively. The latter two are queued development work, not scheduled runs.
- The PR contains the standalone addon, catalog, excerpts, tests, license and tracking. The full local application integration is supplied in the v0.7 archive; **the earlier full application is still not verified on main**.
- Isolated addon validation passed **41 tests without the full application baseline**. The complete local application passed **248 Python tests**. The compiled SEC UI passed **12 isolated component checks**; the existing MFA controller passed **16 mocked tests**. TypeScript typecheck and demo build passed.
- No new coverage percentage, deployed browser test, successful live HTTP intake, GitHub CI result, cloud deployment or professional accounting approval is claimed.

## Reconciliation and dependency queue

The verified full v0.7 archive is reconciled with PR #4 and PR #41, preserving both histories. See [the reconciliation receipt](reports/bootstrap/reconciliation.json) and [progress](progress.md). The former bootstrap README is retained under `docs/archive/bootstrap-README.md`. Only uppercase `README.md` is published at the root.

Use `tasks/queue.json`, `tasks/OPERATOR_DECISIONS.md`, and `content/SOURCE_RETRIEVAL_PLAYBOOK.md` for the complete dependency-ordered queue under #5. All 32 source-family recipes, 47 topic plans and 63 original-item mappings are retained; these are inventories, not acquired or approved evidence.

For a disposable **empty PostgreSQL** database, run:

```bash
# Supply the local test URL through your environment, never a production database.
export OSA_MIGRATION_TEST_DATABASE_URL=postgresql+psycopg://localhost/osa_test
python scripts/check_migrations.py
python scripts/check_queue.py
```

This check refuses a nonempty database, runs upgrade/downgrade/re-upgrade, and checks model/schema parity. CI uses PostgreSQL 17 with synthetic local credentials and no cloud secrets. Docker builds use the committed Node lock and hash-pinned Python runtime requirements.

Technical reviewers: see [the review-record workflow](docs/EDITORIAL_REVIEWS.md) for exact revisions, supporting evidence, expiry, revocation and private history.

Scoped operators can triage source corrections and takedowns at `/corrections`.
Use private administrative descriptions and approved restricted record references;
never paste licensed text, legal advice or credentials into notes. Disabling a source
blocks dependent runtime use. Resolving a case does not restore that source or approve
its content. See [review operations](docs/EDITORIAL_REVIEWS.md) for roles and limits.

Operators can run bounded, resumable all-family or per-family stored-artifact checks
with the [integrity reconciliation client](docs/INTEGRITY_RECONCILIATION.md).
Its private state distinguishes verified bytes, failures, denied operations and
unobserved units; completing a scan does not approve content.

Claim-level human assessment is available through the workspace-scoped [claim review API and operator workflow](docs/CLAIM_REVIEW.md). Reviewers must have both an assigned technical-review role and permission in the target workspace; secure supporting-record handles, actual review attestations and exact claim/evidence revisions are required. Recorded decisions do not grant source rights or certify an entire deliverable. A dedicated reviewer interface and real professional adjudication remain pending.
