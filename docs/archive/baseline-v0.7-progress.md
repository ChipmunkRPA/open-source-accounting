# Progress — open-source-accounting v0.6.0

**Snapshot:** September 27, 2026. This is a development record, not a promise of background work. Prior release detail is preserved under `docs/archive/`.

## Product decisions

- [x] Repository and product renamed to **open-source-accounting**.
- [x] General AI chat and reading/downloading original public content remain free.
- [x] Hosted Agent workflows retain **US$89.99/year** pricing; existing artifacts remain available after expiry under the retention policy.
- [x] Gemini 3.8 Flash remains the configured live model; mock responses remain the local default.
- [x] Google Cloud remains the deployment target: Cloud Run, Cloud SQL, private GCS, Secret Manager, and Identity Platform.
- [x] Mandatory verified-email plus **TOTP authenticator or SMS** for every real signed-in account.
- [ ] Approve production quotas, purchase terms, privacy notices, recovery process and support channel. The 30-task monthly allowance remains proposed.

## Current implementation

| Workstream | Code status | Verification / remaining work |
|---|---|---|
| Backend mandatory MFA | Implemented in `backend/app/auth.py` | SDK boundary mocked in local tests; live project test required |
| Enrollment without workspace access | Implemented `/auth/status`; no user provisioning before MFA | Negative API tests |
| Sensitive-action reauthentication | Five-minute default window for billing/admin/member/document changes | Claims-based tests; no automatic replay of sensitive writes |
| Maximum session age | Twelve-hour default, based on original `auth_time` | Refresh does not reset this application limit |
| Browser TOTP enrollment | Local QR generation, manual key, code confirmation, fresh sign-in afterwards | Controller tests; live QR scan still needed |
| Browser SMS enrollment/sign-in | Consent, E.164 number input, reCAPTCHA, resend cooldown | Controller tests; actual delivery and abuse controls need staging tests |
| Backup-factor enrollment | Security screen requires existing-factor sign-in before adding another | Live SDK/UI test required |
| Session cancellation | Clears in-memory secrets/resolvers and rejects delayed completion | Controller tests |
| GCP MFA configuration | Preview-first script; narrow configuration patch and read-back verification | Preview tested; not applied to any project |
| Infrastructure | Identity read-only runtime permission and environment templates updated | Terraform not applied |
| Content expansion | 21 new original items; old immutable v0.5 item versions retained | Drafts only; no independent accounting review |
| Content tracking | Manifest-derived topic inventory below, checked in CI | Regenerate whenever manifest or questions change |
| GitHub publication | Repository is public; release publication being verified | Final remote commit and CI status recorded in the delivery report, not assumed here |

## Content-pack inventory

<!-- CONTENT-INVENTORY:START -->

Manifest release **0.6.0**: **63 items**, **58 study questions**. Counts are coverage indicators, not quality scores.

| Topic | Guides | Cases | Templates | Playbooks | Q&A sets | Questions | Human-reviewed items | Next gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| audit | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Independent technical review; then authority/access validation |
| audit-evidence | 1 | 0 | 1 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| business-combinations | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| cash-flows | 1 | 1 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| consolidation | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| contingencies | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| controls | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Independent technical review; then authority/access validation |
| credit-losses | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| debt-and-equity | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| disclosures | 0 | 0 | 0 | 3 | 0 | 0 | 0 | Independent technical review; then authority/access validation |
| documents | 0 | 0 | 0 | 2 | 0 | 0 | 0 | Independent technical review; then authority/access validation |
| fair-value | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| financial-reporting | 3 | 1 | 1 | 0 | 0 | 5 | 0 | Independent technical review; then authority/access validation |
| foreign-currency | 1 | 1 | 1 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| going-concern | 1 | 1 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| government-audit | 1 | 0 | 0 | 0 | 0 | 1 | 0 | Independent technical review; then authority/access validation |
| impairment | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| income-taxes | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| internal-controls | 1 | 1 | 0 | 0 | 0 | 3 | 0 | Independent technical review; then authority/access validation |
| inventory | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| learning | 0 | 0 | 0 | 0 | 2 | 0 | 0 | Independent technical review; then authority/access validation |
| leases | 2 | 1 | 0 | 1 | 0 | 4 | 0 | Independent technical review; then authority/access validation |
| related-parties | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| research | 1 | 0 | 4 | 7 | 0 | 4 | 0 | Independent technical review; then authority/access validation |
| revenue | 3 | 2 | 1 | 1 | 0 | 7 | 0 | Independent technical review; then authority/access validation |
| software-costs | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| stock-compensation | 1 | 0 | 0 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |
| subsequent-events | 1 | 0 | 1 | 0 | 0 | 2 | 0 | Independent technical review; then authority/access validation |

All draft items remain ineligible for automatic Agent admission. Rights approval and technical review are separate, revision-bound gates.
<!-- CONTENT-INVENTORY:END -->

## Content production backlog

| Priority | Topic/package | Next deliverables | Required validation |
|---|---|---|---|
| P0 | Existing five core topics: revenue, leases, stock compensation, contingencies, ICFR | Independent review of existing guides/cases; fix findings in new versions | Actual qualified reviewer, current authoritative references, negative examples |
| P0 | Approved primary-source corpus | Small cleared SEC/PCAOB/GAO corpus with version and locator records | Acquisition terms, allowed operations, notices, retention, source authority labels |
| P0 | Gold-standard evaluation set | Convert selected draft Q&A into adjudicated, fact-specific cases | Human adjudication; expected citations, alternatives, abstention and calculation checks |
| P1 | Cash flows, receivables, inventory | More scope-specific cases, rollforwards, disclosure questions | Data reconciliation and model applicability |
| P1 | Impairment and fair value | Distinct asset-model cases, input hierarchy, sensitivities | Specialist and technical accounting review |
| P1 | Acquisitions and consolidation | Acquisition-versus-asset cases, control-rights matrices, restructuring changes | Current authority and complete agreements |
| P1 | Income taxes and FX | Jurisdictional provision cases, functional-currency evidence, rate-direction checks | Appropriate tax/technical review; no generic legal-rate assumptions |
| P1 | Software and debt/equity | Current-adoption software cases; convertible instrument and modification cases | Amendment/effective-date research; avoid outdated shortcuts |
| P1 | Subsequent events / going concern / related parties | More fact-pattern alternatives and auditable event/relationship registers | Distinguish management and auditor duties and time horizons |
| P2 | Additional accounting coverage | Pensions, segment reporting, EPS, derivatives/hedging, investments, nonprofit and governmental topics | Separate scope and editorial capacity before enabling Agent claims |
| P2 | International and specialist work | IFRS comparison sets and industry packs | Actual source rights, regional applicability, specialist review |

## Release acceptance gates still open

- [ ] Clean dependency install and vulnerability scan of the pinned frontend dependencies.
- [ ] Actual Firebase SDK production bundle build in a network-enabled environment.
- [ ] End-to-end verified email, Google Authenticator scan, SMS delivery and alternative-factor sign-in on the deployed origin.
- [ ] Live revoked-token, disabled-user, tenant-isolation, session-age and factor-recovery tests.
- [ ] Cloud project billing, SMS country restrictions, quotas, alerts and reCAPTCHA configuration.
- [ ] Production recovery runbook exercised with two-person approval; no public email-only bypass.
- [ ] Live Gemini, Stripe, GCS and PostgreSQL integration/concurrency tests.
- [ ] Professional content review and a measured, adjudicated accounting benchmark.
- [ ] Public website launch. GitHub publication does not deploy the service.

## How to continue without losing the audit trail

1. Create a topic-specific issue and identify missing authority, facts, examples and reviewer.
2. Add original content with provenance and `unreviewed` status; never overwrite an imported immutable version silently.
3. Update `content/manifest.json`, its hash, and relevant Q&A. Run the content validator and inventory generator.
4. Add negative/edge cases and deterministic numerical tests where appropriate.
5. Have rights and technical reviewers approve the exact revision separately before Agent admission.
6. Record observed test results below and merge only reviewed changes. No count of generated articles establishes comprehensiveness by itself.

## Validation results

Local validation currently includes **203 passing Python tests**, **16 passing browser-controller tests**, a passing TypeScript typecheck/demo build, and content/inventory checks. The production dependency install was blocked by an npm DNS/network error; no live identity bundle or authentication test is claimed. Final measured totals are in the release report.

Results for this build are recorded in `reports/release-v06-tests.txt` and `reports/release-v06-validation.json`. Historical v0.5 browser screenshots and counts are historical evidence, not tests of the new MFA interface. No live cloud authentication, billing, inference, or deployment is claimed.


## GitHub publication integrity status — September 27, 2026

- Target renamed to `ChipmunkRPA/open-source-accounting`; repository exists.
- Local v0.6 source and content release complete at the documented test scope.
- **Remote source publication is not verified complete.** The connector-based staged upload encountered integrity mismatches; no mismatched snapshot should be imported.
- Added `scripts/publish_existing_repository.py`: authenticated, preview-first publication into the existing bootstrap repository; preserves Git history, rejects unexpected existing source, verifies the final remote commit, and never force-pushes.
- Live Google Cloud deployment, Firebase MFA enrollment/sign-in, SMS delivery, and Gemini/Stripe integration remain outstanding.

<!-- SEC-CORE:START -->

## SEC source development — 0.7.0, September 27, 2026

**Current slice:** source-reading preview, explicit intake commands, exact locators, and integration with the existing review gates. SEC Core is not complete.

**34 source targets; 7 sources with selected excerpts; 28 excerpts (3,514 words).**

Zero complete source documents, zero original HTTP artifacts, zero independently reviewed sources, and zero Agent-approved SEC passages in the shipped seed. Transcribed official-source excerpts are not raw downloads. Original educational content counts remain separate.

| Collection | Inventoried targets | Sources excerpted | Excerpts | Complete documents | Agent approved |
|---|---:|---:|---:|---:|---:|
| cfi | 2 | 1 | 12 | 0 | 0 |
| forms | 9 | 1 | 2 | 0 | 0 |
| frm | 11 | 2 | 4 | 0 | 0 |
| reg_g | 1 | 0 | 0 | 0 | 0 |
| reg_sk | 2 | 1 | 6 | 0 | 0 |
| reg_sx | 1 | 0 | 0 | 0 | 0 |
| sab | 8 | 2 | 4 | 0 | 0 |

Catalog target units overlap and vary in size; these counts are not a percentage of all SEC coverage. Successfully parsing a source does not establish technical accuracy or effective dates.

### Ordered work queue

| Position | Workstream | State | Dependency |
|---:|---|---|---|
| 1 | [SEC-CORE #1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1) | in_progress | None |
| 2 | [SEC-PRACTICE #2](https://github.com/ChipmunkRPA/open-source-accounting/issues/2) | queued | SEC-CORE |
| 3 | [SEC-AUDIT-ENFORCEMENT #3](https://github.com/ChipmunkRPA/open-source-accounting/issues/3) | queued | SEC-CORE, SEC-PRACTICE:pilot |

**Queued means a GitHub development issue, not unattended execution.** No scheduled crawler, cloud job, future delivery or billing action was enabled.

### Implementation and release gates

- [x] Add government-host catalog, normalized excerpt hashes and per-passage provenance.
- [x] Implement read-only FTS preview, public API and `/sec-core` frontend.
- [x] Implement explicit bounded HTTP intake, conservative parsers and raw/snapshot storage.
- [x] Reparse and hash-check acquired snapshots before idempotent database staging.
- [x] Keep rights/technical approval separate; preserve exact locators in Agent retrieval.
- [x] Add privileged revision-bound applicability review; never use import date as effective date.
- [x] Create GitHub issues #1, #2, #3 with acceptance criteria and dependencies.
- [ ] Complete native publication of the earlier full application; addon publication alone is insufficient.
- [ ] Acquire and validate complete Core source publications; live network intake blocked in this environment.
- [ ] Review HTML selectors, PDF/table layouts and citation completeness against actual full sources.
- [ ] Exercise the shared PostgreSQL rate budget and controlled egress on deployed infrastructure.
- [ ] Perform real independent rights, technical and historical-applicability reviews.
- [ ] Replace legacy 2,000-source Agent retrieval bound; validate persistent retrieval at corpus scale.
- [ ] Create professionally adjudicated accounting/citation benchmarks and source-update monitoring.

Observed local checks: 248 Python tests passed (203 baseline + 45 new); TypeScript typecheck and demo build passed. Mocked acquisition/reviewer fixtures are not live downloads or real professional approvals. No live Gemini, Identity Platform, PostgreSQL or cloud deployment was performed.

Commands: `PYTHONPATH=backend python -m app.sec_core validate`; `python scripts/sec_core_progress.py --write`; `python scripts/sec_core_progress.py --check`. Full details: `docs/sec/README.md`.

<!-- SEC-CORE:END -->


## SEC Core publication receipt — September 27, 2026

- Native SEC addon published on `feat/sec-core-0-7`; [draft PR #4](https://github.com/ChipmunkRPA/open-source-accounting/pull/4) is open and **not merged**.
- Verified head: `4ac0b7a539ecaf21ca78695f264d916772be2dfb`. The six Python addon modules, two source-data files and standalone unit-test file match the tested local Git blob hashes. See `reports/sec-core-publication-hashes.json`.
- GitHub issues [#1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1), [#2](https://github.com/ChipmunkRPA/open-source-accounting/issues/2) and [#3](https://github.com/ChipmunkRPA/open-source-accounting/issues/3) record Core, Practice and Audit & Enforcement respectively. The latter two are queued development work, not scheduled runs.
- The PR contains the standalone addon, catalog, excerpts, tests, license and tracking. The full local application integration is supplied in the v0.7 archive; **the earlier full application is still not verified on main**.
- Isolated addon validation passed **41 tests without the full application baseline**. The complete local application passed **248 Python tests**. The compiled SEC UI passed **12 isolated component checks**; the existing MFA controller passed **16 mocked tests**. TypeScript typecheck and demo build passed.
- No new coverage percentage, deployed browser test, successful live HTTP intake, GitHub CI result, cloud deployment or professional accounting approval is claimed.
