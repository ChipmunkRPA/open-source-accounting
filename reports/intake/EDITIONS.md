# Multipart inventory validation — #8 / #15

Synthetic receipts, publishers, reviewers and manifests only. No real source was acquired or approved; no Cloud call, licensed-text publication, schema permission downgrade or live notification occurred.

Commands observed from repository root:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_intake_editions.py -q --junitxml=reports/intake/editions-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/editions-backend.xml
OSA_MIGRATION_TEST_DATABASE_URL='<fresh disposable local PostgreSQL database>' backend/.venv/bin/python scripts/check_migrations.py
OSA_POSTGRES_TEST_URL='<same migrated test database>' OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py -q --junitxml=reports/intake/editions-postgres.xml
backend/.venv/bin/python -m ruff check backend/app/services/editions.py backend/app/api/intake.py backend/app/intake_schemas.py backend/app/models.py backend/tests/test_intake_editions.py backend/tests/test_intake_postgres.py backend/alembic/versions/0014_intake_editions.py --select F
backend/.venv/bin/python scripts/export_contracts.py
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
```

Final targeted suite: **23 passed**, covering missing/optional parts, combined representation exclusion, expected future delivery, changed hashes, immutable revisions, retries/conflicts, bounds, provenance, manifest tampering, holds, permissions, expired/stale parser ledgers and no body/network reads. The full backend run observed **853 passed / 28 optional PostgreSQL skipped** before three final edge-case tests were added. The targeted suite was rerun after those additions and the expiry assertion; no new full-suite count is invented.

PostgreSQL: **28 passed**, including two new parametrized concurrency cases. Both initial registration and next-revision races were exercised with identical and competing payloads. An identical concurrent request returned the same revision ID; a competing one received 409. Migration `0014_intake_editions` passed empty-database upgrade/check/downgrade/re-upgrade and model parity with **41 application tables**. See `editions-migrations.log`. The database was newly created from template0 with UTF8 on a disposable local PostgreSQL instance (socket, port 55441); the server was stopped after tests.

Initial targeted failure: a fixture tried to delete a synthetic artifact while its acquisition attempt retained a foreign key. The database correctly rejected it. The fixture now explicitly clears that synthetic attempt reference before testing metadata loss; constraints were not disabled. Final tests passed. The existing Starlette/httpx deprecation warning remains.

This API/migration change has no frontend edits. No browser journey, fresh production deployment, independent professional evaluation or actual all-family edition reconciliation was performed. Reports count matching receipts from the declared inventory, not current object integrity or independent publisher completeness; current operation rights and parser-ledger status remain separate. Old revisions and receipts are preserved. Non-atomic reporting, declaration quality, UI, broader corpus performance and actual source/reviewer gates are documented in `docs/MULTIPART_EDITIONS.md`.

Final implementation [82025c6](https://github.com/ChipmunkRPA/open-source-accounting/commit/82025c6af6c902d640f605585dde9abeb73ebb3a) passed [CI 36366186438](https://github.com/ChipmunkRPA/open-source-accounting/actions/runs/36366186438): each Python 3.11/3.13 job observed **856 backend passes / 28 optional skips**, **28 PostgreSQL passes**, **16 identity tests / zero failures**, production frontend build, 41-table migration parity and contract/content/publication checks. Docker passed. These are final-commit CI observations, distinct from the earlier local full-suite count.
