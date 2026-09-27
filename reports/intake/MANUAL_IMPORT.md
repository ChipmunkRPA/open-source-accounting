# Issue #8 manual intake validation

All source bytes, delivery evidence and reviewers in these tests are synthetic. No network acquisition, publisher permission, accounting approval or GCP deployment occurred.

Commands actually run from the repository root:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_manual_intake.py backend/tests/test_source_intake.py -q
backend/.venv/bin/python -m pytest backend/tests/test_manual_intake.py -q
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/manual-backend.xml
OSA_POSTGRES_TEST_URL='<local disposable migrated PostgreSQL database>' OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py -q --junitxml=reports/intake/manual-postgres.xml
backend/.venv/bin/python -m ruff check backend/app/intake_schemas.py backend/app/services/intake.py backend/app/api/intake.py backend/app/ingest.py backend/app/sec_core/fetch.py backend/tests/test_manual_intake.py backend/tests/test_intake_postgres.py --select F
backend/.venv/bin/python scripts/export_contracts.py
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
```

PostgreSQL 17.11 used the existing disposable `osa_model_budgets_final` database on local Unix socket/port 55439. No schema changes were made in this slice; schema roundtrip was not rerun locally. The server was stopped after 16 PostgreSQL tests passed. JUnit files contain observed test totals and outcomes. Full backend skips are optional PostgreSQL tests exercised separately. One upstream Starlette/httpx deprecation warning remains. No test failures were observed; inspection commands initially referenced two nonexistent test paths and were corrected. This does not validate real GCS, delivery evidence, live MFA or professional content correctness.
