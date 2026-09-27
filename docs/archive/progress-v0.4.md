# Implementation progress — Open Accounting v0.4.0

This is a handoff snapshot, not an indication of background work. Update the module rows and
checklists with each subsequent implementation change. A checkbox means the stated code/check
exists; it does not imply the whole product is production-ready.

## Confirmed product decisions

- [x] General AI chat is free of subscription charges.
- [x] Agent execution requires an annual **US$89.99** subscription.
- [x] General chat does not consume Agent task allowance.
- [x] Gemini 3.8 Flash is the explicit live generation model; no automatic model/location fallback.
- [x] Source rights and workspace membership are independent from payment.
- [x] Existing saved work remains readable/editable/exportable after expiry, subject to source permissions.
- [ ] Approve a production usage allowance. Current 30/month and two concurrent runs are **proposed**.
- [ ] Publish approved purchase, cancellation, privacy, retention and source-coverage terms.

## Module status

| ID | Module | State in this handoff | Test/evidence | Next action |
|---|---|---|---|---|
| CORE-01 | FastAPI application/config/security errors | Implemented locally | API tests, root/static load | Production HTTP/security audit |
| CORE-02 | Database and models | SQLite implemented; Postgres-ready ORM | 100-test suite, schema migration | Actual PostgreSQL/concurrency evaluation |
| AUTH-01 | Development identities | Implemented, production-forbidden | Role/workspace tests | Keep localhost-only |
| AUTH-02 | Firebase auth | Live adapter implemented, unvalidated | Token boundary/code review only | Credentialed ID-token, refresh, revocation tests |
| CHAT-01 | Free chat/history | Implemented | API + browser harness | Live model response/abuse evaluation |
| AGENT-01 | Catalogue/intake/scope | Implemented | UI and schema tests | Improve topic-specific intake questions |
| AGENT-02 | Durable worker/leases | Implemented DB queue | API/worker tests, lease exhaustion | Postgres contention/crash/load tests |
| AGENT-03 | Bounded orchestration | Implemented | 15 mock workflow executions | Professional evidence/accuracy benchmark |
| AGENT-04 | Gemini Cloud REST | Adapter implemented | Mock transport/schema/failure tests | Real project/model smoke test |
| AGENT-05 | Structured verification | Implemented structural + model pass | Citation/source tests | Stronger semantic entailment/adversarial evaluation |
| SEARCH-01 | Lexical/exact retrieval | Implemented bounded corpus search | Source/period/access tests | Scale benchmark and semantic retrieval |
| SEARCH-02 | Embeddings/pgvector | **Not implemented** | None | Approved embedding provider and index lifecycle |
| SOURCE-01 | Rights registry/admin | Implemented | Independent-approval, disable tests | Legal assessment and source version workflow |
| SOURCE-02 | Licensed standard feeds | **Not supplied/integrated** | Reference-only seed records | Obtain/review real source rights |
| SOURCE-03 | SEC acquisition helper | Implemented, disabled utility | Host/private-address guards | Approved acquisition/normalization and rate tests |
| DOC-01 | TXT/MD/PDF/DOCX extraction | Implemented bounded subprocess | Format/size/path/parser tests | Broader corpus, layout/large-document tests |
| DOC-02 | Malware scanner | ClamAV adapter implemented | Required-scanner guard | Live scanner/maintenance/egress validation |
| DOC-03 | Private object storage | Local implemented; GCS adapter | Local deletion/path tests | GCS IAM/retention/live test |
| DOC-04 | OCR/spreadsheets/images | **Not implemented** | Explicit file rejection | Separate approved parsers and UI |
| MEMO-01 | Editor/revisions | Implemented Markdown editor | API + autosave/browser checks | Rich text and merge/conflict UX |
| MEMO-02 | Human review | Implemented immutable revision labels | Self vs independent tests | Authenticated multi-user E2E |
| MEMO-03 | Exports | MD/HTML/DOCX/PDF implemented | Export tests; sample render inspection | Tables, non-Latin fonts and pagination |
| MEMO-04 | AI redline accept/reject | **Not implemented** | Critique produces a research result | Structured patch suggestions + acceptance UI |
| BILL-01 | Paid gate and quotas | Implemented | Free/paid/expiry/cancel/idempotency tests | Publish approved limits and load test |
| BILL-02 | Stripe Checkout/portal | Adapter implemented | Mock requests/annual-price validation | Real test-mode checkout and portal |
| BILL-03 | Webhooks/reconciliation | Implemented supported shapes | Signature/dedup/invoice/refund tests | API-version matrix, delivery/recovery tests |
| BILL-04 | Taxes/refund operations/promotions | **Not implemented** | Unsupported cases fail closed | Define scope with financial/legal review |
| TOOLS-01 | Relative SSP allocation | Implemented deterministic arithmetic | Decimal/cent checks | Accounting-approved scenario benchmark |
| TOOLS-02 | Simple lease schedule | Implemented monthly arrears only | PV/amortization/input checks | Broader payment conventions/ROU work |
| TOOLS-03 | Contract diff | Implemented bounded text comparison | Workflow tests | Better clause alignment and omissions |
| WATCH-01 | Corpus-change inbox | Experimental implementation | Consent/due/expiry tests | Approval-time/version tracking and dedup hardening |
| WATCH-02 | Live web/email monitoring | **Not implemented** | No misleading external-watch claim | Connect approved feeds and notification delivery |
| UI-01 | Responsive compiled TypeScript app | Implemented | 21 browser harness checks | Real-origin E2E + assistive-technology audit |
| UI-02 | Next.js host | Optional adapter only | **Not installed/built** | Clean install/build and route tests |
| OPS-01 | Alembic/CLI | Implemented | Initial migration run; CLI compile | DBA migration review, role bootstrap testing |
| OPS-02 | Docker/Compose | Templates implemented | **Not built here** | Clean Docker run and volume tests |
| OPS-03 | Google Cloud infrastructure | Templates implemented | **Not applied** | Project/IAM/network/secret review and staging |
| OPS-04 | CI configuration | Added | **Not run on GitHub** | Create clean install lockfiles and run CI |
| OPS-05 | Account deletion/DR/central telemetry | Partial or missing | Documented boundaries | Lifecycle, recovery and operating runbooks |

## Current validation record

- [x] Python API/worker suite: **100 passed** (`reports/backend-tests.log`, JUnit report).
- [x] Python statement coverage: **81%** (`reports/coverage.json`); not branch/security assurance.
- [x] Strict TypeScript typecheck and build completed; compiled assets included.
- [x] **21 browser component/integration checks**, using compiled modules and the actual local
  API/worker through a bridge. History/storage were virtualized because browser URL navigation
  was blocked by environment administrator policy. That policy was not changed.
- [x] Rendered interface screenshots inspected (research, memo, pricing, mobile).
- [x] DOCX/PDF sample exports rendered and visually inspected.
- [x] Initial Alembic migration executed against an empty SQLite database.
- [ ] Live Gemini, Stripe, Firebase, GCS, ClamAV or PostgreSQL integration tests.
- [ ] Clean package installation and lockfile generation. Authoring environment network resolution
  prevented package downloads; tests used already-installed Python/TypeScript dependencies. The tested pypdf 5.9.0 differs from the declared clean-install target >=6, so that resolved dependency set remains untested.
- [ ] Normal deployed-origin browser E2E (including real auth, redirects, download and CORS).
- [ ] Docker/Next builds; Terraform/provider validation and cloud deployment.
- [ ] Technical-accounting benchmark, legal/source review, accessibility and penetration testing.

## Notable changes from the v3 design

The handoff replaces simulated prototype actions with real API/database/worker behavior. It uses
an included compiled TypeScript UI and a database queue to make the local code independently
runnable. Next.js is optional, not the validated default. Semantic/vector retrieval, rich-text
coauthoring, full editorial publication, cloud queue dispatch and licensed standards are not silently
claimed as complete. The 16 workflows share a bounded engine instead of duplicating agent code.

## Next implementation sequence

1. Run a clean installation/CI; pin reviewed dependencies and fix any environmental incompatibilities.
2. Configure Gemini with test credentials and run source-grounded accuracy/robustness evaluations.
3. Replace seed process examples with reviewed original/licensed accounting content and source versions.
4. Validate Firebase, Postgres, private storage/scanner and every Stripe test-mode state transition.
5. Approve limits and terms; implement taxes/receipts and reconciliation recovery required by the offer.
6. Improve retrieval, full-document coverage, memo patch review, multilingual exports and topic intake.
7. Deploy to a private staging project and perform security/accessibility/accounting evaluations.
8. Launch only the independently validated workflows; keep other tasks labeled experimental.

## Update convention

For each future change, record: module ID; commit or artifact; implemented behavior; tests actually
run; unresolved risk; and any migration/configuration change. Never turn an adapter into “live
verified” merely because a mock passed. Keep a dated changelog below.

### v0.4.0 handoff

Implemented free/paid research application, 15 executable research workflows plus experimental
corpus watches, private documents, draft memos, source governance, annual billing adapters,
responsive UI, migration and deployment scaffolding. Added `readme.md`, this tracker, module map,
security/deployment notes, source fixtures and a reproducible test suite.
