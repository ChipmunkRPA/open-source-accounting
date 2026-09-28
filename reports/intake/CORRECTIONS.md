# Correction/takedown queue validation (#23)

Observed full backend run: **796 passed / 23 optional PostgreSQL skipped** (before final impact endpoint and two additional targeted cases). Final targeted run: **6 passed**. PostgreSQL contracts: **24 passed**, including competing correction actions (one commits and one receives 409; one policy increment/event). Migration round trip and re-upgrade/schema parity passed with **40 application tables**. TypeScript typecheck, production Identity Platform build, lint F and generated API contract passed. CI recorded after observation.

```sh
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/corrections-backend.xml
backend/.venv/bin/python -m pytest backend/tests/test_corrections.py -q --junitxml=reports/intake/corrections-targeted.xml
# Disposable, explicitly designated PostgreSQL URL supplied via environment:
backend/.venv/bin/python scripts/check_migrations.py
backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py -q --junitxml=reports/intake/corrections-postgres.xml
backend/.venv/bin/python scripts/export_contracts.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Synthetic browser fixture: restricted technical-reviewer access rejected; admin opened a case, disabled its source, resolved the case and inspected one recorded dependent. Source remained disabled. Browser found the version label used the wrong metadata key; fixed, rebuilt and rechecked. Screenshot corrections-ui.png. Test fixture initially unpacked two values from a four-value helper; corrected, all six cases passed. One upstream Starlette/httpx warning. Temporary database/server/tab only; no real rights/professional decisions, source acquisition, paid resources, production, inference, billing/SMS or notifications.

Limits: administrative closure is not independent approval. Latest-500 source picker and latest-50 UI events; API events paginated. Source disable relies on existing runtime rechecks, cannot recall downloads, and does not yet produce an immutable affected-artifact remediation ledger. Event history is append-only through the API, not tamper-proof against privileged database operators. See docs/EDITORIAL_REVIEWS.md for remaining work.
