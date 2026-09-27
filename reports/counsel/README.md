# Counsel workflow validation, 2026-09-27

All counsel references, people, source bodies and review attestations in these tests are synthetic. No actual legal or accounting approval, source acquisition, live model, MFA provider, Cloud, billing or SMS action occurred.

- `targeted.log` / `targeted.xml`: `backend/.venv/bin/python -m pytest backend/tests/test_counsel.py -q --junitxml=reports/counsel/targeted.xml`; 24 passed on Python 3.11.9.
- `backend.log` / `backend.xml`: `backend/.venv/bin/python -m pytest backend/tests --junitxml=reports/counsel/backend.xml`; 405 passed, 6 skipped (explicit PostgreSQL-only cases).
- `postgres-migrations.log`: initial `OSA_MIGRATION_TEST_DATABASE_URL=<empty local database> backend/.venv/bin/python scripts/check_migrations.py` failed before migration because that database inherited SQL_ASCII encoding. PostgreSQL `SHOW server_encoding` confirmed SQL_ASCII. No migration guard was relaxed.
- `postgres-migrations-utf8.log`: same migration command with a separate fresh UTF-8 database passed upgrade, schema comparison, downgrade, re-upgrade and comparison; 30 application tables. PostgreSQL 17.11, local Unix socket. Database created with `createdb --template template0 --encoding UTF8`.
- `postgres-tests.log` / `postgres.xml`: `OSA_POSTGRES_TEST_URL=<migrated UTF-8 local database> OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py --junitxml=reports/counsel/postgres.xml`; 6 passed, including two new counsel activation/revocation races. Four processes still share intake rate reservations; the existing intake/output race cases also ran. The local PostgreSQL server was stopped afterward.

Changed-module Ruff F passed after removing one unused import in the new test file. Actual API contracts regenerated with `scripts/export_contracts.py`. Content, queue, original/SEC generated-progress checks passed. Publication heuristic is only a configured-pattern screen, not a security review. One upstream Starlette/httpx deprecation warning remains.

This branch has no frontend edits; no new local browser/MFA/frontend result is claimed. CI performs a fresh frontend install/typecheck/auth test/production bundle, Linux/Python 3.11/3.13 regressions, PostgreSQL migration/concurrency checks and Docker build. Published commit/CI links belong in `progress.md` and the PR.
