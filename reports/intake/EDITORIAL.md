# Editorial ledger validation (#23)

All fixtures and reviewer decisions are synthetic. No actual source rights, accounting review, applicability decision, professional approval or GCP resource was created.

Observed final backend: **679 passed / 19 optional PostgreSQL skipped**. PostgreSQL: **19 passed separately**, including two processes competing to record the same revision. JUnit: editorial-backend.xml and editorial-postgres.xml. Local PostgreSQL 17 used a fresh UTF8 template0 disposable database `osa_editorial`. Migration upgrade/check/downgrade/re-upgrade passed with **36 application tables** and preserved prior output counters and unknown model liabilities; see editorial-migrations.txt. Server stopped afterward.

Commands actually run:

```sh
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/editorial-backend.xml
OSA_POSTGRES_TEST_URL='<local migrated disposable PostgreSQL database>' OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py -q --junitxml=reports/intake/editorial-postgres.xml
OSA_MIGRATION_TEST_DATABASE_URL='<empty local disposable PostgreSQL database>' backend/.venv/bin/python scripts/check_migrations.py
backend/.venv/bin/python scripts/export_contracts.py
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
# From frontend:
npm run typecheck
npm run test:auth
npm run build
```

Frontend typecheck, 16 mocked auth cases and actual production Identity Platform bundle passed. Targeted prior content/SEC cases: 43 passed; new editorial cases: 17 passed. Lint F initially caught the imported fixture re-export; corrected. A broader final lint also found three unused legacy imports in the touched content test file; removed. An initial file-edit command used the wrong working directory and failed without editing; corrected. No test failures or weakened assertions. One upstream Starlette/httpx deprecation warning remains.

Manual browser: isolated local SQLite/mock app at 127.0.0.1:8779. Member role denied editorial access. Selected synthetic technical reviewer, inspected synthetic source body, filled scope/findings/supporting-record reference/hash/expiry and explicit fixture attestation, recorded `changes_requested`, verified history persisted with `current: false`. Screenshot editorial-ui.png. No real professional approval, production identity/MFA, live model, external acquisition or deployment was exercised. Temporary server and browser tab stopped afterward.

Scope limits: technical history is application-immutable, not signed evidence or a database administrator-proof ledger. Evidence identifiers/hashes are attestations, not verified private documents. Reference IDs are bound; linked publication revisions and actual human review remain outstanding. Other #23 acceptance criteria remain open.

Implementation 2e5a37be5852e2df54a27bf311f59196729d9d89 passed main CI 36356428668: Python 3.11/3.13 clean installs, real frontend, backend, migrations/PostgreSQL and Docker. Final import-cleanup targeted regression: 60 passed.
