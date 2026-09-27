# Parser/citation review validation (#23)

All artifacts and decisions in tests are synthetic. No real professional review, licensed acquisition or authoritative approval occurred.

Backend: **711 passed / 20 optional PostgreSQL skipped**. New parser-specific cases: **18 passed**. Initial parser-targeted run had 16 passes/1 failure due to the test using a nonexistent Storage._local helper; changed to the actual _path helper, added expiry/dependent-export coverage and passed 18. Later private-history assertions and explicit publication metadata/notice checks were added and final full regression rerun. JUnit: parser-review-backend.xml and parser-review-targeted.xml. One upstream Starlette/httpx warning remains.

PostgreSQL: **20 passed separately**, including two processes submitting the same parser sequence (one append, one 409). Fresh UTF8 template0 `osa_parser` database; upgrade/check/downgrade/re-upgrade passed with **37 application tables**, preserving output counters and unknown model liabilities. See parser-review-postgres.xml and parser-review-migrations.txt. Initial cluster start used its default socket/port, causing createdb to fail against the intended test socket. Restarted the known disposable cluster with the explicit Unix socket, port 55439 and no TCP listener; then the migration/test run passed. Stopped the server afterward.

Commands actually run:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_parser_review.py -q --junitxml=reports/intake/parser-review-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/parser-review-backend.xml
OSA_MIGRATION_TEST_DATABASE_URL='<empty local disposable PostgreSQL database>' backend/.venv/bin/python scripts/check_migrations.py
OSA_POSTGRES_TEST_URL='<local migrated disposable PostgreSQL database>' OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py -q --junitxml=reports/intake/parser-review-postgres.xml
backend/.venv/bin/python -m ruff check backend/app/services/parser_review.py backend/app/services/rights.py backend/app/services/intake.py backend/app/models.py backend/app/api/library.py backend/app/editorial_schemas.py backend/tests/test_parser_review.py backend/tests/test_intake_postgres.py --select F
backend/.venv/bin/python scripts/export_contracts.py
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
```

No frontend source changed and no new local browser/MFA/build result is asserted. CI separately exercises the real frontend build, clean Python installs, PostgreSQL and Docker. Dedicated parser-review UI and actual independent review remain open. Parser records cannot establish accounting correctness, historical applicability or source permission. Runtime provenance checks do not read the full raw object on every request; new packets/decisions do verify bytes.
