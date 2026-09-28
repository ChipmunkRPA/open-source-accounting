# Inherited publication output rights (#23)

Observed full backend **784 passed / 23 optional PostgreSQL skipped**, including **10 new derived-output cases**. All **23 PostgreSQL tests separately passed**, including inherited-budget concurrent identical and different releases. Initial existing dependency/output tests: 34 passed. Combined targeted run: 41 passed before three additional cases; final derived-only run: 10 passed after extending inherited storage permission checks. JUnit: derived-output-{backend,postgres,targeted,final-targeted}.xml.

Failures: one initial new fixture omitted requires_technical_review, making its expected revocation gate inapplicable; fixed the fixture to represent an actual reviewable source. Two PostgreSQL inherited-output fixtures omitted required publisher; fixed, then all 23 passed. Full backend regression itself passed. An intermediate commentary mistakenly attributed the two PostgreSQL failures to full regression before reading separate logs. One upstream Starlette/httpx warning remains.

Commands observed:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_dependencies.py backend/tests/test_output_rights.py -q
backend/.venv/bin/python -m pytest backend/tests/test_derived_output.py backend/tests/test_output_rights.py backend/tests/test_dependencies.py -q --junitxml=reports/intake/derived-output-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/derived-output-backend.xml
# URL was the existing disposable local Unix-socket database, not production:
OSA_POSTGRES_TEST_URL="$TEST_DATABASE_URL" OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py -q --junitxml=reports/intake/derived-output-postgres.xml
backend/.venv/bin/python -m pytest backend/tests/test_derived_output.py -q --junitxml=reports/intake/derived-output-final-targeted.xml
backend/.venv/bin/python -m ruff check backend/app backend/tests/test_derived_output.py backend/tests/test_intake_postgres.py --select F
backend/.venv/bin/python scripts/export_contracts.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
```

No schema change/new local migration round trip. Existing migrated PostgreSQL database reused and stopped afterward. Browser: temporary localhost SQLite/mock app, synthetic derived commentary and synthetic license/notice. Private technical history displayed the inherited notice, including literal script-like text, and separate current-review message. Screenshot derived-output-ui.png. Server/tab stopped. No actual license, acquisition, professional review or live provider use.

Tests cover inherited per-response/cumulative groups, direct/derived idempotency, revocation and rebinding retaining obligations, stale targets/history integrity, source/private-history notices, run/memo Markdown/HTML exports, old-body history, nested groups and PostgreSQL concurrent releases. Existing export-format tests cover the shared notice renderer separately. This is not corpus-scale graph/deadlock, legal, production, full browser-format or accessibility validation.

Limits: obligations are per staged source/body and declared bindings, not global text similarity detection. All private history may conservatively withhold if an older supporting revision is unavailable. Graph/history bounds fail explicitly. Actual licensing/primary text/reviewers, affected-content reports and all-family coverage remain open. No paid resources, deployment, billing/SMS or external notifications.
