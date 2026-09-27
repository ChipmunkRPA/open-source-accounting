# Open Accounting — open-source research workspace

**Version:** 0.5.0  
**Product:** free general AI chat; Agent work at **US$89.99/year**  
**Configured generation model:** `gemini-3.8-flash`  
**Status:** working local application, tests, and production adapters. **Not production-certified or deployed.**

This is application source code, not another static website prototype. The browser calls a real
FastAPI backend. Chats, documents, research jobs, evidence, memos, revisions, access states,
and notifications persist in a database. A separate worker executes Agent jobs.

The default installation is deliberately safe: **local identities + deterministic mock model +
no live billing**. Mock answers explicitly say they are demonstrations, not accounting analysis.
No proprietary accounting corpus, paid model credentials, customer files, or secret keys are included.

## Open-source release and content library

**Code: MIT. Original educational content: CC BY 4.0.** See [LICENSE](LICENSE),
[content/LICENSE.md](content/LICENSE.md), [NOTICE.md](NOTICE.md), and
[CONTRIBUTING.md](CONTRIBUTING.md). The hosted Agent price does not restrict your
rights to fork, modify, or self-host under the open licenses.

This release adds **42 original library items, approximately 16,800 words, 30 study
questions, and 22 official-source/license reference records**. Read the
[content index](content/README.md), or start the application and open **`/library`**.
The library is free to read and download without an account or Agent subscription.

All 42 items are **AI-assisted editorial drafts, not professionally reviewed**.
No current ASC text or proprietary standards corpus is included. Some publisher
pages were examined; other pointers remain reference-only. The source registry
records that distinction. The pack is neither comprehensive GAAP guidance nor a
professionally validated model benchmark.

The public reader and Agent evidence store are separate. Content is staged as
unapproved, then requires independent rights and technical approval before Agent
inference. Test passes do not grant either approval.

**GitHub publication was not completed in the authoring environment.** The account
was connected, but the target repository was unavailable and the connector did not
provide repository creation. See [PUBLISHING.md](PUBLISHING.md) for the checked,
fail-closed publication script. No deployed website is represented.

![Open library rendered component preview](reports/library-desktop.png)

## 1. What is implemented

| Module | Working implementation |
|---|---|
| Free chat | Saved threads, ordinary follow-ups, mock/live provider boundary, abuse limit independent of payment |
| Agent catalogue | 16 tasks; five core workflows enabled, ten additional research workflows and corpus watch experimental |
| Research intake | Framework/entity/period context, confirmed facts, document selection, free deterministic scope preview |
| Paid execution | Server-side subscription gate, idempotent start, usage reservation, concurrency cap, cancellation |
| Research worker | Durable database queue, lease/claim/retry, planning, permission-filtered retrieval, synthesis, checking, release |
| Evidence | Claim/evidence identifiers, source locators, text vs reference-only labels, current-permission recheck |
| Documents | TXT/MD/text-PDF/DOCX; private workspace storage, subprocess parsing, limits, optional ClamAV integration |
| Memos | Result-to-memo conversion, manual editing, autosave, optimistic revisions, review history, MD/HTML/DOCX/PDF export |
| Billing | Annual Stripe Checkout/portal REST adapters, verified webhooks, canonical reconciliation, cancellation/expiry, local demo controls |
| Source administration | Operation-specific policies, independent approval, source disable, dependency blocking, audit records |
| Workspaces | Ownership/membership, reviewer vs editor actions, registered-user sharing, private-data checks |
| Deterministic tools | Text diff, relative-SSP allocation, simple fixed-payment lease schedule, journal balance helper |
| Watches | Opt-in new-approved-corpus notifications in the app; no email or autonomous web monitoring |
| UI | Actual responsive TypeScript application, source/evidence dialogs, task forms, editor, pricing and billing |
| Operations | Initial Alembic migration, CLI, Docker/Compose, deployment templates, tests and generated OpenAPI |
| Open library | 42 manifest-backed items, search, filters, reader, Markdown download, provenance and review labels |
| Content review | Immutable content hashes, idempotent staging, separate rights/technical roles, revocable Agent admission |
| Open-source release | License notices, contribution guidelines, source manifest, preflight scanner, safe GitHub publisher |

See **[progress.md](progress.md)** for the precise implementation/test status and gaps. See
**[docs/module-map.md](docs/module-map.md)** for where each capability is implemented.

## 2. Start locally — recommended first run

Requirements: Python **3.11+** (tested here on 3.13.5), a normal internet connection to install
packages, and two terminals. Node is not needed to run the included compiled UI; it is needed
to edit/rebuild the TypeScript frontend.

From the extracted `open-accounting` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e './backend[dev]'
cp backend/.env.example backend/.env
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` and use
`Copy-Item backend/.env.example backend/.env`. Keep both processes in the `backend` directory
so relative database/storage locations and `.env` are consistent.

**Terminal 1 — API and website:**

```bash
source .venv/bin/activate
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Agent worker:**

```bash
source .venv/bin/activate
cd backend
python -m app.worker
```

Open **http://localhost:8000**. API documentation is at **http://localhost:8000/docs**.
The local database and uploads live under `backend/data/`.

On macOS/Linux, after dependency installation, `bash scripts/dev.sh` starts both processes
and stops them when the script exits. Keep the default localhost-only network binding.

**Do not publicly expose `AUTH_MODE=dev`.** The development identity selector intentionally
has no passwords and is not an authentication mechanism.

### Local walkthrough

1. Send a message in **Chat · Free**. A clearly labeled mock response is saved.
2. Choose **Agent studio → Deep research**, enter a question, and save the scope.
3. Starting as a Free user opens the annual-plan upgrade. Choose **Activate local Agent demo — no charge**.
4. Confirm the saved scope and explicitly start. The worker processes the task.
5. Inspect evidence and reference-only labels. Create a memo, edit it, review a revision, and export.
6. In Billing, cancel renewal or switch the development state to Expired. Saved work stays available;
   new Agent work is blocked and general chat remains free.
7. Upload the original fictional files in `fixtures/` to try document and contract-comparison flows.

No part of this walkthrough charges a card or calls Gemini.

## 3. Editing and rebuilding the UI

```bash
cd frontend
npm install
npm run typecheck
npm run build
```

The build emits `frontend/dist`; FastAPI serves it directly. Refresh the browser after a build.
The primary UI intentionally uses native DOM components and strict TypeScript rather than
requiring a React install to run. User text is inserted as text nodes, not executable HTML.

An **optional, unvalidated Next.js host** is included at `frontend/next-host/`; its readme describes
how to host the same UI in Next. It was not installed or built in this environment and is not
required for the working default application. It does not add SSR, SEO, or a second editor.

## 4. Enable Gemini 3.8 Flash deliberately

The live adapter is `backend/app/providers/gemini.py`. It calls the Google Cloud REST
`generateContent` endpoint with Application Default Credentials. It does not silently fall back
to another model, consumer API, or location.

For a controlled local integration test, install the project dependencies, configure a Cloud project
with billing/model access, and obtain ADC with your approved Google Cloud authentication method.
For example, with the Google Cloud CLI installed:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

In `backend/.env`, set:

```dotenv
MODEL_PROVIDER=google_cloud
MODEL_ID=gemini-3.8-flash
MODEL_LOCATION=us
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

Restart **both** API and worker. This can incur model charges even though general chat is free to
end users. `us`, `eu`, and `global` are explicit multi-region choices in this adapter; a live smoke
test must confirm your project's access and endpoint behavior. Do not assume your Cloud Run
region is the model's location.

The adapter uses LOW/MEDIUM/HIGH thinking configurations for distinct stages, structured JSON,
and application validation. It does not set obsolete temperature controls, use unrestricted
Google Search grounding, or enable automatic model-owned tool execution.

A provider outage, truncated answer, invalid schema, or unavailable model fails explicitly.
A second model pass is not an independent accounting professional review. The live model
endpoint and accuracy have **not** been tested with credentials in this handoff.

## 5. Source library and retrieval

### Original content pack

From the repository root, validate the manifest, references, Q&A, and arithmetic:

```bash
python scripts/check_content.py
```

Stage original articles using the **same environment/database as the API**:

```bash
cd backend
python -m app.content validate
# Local demo only: the seeded source administrator has ID admin.
python -m app.content import --author admin
```

In production, use an actual authorized administrator ID. Import is idempotent and
never auto-approves content. In local mode, switch to the **Rights Approver** identity
and approve source rights, then to **Technical Reviewer** to inspect and record an
actual technical decision. Do not approve merely to bypass a gate.

For real accounts, the privileged operator CLI can assign `technical_reviewer` to
a qualified, different user. The technical review records a content hash, source
references, note, decision, reviewer and time. Hash changes invalidate inference
permission. Roles and API guards are covered by tests; no real review has been
recorded for this draft pack.

The public file-based article continues to show its release's draft status until a
new reviewed content version is actually published. Database approvals are not
silently written back into the source files. This preserves an auditable boundary.

### Runtime evidence store

The seed library contains only original research-process explanations and metadata/reference-only
records. It is **not** a comprehensive GAAP library and cannot support a claim that all current ASC
text was reviewed. No DART, AICPA, IFRS, or full ASC content is supplied.

Retrieval is a working **bounded lexical/exact-match implementation**, not pgvector semantic search.
It filters source rights, workspace membership, framework, and available date metadata before
model input. A run reviews a selected subset, not every page of every uploaded document.

Add reviewed content through **Source admin** or the CLI:

```bash
# Run from backend. Users must already exist.
python -m app.admin set-role USER_ID admin
python -m app.admin set-role A_DIFFERENT_USER_ID rights_approver
python -m app.admin import-source ../fixtures/original-source.json --author USER_ID
```

Import creates an **unapproved** record. A different rights approver must approve it. Permissions
are independent for model input, storage, display, quotations, export, embeddings, training and
commercial use. An annual product subscription cannot expand those permissions.

There is an optional, disabled SEC-only acquisition utility in `services/source_gateway.py`.
It is not a general crawler and is not automatically called for user questions. External material
still needs classification and review before publication. Full licensed feeds, automated version
updates, and embeddings are follow-up work.

## 6. Documents and privacy

Supported: `.txt`, `.md`, text-based `.pdf`, `.docx`. Default limits: 10 MB/file, 150 PDF pages,
300,000 extracted characters, 50 documents/workspace. These are configurable engineering limits,
not assurance that every supported file will parse.

The parser runs in a bounded subprocess. Linux adds resource limits; other operating systems
retain timeout/size checks but do not provide the same process limits. There is **no OCR**, image
understanding, spreadsheet ingestion, or forensic PDF-layout preservation. Keep scanned documents
out of the initial workflow.

Set `UPLOAD_SCANNING_REQUIRED=true` and configure `CLAMAV_HOST`/`CLAMAV_PORT` to require the
included ClamAV INSTREAM adapter. Actual scanner/service networking was not tested here. Production
configuration refuses to start without a scanner configuration, but an operator must still verify
that the scanner is reachable and maintained.

Deleting a document removes its active object/chunks and hides/purges dependent stored output and
memo history. It cannot recall downloaded exports or instantly erase backups/provider-retained
copies. A reviewed retention policy and backup deletion procedure are still required. Do not upload
real confidential client material until that review is complete.

## 7. Billing — USD 89.99 annually

### Local testing

`DEMO_BILLING_ENABLED=true` is allowed only outside production. Billing state controls make no
payments. Free chat never consumes Agent task allowance. Manual editing and exporting existing
work remain available after expiry, subject to workspace and source permissions.

The implementation proposes **30 tasks per subscription month**, two simultaneous tasks, and
zero renewal grace by default. These operating policies are **not approved business commitments**.
They are configuration values; publish and approve them before setting `BILLING_TERMS_APPROVED=true`.
Failed/cancelled work releases a reservation. Completed released deliverables consume one task.
No automatic monetary overages are implemented.

### Stripe integration test

1. In Stripe test mode, create one **USD 89.99/year**, licensed, single-quantity recurring Price.
2. Configure a Customer Portal and webhook endpoint for the events below.
3. Populate the following values using test credentials, then restart the API:

```dotenv
BILLING_ENABLED=true
BILLING_TERMS_APPROVED=true
STRIPE_SECRET_KEY=YOUR_TEST_SECRET
STRIPE_WEBHOOK_SECRET=YOUR_TEST_WEBHOOK_SECRET
STRIPE_PRICE_ID=YOUR_8999_USD_ANNUAL_PRICE
STRIPE_API_VERSION=YOUR_REVIEWED_API_VERSION
```

The configured API version must match the endpoint shape you test. No live version is invented
or hard-coded in this codebase. Include `customer.subscription.*`, `invoice.paid`,
`invoice.payment_failed`, checkout completion events, `charge.refunded`, and
`charge.dispute.created` in the reviewed endpoint configuration. Webhook URL:
`POST /api/v1/billing/webhook`.

The webhook verifies the raw-body signature and timestamp, deduplicates event IDs, and retrieves
canonical subscription/invoice state. Access is not granted by a redirect or subscription status
alone. A matching settled annual invoice extends access. Canceled renewal retains the paid term;
archiving the Price does not invalidate a previously paid term. Refund/dispute revocation uses
supported matching-charge/invoice shapes; test your Stripe version thoroughly.

This MVP deliberately rejects trials, coupons, zero-dollar grants, manual out-of-band payments,
multiple seats, prorations/migrations, and ambiguous invoices. Taxes, invoice/legal terms, full
refund operations, chargeback resolution, webhook reconciliation sweeps, and financial reporting
must be reviewed/extended before accepting money. The code does not implement tax advice.

## 8. Production authentication and hosting

Local auth is never a production option. The Firebase adapter verifies server-side ID tokens,
revocation and verified email. The browser includes email/password registration, verification,
sign-in and refresh; tokens are memory-only. Google social login, password-reset UI, MFA, and
email invitations are not implemented. Sharing currently resolves already-registered users.

Production requires explicit settings for Firebase, Google Cloud inference, PostgreSQL, private
GCS, HTTPS, migrations, scanner configuration, and disabled demo features. See
`infra/.env.production.example` and **[docs/deployment.md](docs/deployment.md)**.

Docker/Compose and Google Cloud templates are included, but **no Docker build, Terraform apply,
Cloud Run deployment, Postgres concurrency test, live Firebase sign-in, or GCS call was performed**.
Do not deploy with real customers until those steps and the security/rights review are completed.

## 9. Database migrations and worker operations

Local startup creates the schema and seeds original demo material. Production must not do that.
For a new migration-managed database:

```bash
cd backend
python -m alembic upgrade head
```

The initial migration is frozen in `alembic/versions/0001_v040.py`. Future model changes need a
new reviewed migration. For an existing local auto-created DB, back it up and compare its schema
before stamping; do not blindly run create-table migrations over populated tables.

`python -m app.worker` polls continuously. `python -m app.worker --once` drains currently available
jobs and exits, suitable for a run-to-completion job. API and worker use the same database, source
policy and model configuration. Worker leases prevent simultaneous ownership; provider calls are
**not exactly once** across a crash. Retry budgets limit but do not eliminate duplicate model spend.

The included queue is database-backed. Cloud Tasks, Redis/Celery and immediate event-driven Cloud
Run job launch are not implemented. Scheduled Cloud Run jobs introduce queue latency.

## 10. Tests and evidence

```bash
cd backend
python -m pytest --cov=app --cov-report=term-missing
cd ../frontend
npm run typecheck
npm run build
cd ..
python scripts/export_contracts.py
```

For release 0.5.0, the API/worker and release-script suite passes; exact counts,
coverage, commands, and limitations are recorded in [progress.md](progress.md) and
`reports/content-tests.log`. TypeScript typecheck/build and the content integrity,
reference, and arithmetic checks also passed.

The new library reader was tested through **11 offline compiled-component checks**,
with a local content fixture and no network calls. Tests cover pagination, filtering,
provenance, a Markdown table, draft labels, mobile overflow, and inert handling of
HTML/unsafe links. Local URL navigation was blocked by browser administrator policy;
no policy was changed. These are not deployed-origin authentication, download,
checkout, or end-to-end browser tests. Screenshots in `reports/library-*.png` show
that component-rendering setup. The previous release's broader browser evidence is
historical; this release does not claim it was rerun.

Optional rendering check (requires Playwright and a local Chromium installation):

```bash
python scripts/test_library_components.py
```

Tests used preinstalled libraries; a clean dependency install, lockfile build,
Docker deployment, live cloud credentials, and professional accounting evaluation
remain outstanding. See the exact environment versions in the validation report.
No live Gemini, payment, source-ingestion, or GitHub-publication call is represented
by the offline test passes. GitHub discovery/read calls did run; publication did not.

## 11. Important limitations before launch

- Full ASC/AICPA/IFRS/publisher feeds are not included or licensed by this software.
- Commercial fair-use policies need review; a rights flag is not a legal determination.
- Lexical retrieval, partial document extraction and optional experimental tasks are not exhaustive research.
- The memo editor is Markdown, not a collaborative rich-text editor with tracked AI patch acceptance.
- Lease calculations cover fixed monthly arrears payments only; they do not determine classification or ROU assets.
- Revenue allocation is arithmetic over user-confirmed SSP inputs, not an automatic performance-obligation decision.
- Internal-audit/control results are drafts, not audit opinions, certifications, or autonomous materiality conclusions.
- There is no accounting-system writeback, regulatory filing, external email sending, or payment collection by an agent.
- PDF exports use standard fonts; multilingual/font fidelity and complex tables need further work.
- Storage lifecycle, legal pages, account deletion, centralized abuse controls, full telemetry and disaster recovery are incomplete.

The next implementation steps are recorded in `progress.md`. No background development or future delivery is scheduled.
