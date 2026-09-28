# Staged dependency coverage report (#23)

Observed full backend **792 passed / 23 optional PostgreSQL skipped**, including **8 new report cases**. Initial targeted report run **5 passed**, before artifact-record/SEC-unit/cycle cases were added. Receipts: dependency-report-backend.xml and dependency-report-targeted.xml. No failures; one upstream Starlette/httpx warning remains.

TypeScript typecheck, production Identity Platform build, lint F and generated API contract passed. No new local PostgreSQL/migration/live-provider assertion; schema unchanged. Implementation [fe41378](https://github.com/ChipmunkRPA/open-source-accounting/commit/fe413786138d61ebd7b8c37d7aa275536be499a8) passed [CI 36361607407](https://github.com/ChipmunkRPA/open-source-accounting/actions/runs/36361607407): Python 3.11/3.13 clean installs, frontend/backend, migrations/PostgreSQL and Docker. Content/hash/queue/generated-progress/publication checks passed.

Commands:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_dependency_report.py -q --junitxml=reports/intake/dependency-report-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/dependency-report-backend.xml
backend/.venv/bin/python -m ruff check backend/app/services/dependency_report.py backend/app/api/library.py backend/tests/test_dependency_report.py --select F
backend/.venv/bin/python scripts/export_contracts.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
```

Browser: temporary localhost SQLite/mock database with synthetic derived commentary/target. Report showed nine staged records; Show dependents selected the one synthetic dependent. Refined null-review wording from Not required to Not tracked here, rebuilt/reloaded and rechecked. Screenshot dependency-report-ui.png. Temporary server/tab stopped. No real source/review/license counts advanced.

Tests cover reviewer role, pagination/bounds, all-family denominators, missing/stale bindings, no bodies/private findings/output-ledger charges, revoked/transitive impact, stable report hash, incomplete integrity graphs, artifact-record counts without pretending byte verification, SEC excerpts distinct from HTTP artifacts, and cycles. Large-corpus accessibility, consistent multi-statement database snapshots and immutable audit exports remain unproven. No paid resource, deployment, live billing/SMS/inference or notification.
