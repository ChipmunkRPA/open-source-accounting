# Output rights validation · 2026-09-27

Synthetic original source text, permissions and reviewers only. No publisher body,
real review, live model, Cloud resource, billing or notification was used.

- `initial-backend.log`: initial full regression, 363 passed / 2 skipped before new tests.
- `targeted.log`: first output-control suite, 16 passed; two additional cases are included in the final full suite.
- `backend.log` / `backend.xml`: `cd backend && .venv/bin/python -m pytest --junitxml=../reports/output-rights/backend.xml`.
- `postgres-migrations.log`: empty disposable local PostgreSQL upgrade/check/downgrade/re-upgrade, 29 application tables. Command: `OSA_MIGRATION_TEST_DATABASE_URL=<disposable database> backend/.venv/bin/python scripts/check_migrations.py`.
- `postgres-tests.log` / `postgres.xml`: `OSA_POSTGRES_TEST_URL=<migrated disposable database> OSA_DISPOSABLE_TEST_DATABASE=true .venv/bin/python -m pytest tests/test_intake_postgres.py --junitxml=../reports/output-rights/postgres.xml`, 4 passed. Two intake/rate-budget and two output-ledger concurrency cases. PostgreSQL 17.11, Unix socket only.

Frontend typecheck and production build passed. Backend extraction assertions verified
required notices in Markdown/HTML/DOCX/PDF and escaped HTML-like text. Local browser
read-only verification at `/topics` confirmed the visible synthetic notice and zero
script elements in its notice container. The source-inspection button did not open
its dialog through the in-app browser controls (no console errors); it is not claimed
as an end-to-end UI pass. Added visible source-request error handling. The temporary
preview server, tab and PostgreSQL server were stopped after verification.

Some initial helper/read commands used an incorrect working directory or an outdated
patch context; those made no application changes and were corrected. Three pre-existing
unused names in the changed API modules were removed after Ruff F reported them. The
upstream Starlette/httpx deprecation warning remains. No test guard was relaxed.
