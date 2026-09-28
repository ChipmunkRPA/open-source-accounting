# Persistent integrity holds (#8/#23)

Observed full backend **813 passed / 25 optional PostgreSQL skipped**, before the final cross-hold test/staging guard was added. Final targeted **16 passed** (five new hold cases plus 11 existing integrity cases). Real PostgreSQL contracts **25 passed**, including concurrent failures preserving both artifact holds and policy increments. TypeScript typecheck, production Identity Platform build, lint F and generated API contract passed. No schema change or new migration assertion; reused the disposable migrated 40-table database.

```sh
backend/.venv/bin/python -m pytest backend/tests/test_integrity_holds.py backend/tests/test_artifact_integrity.py -q --junitxml=reports/intake/integrity-holds-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/integrity-holds-backend.xml
# OSA_POSTGRES_TEST_URL and OSA_DISPOSABLE_TEST_DATABASE supplied for disposable local database:
backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py -q --junitxml=reports/intake/integrity-holds-postgres.xml
backend/.venv/bin/python scripts/export_contracts.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Failures and corrections: TypeScript initially rejected nullable app.me; corrected with optional access. Initial PostgreSQL restart used the default socket/port, so all 25 cases failed to connect and did not exercise contracts; restarted that same disposable database with the recorded socket/port, rerun passed. Upstream Starlette/httpx warning remains. Browser initially reused old assets on one local origin; verified rebuilt assets from a fresh local origin. Found stale acknowledgement error after success, fixed message clearing and repeated the journey.

Final browser: synthetic damaged-then-restored artifact kept its hold despite verified hashes. Local rights-approver role was required for release; missing acknowledgement rejected. Acknowledged release rechecked files and reported old evidence remained invalid, without stale error text. Screenshot integrity-holds-ui.png. Temporary servers/tab stopped. No real artifact repair or reviewer decision, acquisition, paid resource, deployment, live inference/billing/SMS/notification.

Limits: holds affect the entire work conservatively and can require renewed scoped/counsel permissions before recovery checks. They protect operations using existing runtime dependency checks and cannot recall downloaded copies. No automatic hold clearance, source enabling, approval, old-evidence revival or in-place passage rebinding. Corpus-wide reconciliation, immutable external audit storage, recovery workflows and live GCS behavior remain open. See docs/EDITORIAL_REVIEWS.md.

Implementation [6678cf9](https://github.com/ChipmunkRPA/open-source-accounting/commit/6678cf95d7dc4fc82fdeb9c0b1a5dca798c8151f) passed [CI 36363181461](https://github.com/ChipmunkRPA/open-source-accounting/actions/runs/36363181461): Python 3.11/3.13 clean installs, frontend/backend, migrations/PostgreSQL and Docker. Content/hash/queue/generated-progress/publication checks passed.
