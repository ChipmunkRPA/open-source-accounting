# Baseline receipt and precedence

Snapshot: 2026-09-27. Repository: https://github.com/ChipmunkRPA/open-source-accounting.

## Select this baseline

`baseline/open_source_accounting_v0_7_sec_core.zip`
SHA-256: `3d4f78aa6bfab4323af14ce58cf1b8f77cba2967d984bdbdf378fd9a1ff5529f`

The ZIP has 277 members and contains the full integrated local application. It was verified as present and hashed for this handoff. Existing source files were read for structure and routing, not professionally audited. Do not substitute earlier v0.6 ZIPs with inconsistent 50/70/63 content claims.

At the live repository check, `main` was `4ffce77dc67a0151077c0e6cdc4caf38c055185c` and contained bootstrap/publication files rather than the complete application. Draft PR #4 on `feat/sec-core-0-7` contained a standalone SEC addon (reported head `4ac0b7a539ecaf21ca78695f264d916772be2dfb`). Re-read live Git refs before execution. Documentation handoff changes, if added later in this turn, do not publish the complete app.

## Content audit

- 63 original manifest items: {'guide': 28, 'case': 8, 'template': 9, 'playbook': 16, 'qa_set': 2}.
- 58 educational questions; 26 historical source/license reference records.
- All 63 local file hashes match their manifest SHA-256. No professional approvals were created.
- SEC Core: 34 target records; 28 selected excerpts from seven sources; 3,514 words; zero complete original HTTP document artifacts and zero approved Agent SEC evidence.
- The original educational pack and selected official excerpts have different provenance and license treatment. Do not add their counts as a percentage of SEC/GAAP coverage.
- The IFRS comparison playbook currently cites only FASB metadata. Add actual IFRS source/adoption coverage before claiming a two-framework analysis.
- Several item-level `primary_text_gap` flags are false even though the baseline only has reference-only ASC metadata. Primary-source access must be decided from real evidence, not that flag.

## Engineering status to verify

Full source includes FastAPI/SQLAlchemy APIs, bounded worker, TypeScript UI, mock and Gemini adapters, subscription checks/Stripe adapters, identity/MFA code, original content pipeline and SEC addon integration. Known gaps include fresh production dependency install, real Identity Platform/TOTP/SMS tests, actual Cloud Gemini/Stripe/GCS/PostgreSQL integration, scalable retrieval, robust additional formats, professional evaluation and production deployment.

Historical reports record 248 backend tests (including the 41-test standalone SEC subset), 16 mocked identity-controller checks and 12 isolated SEC UI checks. **Those are previous run reports, not tests rerun in this handoff.** The new handoff validation only covers artifact hashes, inventory mapping and queue structure unless expressly noted in VALIDATION.md.

## Precedence

1. Current maintainer decisions and explicit safety/rights boundaries.
2. Live repository history/user changes and current issue acceptance criteria.
3. Verified v0.7 source archive as missing complete-app baseline, reconciled by diff—not an instruction to overwrite newer work.
4. This handoff's requirements and retrieval task maps.
5. v3 functional design as intent; earlier quantities, vendor claims and quotas require verification, not blind copying.

Do not execute legacy materialization/import workflows or encoded payloads just because a bootstrap file references them. Inspect first. Do not force-push, erase history, publish private/licensed source bodies or invent approval to bypass a blocked task.
