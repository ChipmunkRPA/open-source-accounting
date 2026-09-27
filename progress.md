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
