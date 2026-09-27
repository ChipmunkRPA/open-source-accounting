# General applicability validation (#23)

Observed full backend: **753 passed / 21 optional PostgreSQL skipped**, including **23 new applicability cases**. Initial targeted run **39 passed** (21 applicability plus 18 parser cases), before two additional applicability cases. Separately, **all 21 PostgreSQL cases passed**, including competing applicability decisions: one append and one stale conflict. No test failures. Broad lint found eight existing unused imports in billing/core/workspaces/SEC/storage; removed and lint passed. One upstream Starlette/httpx deprecation warning remains.

Empty PostgreSQL upgrade/check/downgrade/re-upgrade and model/schema parity passed with **38 application tables**; existing output counters and unknown model liabilities survived upgrade. Receipts: applicability-{backend,targeted,postgres}.xml and applicability-migrations.txt. Disposable PostgreSQL stopped afterward.

Commands actually run:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_applicability.py backend/tests/test_parser_review.py -q --junitxml=reports/intake/applicability-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/applicability-backend.xml
# Disposable local PostgreSQL URL supplied through the named environment variables:
OSA_MIGRATION_TEST_DATABASE_URL="$TEST_DATABASE_URL" backend/.venv/bin/python scripts/check_migrations.py
OSA_POSTGRES_TEST_URL="$TEST_DATABASE_URL" OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py -q --junitxml=reports/intake/applicability-postgres.xml
backend/.venv/bin/python -m ruff check backend/app backend/tests/test_applicability.py backend/tests/test_parser_review.py backend/tests/test_intake_postgres.py --select F
backend/.venv/bin/python scripts/export_contracts.py
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
```

Database URL above is a reproducible placeholder for the observed disposable Unix-socket database, not a credential or assertion that a production database was tested. No new local frontend/browser/live-provider check this slice. Implementation a0ae67910320aade9f5b684d926c5c1be8c92924 passed main CI 36358792516: both Python 3.11/3.13 clean installs, real frontend, backend, migrations/PostgreSQL and Docker. Prior documentation main c5e9712 passed CI 36358366377.

All fixtures, reviewers, rights and evidence references are synthetic. Zero actual acquired/parsed/reviewed/indexed units added. Tests exercise missing review, actual public versus import dates, entity/framework/audit scope, bounded/open-ended intervals, unresolved conditions, expiry/revocation, stale content/technical/payload changes, private history and saved-export withholding. They do not prove accounting correctness, licensing, actual reviewer identity or case-specific conditional applicability.

Limits: API-first; general review UI and conditional resolver remain. Bundled SEC uses its existing separate workflow and still needs durable-ledger reconciliation. Linked-publication dependencies, industry/jurisdiction scope and independent actual review remain. Browser download completion remains unverified. No paid resource, deployment or live inference/billing/SMS/notification occurred.
