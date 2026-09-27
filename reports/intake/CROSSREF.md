# Crossref intake validation (#8, #19)

Fixtures are original synthetic metadata and reviewers. No Crossref works page, abstract, full text, license or publisher index was acquired. Official documentation was inspected read-only; exact URLs, date and distinctions are recorded in docs/CROSSREF_INTAKE.md.

Commands actually run from repository root:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_crossref_discovery.py -q
backend/.venv/bin/python -m pytest backend/tests/test_crossref_discovery.py backend/tests/test_manual_intake.py backend/tests/test_source_discovery.py backend/tests/test_source_intake.py -q
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/crossref-backend.xml
OSA_POSTGRES_TEST_URL='<local migrated disposable PostgreSQL database>' OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py -q --junitxml=reports/intake/crossref-postgres.xml
backend/.venv/bin/python -m ruff check backend/app/crossref_discovery.py backend/app/services/source_concurrency.py backend/app/intake_schemas.py backend/app/services/intake.py backend/app/services/discovery.py backend/app/sec_core/fetch.py backend/tests/test_crossref_discovery.py backend/tests/test_intake_postgres.py --select F
backend/.venv/bin/python scripts/export_contracts.py
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
```

The first targeted run had 30 passes and one failure: OPEN_LITERATURE lacked the official API host in its recipe. Added the official issue #19 seed api.crossref.org, then all 31 cases passed. Later targeted coverage grew to 38 cases. One upstream Starlette/httpx warning remains. No tests were weakened or skipped to hide this failure.

PostgreSQL 17.11 used the existing disposable osa_discovery database (35 tables) on the local Unix socket/port 55439. All 18 PostgreSQL cases passed, including the new cross-process single-request admission test. No migration/schema change; roundtrip not rerun locally. The database server was stopped after validation. See JUnit files for observed final totals. No new local frontend, real MFA, provider access or invoice result is claimed.

Final observed totals: 662 backend passes/18 optional PostgreSQL skips; all 18 PostgreSQL cases passed separately. Implementation commit e841cb056d670b8c56ff72e09978c3a396bb1274 passed main CI run 36355697683 on Python 3.11/3.13, frontend, migrations, PostgreSQL and Docker. No paid resources or live provider calls were made.
