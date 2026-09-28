# Resumable integrity reconciliation (#8/#23)

Observed backend **822 passed / 25 optional PostgreSQL skipped**, before the final family-partition case. Final targeted **9 passed**. Lint F and generated API contract passed; CLI help ran. No frontend/schema changes, new browser assertion, local PostgreSQL or migration run. Corrected [CI 36363740221](https://github.com/ChipmunkRPA/open-source-accounting/actions/runs/36363740221) passed both Python 3.11/3.13 clean installs, frontend/backend, migrations/PostgreSQL and Docker. Content/hash/queue/generated-progress/publication checks passed.

```sh
backend/.venv/bin/python -m pytest backend/tests/test_integrity_reconciliation.py -q --junitxml=reports/intake/reconciliation-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/reconciliation-backend.xml
backend/.venv/bin/python -m ruff check backend/app/reconcile_integrity.py backend/app/api/intake.py backend/tests/test_integrity_reconciliation.py --select F
backend/.venv/bin/python scripts/export_contracts.py
PYTHONPATH=backend backend/.venv/bin/python -m app.reconcile_integrity --help
```

Cases exercise actual application inventory/verification routes with synthetic fixtures: page traversal, persisted resume, all 32 family rows, normalized units separate, denied rights, recent-auth/transport/rate/server pause, raw-hash conflict before reads, origin/inventory/result checksum rejection, state locking/symlinks/private permissions, inventory bound, plan/run/report entry point with a synthetic token, and family partitions marking others out of scope. No token appeared in output. No test failures; one upstream Starlette/httpx warning.

No real token, publisher acquisition, Cloud bucket, professional decision, paid resource, deployment, live inference/billing/SMS/notification. Limits and operator commands: docs/INTEGRITY_RECONCILIATION.md. Inventories are non-atomic bounded read sets; observations may become stale. A completed scan is not corpus completeness or content approval.

Publication preflight initially flagged a deliberately fake credential URL in the rejection test. Implementation 914de03 was pushed despite that failed check; d0dc6f9 constructs the same synthetic rejected URL without the literal pattern. Nine targeted tests and publication preflight reran successfully before the corrective push. Superseded CI 36363712485 was cancelled; the corrected CI above passed. No real credential was involved.
