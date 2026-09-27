# Output amendment validation, 2026-09-27

All work groups, bodies, amendments, evidence and reviewers are synthetic. No real license, counsel decision, content approval, source acquisition, model request or Cloud action occurred.

- `targeted.log/xml`: `backend/.venv/bin/python -m pytest backend/tests/test_output_amendments.py backend/tests/test_output_rights.py --junitxml=reports/amendments/targeted.xml`; initial 39 passed.
- `amendment-final.log/xml`: amendment-only suite after adding separate counsel/scope invalidation cases; 23 passed. The subsequent batch case is included in the final suites below.
- `bulk-targeted.log/xml`: output amendment/output rights suites after atomic bulk-reader reservation; 42 passed (24 amendment cases and 18 existing output cases).
- `backend-initial.log/xml`: full suite before the two added counsel/scope cases, 458 passed / 10 optional PostgreSQL cases skipped.
- `backend-before-bulk.log/xml`: after those cases, 460 passed / 10 skipped.
- `backend.log/xml`: final `backend/.venv/bin/python -m pytest backend/tests --junitxml=reports/amendments/backend.xml`; **461 passed / 11 skipped**, Python 3.11.9. All skipped PostgreSQL cases were separately exercised below.
- `postgres-migrations.log`: `OSA_MIGRATION_TEST_DATABASE_URL=<empty disposable UTF-8 database> backend/.venv/bin/python scripts/check_migrations.py`; upgraded to pre-amendment schema `0005_scopes`, inserted a synthetic ledger/receipt, upgraded to head and verified exact count/hash/timestamp preservation and initial term revision. Schema check/downgrade/re-upgrade passed, 32 application tables. This preservation check also runs in CI.
- `postgres-before-bulk.log/xml`: ten PostgreSQL cases passed before the bulk reservation change.
- `postgres-tests.log` / `postgres.xml`: final `OSA_POSTGRES_TEST_URL=<migrated disposable database> OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py --junitxml=reports/amendments/postgres.xml`; **11 passed**. New races cover competing amendments, usage release versus amendment, and opposite-order bulk readers. Counters equal release receipts after either permitted race outcome. PostgreSQL 17.11, local Unix socket; server stopped after verification.

The batch reservation change arose from code review of multi-item readers: sequential reservations could otherwise acquire additional source locks after a group lock. Topics/editorial responses now reserve their complete batch with globally ordered source/group locks. It was not a newly observed production deadlock. No safety test was weakened.

Changed-module Ruff F, actual contract regeneration, content/hash/queue/generated-progress checks passed. Publication heuristic checks configured patterns only, not a full security audit. One upstream Starlette/httpx deprecation warning remains. No frontend changes or new local browser/live MFA result is claimed; CI performs clean frontend, Linux/Python 3.11/3.13, PostgreSQL and Docker checks.
