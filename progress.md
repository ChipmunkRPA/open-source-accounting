# Open Source Accounting — current implementation progress

## 2026-09-27 · #7 operation-rights slice (parent #5; depends on #6)

Implementation: eleven independent operations; strict Boolean grants; unknown-action denial; license effective/expiry boundaries; exact work/body/policy digest; trusted-context requirements for route/workspace/seat/audience/provider/region/retention/jurisdiction; mandatory revision/attestation on the server approval API. Approval/disable serialize on PostgreSQL source rows, and approval increments the policy version so prior saved evidence cannot revive. Rights approval does not grant technical approval to new submissions. Editorial readers cannot see unapproved bodies. Licensed/reviewed-use body submissions are rejected until separately authorized intake exists. Existing unbound records require re-review; no approval migration was fabricated.

Content/policy work: all **32** family recipes remain in scope; added a fail-closed planning matrix with zero granted operations, **9 unsent permission-request packets**, and an unapproved counsel-review template. Read **7 official policy pages** with locator/discovery notes (Copyright Office, AICPA, IFRS, IFAC, IIA, DART, PCAOB). These are policy-page observations, not original HTTP artifacts or acquired standards. Raw response hashes, headers and unknown issue/availability/effective dates are explicitly unavailable/null. FAF/COSO/ISACA product terms and routes still need verification. No form, email, purchase or license agreement was submitted.

Actual validation: backend full regression **307 passed**, one upstream Starlette/httpx deprecation warning; the earlier targeted slice had 117 passing tests. Frontend typecheck, **16 mocked auth tests**, and real Firebase production bundle build passed. Actual API contracts regenerated; changed Python modules passed Ruff F checks after removing two unused imports. Content/hash/queue/generated-progress checks passed; publication heuristic had zero configured sensitive-pattern findings. See `reports/rights/`. Tests use synthetic reviewers and licenses only. No human/legal/accounting approval is asserted.

Baseline #6 CI now passed for commit [1020d62](https://github.com/ChipmunkRPA/open-source-accounting/commit/1020d62e01b8eecd94ecd66ee6e16214eba5cc85): Linux clean builds/tests on Python 3.11 and 3.13, Node 22, PostgreSQL migration round trip and Docker production build. [CI receipt](https://github.com/ChipmunkRPA/open-source-accounting/actions/runs/36335402383). [PR #42](https://github.com/ChipmunkRPA/open-source-accounting/pull/42) remains open for maintainer review; no force-push or merge was performed.

Coverage unchanged: original drafts **63 inventoried / 63 hash-verified / 0 professionally reviewed / 0 Agent-admitted**; 58 educational questions, 26 historical references; SEC **34 targets / 28 selected parsed excerpts / 7 excerpted sources / 0 full HTTP documents / 0 independent technical or applicability approvals / 0 approved production-indexed sources / 0 human-adjudicated evaluations**. All publisher standards remain reference-only pending specific rights. No new source corpus acquisition, authority claims or live model evaluation. Source and model versions remain those recorded for #6; `gemini-3.8-flash` Cloud availability/endpoint/region/costs remain unverified under #26.

Remaining #7 work (not marked complete): pre-acquisition authorization records and #8 adapter integration; trusted scope propagation through retrieval/model/export; cumulative quotation/reconstruction controls; attribution enforcement; counsel-review persistence; revocation/deletion across derived indexes/caches/articles. Scoped policies currently deny legacy callers that cannot supply trusted context. This is a safe limitation, not a completed licensed intake system. Real rights evidence and reviewers are blocked on operator action (owner unassigned); code and synthetic contracts remain unblocked. Broader MFA/Cloud/billing/production gates remain unchanged and require approved secure configuration and explicit authorization.

Next resumable task: finish the pre-acquisition policy record and policy-aware intake boundary under **#7 → #8**, preserving the 32-family matrix, before acquiring any new body text. Review/merge #42 before its dependent rights PR. No unattended execution is scheduled. Rights commit/PR links follow after publication.

---

## 2026-09-27 · #6 baseline integration (parent #5)

Scope: 277 archive members reconciled file-by-file; 229 missing files imported, generated frontend assets excluded, conflicting root README/progress retained in `docs/archive`. Baseline SHA-256: `3d4f78aa6bfab4323af14ce58cf1b8f77cba2967d984bdbdf378fd9a1ff5529f`. PR #4 head `4ac0b7a539ecaf21ca78695f264d916772be2dfb` and PR #41 head `a257bc767811370342675b879b8a4451e8acb4ab` are preserved in this branch's ancestry; SEC module bytes and data are equivalent. This integration supersedes the standalone-code scope of #4 and includes #41; neither PR nor its issues were closed. Main inspected at `4ffce77dc67a0151077c0e6cdc4caf38c055185c`.

Implementation: native FastAPI/TypeScript application, worker, migrations, fixtures and all-content handoff maps; uppercase root README; Python `uv.lock` plus hash-pinned runtime requirements; Node lock; real Firebase MFA bundle build; Docker vendor-copy correction; read-only clean-install CI with PostgreSQL 17. Retired the old encoded materializer and main-writing cleanup workflow without executing either. Existing license selections are retained and conflicting legacy notice corrected.

Actual local checks (Python 3.11.9, Node 24.5.0, npm 11.5.1, uv 0.10.9, PostgreSQL 17.11):
- Handoff verifier: PASS, 66 checksummed files, 277 members, 63 item hashes, 32 family recipes, 47 planning areas, 38-task acyclic queue, 16 workflow mappings.
- Clean `uv sync --project backend --extra dev --frozen`: PASS; 74 installed packages. `uv pip check`: PASS.
- `npm ci --ignore-scripts`, typecheck, `test:auth` and **production** `build`: PASS; 16 mocked auth tests; registry audit reported zero vulnerabilities. Firebase 12.19.0 exists in the official registry and was retained. No real sign-in or SMS was attempted.
- Backend `python -m pytest`: **248 passed**, one upstream Starlette/httpx deprecation warning. Initial run was **247 passed / 1 failed** because frontend assets had not finished building; CI now builds the production frontend before backend tests. Both logs retained.
- Empty local PostgreSQL: upgrade, model/schema parity, downgrade and re-upgrade PASS; 22 application tables. No Cloud SQL or PostgreSQL concurrency claim.
- Actual API/model schemas regenerated. Content checker PASS: 63 items, 58 educational questions, 26 reference records, three arithmetic examples. Queue/hash and content/SEC progress checks PASS. Publication heuristic found zero configured sensitive-pattern matches; this is not a security audit.
- Docker daemon unavailable locally; Dockerfile build is assigned to CI. Linux/Python 3.13 and Node 22 validation awaits CI. No historical test counts are presented as rerun results above.

Coverage remains unchanged: 63/63 original items inventoried and hash-verified, 0 professionally reviewed or Agent-admitted; 58 educational questions are not independent benchmark cases. SEC 34 targets, 28 selected parsed excerpts from seven sources; **0 full HTTP source artifacts acquired**, 0 professionally/applicability-approved or production-indexed sources, 0 human-adjudicated evaluations. The 32 family recipes and 47 topic records are planning units; no new publisher body was acquired, license granted, content approved or live model evaluated. All restricted bodies remain reference-only. Source versions remain the supplied v0.7 SEC pack and v0.5/v0.6 original item revisions. Requested model remains `gemini-3.8-flash`; Cloud endpoint, SDK behavior, region, availability and costs are unverified under #26.

Blockers/owners: maintainer review and CI for #6 (owner unassigned); operator project/region/approved credentials and spend for #26–#28; operation-specific rights evidence for #7/#9–#21; real independent technical/applicability reviewers for #22/#23/#36. Local metadata, policy code and synthetic tests remain available. No paid resources, production deployment, live billing, notifications, filings or journal entries were authorized or performed.

Next resumable action: review the #6 integration PR and CI; proceed on a bounded dependent #7 branch with strict operation-level rights and permission-request packets for all families. Keep #6 open until acceptance/CI is confirmed. No unattended continuation is scheduled.

Evidence: `reports/bootstrap/`, `reports/bootstrap/reconciliation.json`. Integration commit: [3b09304](https://github.com/ChipmunkRPA/open-source-accounting/commit/3b09304). Review: [PR #42](https://github.com/ChipmunkRPA/open-source-accounting/pull/42). CI is running; its result is not yet claimed.

---

## Preserved pre-integration progress history

The following entries and historical test counts predate this integration. The current section above controls release status; generated content inventory remains current.

# open-source-accounting — progress

Updated: September 27, 2026. This public tracker distinguishes prepared local work from verified repository publication and live deployment.

## Release state

- [x] Project renamed to `open-source-accounting`.
- [x] Public target repository exists at `ChipmunkRPA/open-source-accounting`.
- [x] v0.6 application and content release prepared locally.
- [ ] Complete application source import verified in this repository. The connector transport encountered integrity mismatches; see `PUBLICATION_STATUS.md`.
- [ ] Clean installation with all production dependencies validated.
- [ ] Google Cloud deployment and real-provider integrations validated.

## Content-pack inventory

| Type | v0.5 | Added in v0.6 | Current prepared total |
|---|---:|---:|---:|
| Original research guides | 14 | 14 | 28 |
| Synthetic worked cases | 5 | 3 | 8 |
| Reusable templates | 6 | 3 | 9 |
| Agent workflow playbooks | 16 | 0 | 16 |
| Study-question guides | 1 | 1 | 2 |
| **Content items** | **42** | **21** | **63** |
| Structured study questions | 30 | 28 | 58 |
| Source/license reference records | 22 | 4 | 26 |

All new content is AI-assisted editorial draft material. No item is represented as independently technically approved. The prepared release includes `scripts/content_progress.py` to generate a detailed item/topic inventory from the content manifest and check tracker freshness.

## Added coverage

The v0.6 pack adds guides on cash flows; credit losses; inventory; asset impairment; fair value; business combinations; consolidation; income taxes; foreign currency; going concern; subsequent events; related parties; software costs; and debt/equity classification.

New worked cases cover a cash-flow bridge, foreign-currency monetary-liability remeasurement, and a liquidity timing gap. New templates cover estimates, subsequent-event chronology, and currency evidence. Numerical exercises document stipulated assumptions rather than presenting calculations as proof of accounting conclusions.

## Content development gates

- [x] Preserve and validate the earlier 42-item pack.
- [x] Add and validate 21 original items and 28 study questions.
- [x] Record provenance, hashes, source references, and draft status.
- [x] Keep proprietary standards reference-only absent separately approved rights.
- [x] Keep public draft publication separate from Agent-evidence approval.
- [ ] Independent technical review of every guide and worked case.
- [ ] Confirm primary-source coverage and applicability for supported reporting periods.
- [ ] Broaden disclosure examples and regulatory correspondence through approved acquisition.
- [ ] Expand a professionally reviewed benchmark for each Agent workflow.
- [ ] Validate source-change detection and dependent-content re-review.

## Google Cloud and MFA implementation

- [x] Backend checks for verified email and TOTP or SMS MFA on authenticated application access.
- [x] Revocation-aware token verification, project/tenant checks, session age, and fresh-authentication checks for sensitive operations.
- [x] Frontend TOTP enrollment and challenge flow; Google Authenticator-compatible local QR/manual setup.
- [x] Frontend SMS flow with consent, reCAPTCHA, resend controls, and stale-request guards.
- [x] Fresh sign-in after enrollment; backup-factor enrollment requires reauthentication.
- [x] Fail-closed production configuration and MFA-client-bundle checks.
- [x] Preview-first Identity Platform configuration script and Google Cloud setup documentation.
- [ ] Install and build the complete production Firebase SDK bundle.
- [ ] Configure the actual Google Cloud/Identity Platform project and SMS regions.
- [ ] Test real TOTP enrollment/sign-in, real SMS delivery, revoked sessions, and account recovery.
- [ ] Complete deployed-origin browser, accessibility, abuse, and penetration testing.

Public library pages remain available without authentication. Free chat remains free but requires the account security checks for authenticated use. Hosted Agent operations remain US$89.99/year. The subscription does not grant rights to proprietary source material.

## Recorded local validation

- 203 Python tests passed in the prior v0.6 baseline.
- 16 mocked MFA-controller tests passed.
- TypeScript checks and demo frontend build passed.
- Content validation: 63 items, 58 questions, 26 references.
- Release preflight found no matches for its configured sensitive-data patterns; this is not a full security audit.

These results do not establish live Firebase, Google Cloud, Gemini, Stripe, or SMS operation, nor accounting accuracy. The production dependency install was blocked by package-network/DNS availability in the development environment.

## Next development order

1. Publish and verify the complete source tree, then run clean CI.
2. Deploy to a dedicated staging Google Cloud project and complete MFA/security tests.
3. Independently review the content pack and admit approved evidence only.
4. Validate the five core Agent workflows against professionally reviewed cases.
5. Expand topic depth, vetted primary-source coverage, and reviewed examples before broadening production claims.

The SEC source work below proceeds as a standalone addon while full baseline publication remains open. The complete local v0.7 package also includes the API/UI integration; this addon branch alone is not the full hosted application.

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
