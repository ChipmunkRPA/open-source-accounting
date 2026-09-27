# Issue #8 offline index discovery validation

Synthetic HTML and reviewers only. No publisher index or linked publication was fetched, and no production rights or professional approvals were created.

Commands run from repository root:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_source_discovery.py -q
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/discovery-backend.xml
OSA_MIGRATION_TEST_DATABASE_URL='<empty local disposable PostgreSQL database>' backend/.venv/bin/python scripts/check_migrations.py
OSA_POSTGRES_TEST_URL='<same migrated disposable database>' OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py -q --junitxml=reports/intake/discovery-postgres.xml
backend/.venv/bin/python -m ruff check backend/app/source_discovery.py backend/app/services/discovery.py backend/app/models.py backend/app/api/intake.py backend/app/ingest.py backend/alembic/versions/0009_discovery.py backend/tests/test_source_discovery.py backend/tests/test_intake_postgres.py --select F
backend/.venv/bin/python scripts/export_contracts.py
```

PostgreSQL 17.11 database `osa_discovery`, created empty from template0 with UTF8 on the existing local socket/port 55439. Migration output is saved in discovery-migrations.txt. JUnit files record actual totals and failures. Full backend skips are optional PostgreSQL cases exercised separately. The existing upstream Starlette/httpx warning remains. A migration-file inspection used an incorrect filename; an initial API patch context did not match and was corrected before tests. Neither event changed database state or weakened tests.

Observed results: 624 backend passes/17 optional PostgreSQL skips; 17 PostgreSQL passes; 35-table migration round trip and parity passed. Content/hash, queue DAG, generated progress and publication checks also passed using the standard scripts listed in the previous intake report. No test failures. Local PostgreSQL was stopped after validation.
