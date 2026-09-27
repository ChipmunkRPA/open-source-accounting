# Issue #8 validation receipts · 2026-09-27

All inputs and reviewers in these tests are synthetic. No live source acquisition,
GCS write, provider request, human review or production deployment occurred.

- `backend.log` / `backend.xml`: `cd backend && .venv/bin/python -m pytest --junitxml=../reports/intake/backend.xml`.
- `postgres-migrations.log`: `OSA_MIGRATION_TEST_DATABASE_URL=<empty disposable local PostgreSQL URL> backend/.venv/bin/python scripts/check_migrations.py`.
- `postgres-tests.log` / `postgres.xml`: `cd backend && OSA_POSTGRES_TEST_URL=<same migrated disposable DB> OSA_DISPOSABLE_TEST_DATABASE=true .venv/bin/python -m pytest tests/test_intake_postgres.py --junitxml=../reports/intake/postgres.xml`.
- `initial-regression.log`: first 100 SEC/rights regressions before the full suite.
- `intake-tests.log`: first targeted intake run, superseded by the full suite.

Local versions: Python 3.11.9, PostgreSQL 17.11, Node 24.5.0, npm 11.5.1;
parser `source-intake-1/sec-core-0.7.0`; migration `0002_intake`.
PostgreSQL listens only on a local Unix socket; it is not a Cloud SQL instance.
Cross-process tests coordinate four processes/16 reservations and two duplicate
acquisition workers. Synthetic HTTP response count is checked, not actual network rate.

The first publication heuristic rejected a deliberately fake credential URL in a
negative test and its parameterized JUnit name. The fixture now uses a one-character
non-secret placeholder and descriptive test IDs. No scanner rule was weakened.
The recurring upstream Starlette/httpx deprecation warning remains.
