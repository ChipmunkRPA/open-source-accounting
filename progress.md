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

- 203 Python tests passed.
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
