# Exact publication dependency validation (#23)

Full regression observed **772 passed / 21 optional PostgreSQL skipped**, including the first 14 dependency cases. Final targeted dependency run **16 passed**, after adding mandatory-attribution and saved-export/retrieval cases plus attribution withholding. Receipts: dependencies-backend.xml and dependencies-targeted.xml. Final SEC integration rerun: **9 passed**, after adding dependency-context checks to the SEC retrieval path. CI checks the final full tree separately.

Earlier targeted run exposed three expected positive-fixture failures after metadata-only references ceased granting admission. Added explicit synthetic reviewed publication bindings to those positive fixtures. A subsequent run exposed an applicability-history count that included the newly added dependency review; corrected the assertion to count the parent source's records. No genuine approval/acquisition occurred. One upstream Starlette/httpx warning remains.

Commands observed:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_content_library.py backend/tests/test_applicability.py -q
backend/.venv/bin/python -m pytest backend/tests/test_dependencies.py backend/tests/test_applicability.py backend/tests/test_content_library.py -q
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/dependencies-backend.xml
backend/.venv/bin/python -m pytest backend/tests/test_dependencies.py -q --junitxml=reports/intake/dependencies-targeted.xml
backend/.venv/bin/python -m pytest backend/tests/test_sec_core_integration.py -q
backend/.venv/bin/python -m ruff check backend/app backend/tests/dependency_fixtures.py backend/tests/test_dependencies.py --select F
backend/.venv/bin/python scripts/export_contracts.py
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
```

No schema change or new local PostgreSQL/frontend/browser/live-provider assertion. All added source text, identities, attestations and rights are synthetic. Binding a fixture to a real reference ID tests software behavior only; it is not primary evidence for that reference.

Tests cover missing exact bindings, source disablement, revision/policy/rights/technical changes, output-control/notice withholding, invalid/self/partial/duplicate/stale bindings, dependency applicability and saved evidence/retrieval invalidation. Actual all-family coverage remains unchanged. Limits: binding picker, propagated output budgets/notices, corpus-scale impact reports and actual primary-source review remain. No paid resource, production, live billing/SMS or external notification.

Implementation bad45bc7db057821f22532fd18262e9f4bb96782 passed main CI 36359874953: Python 3.11/3.13 clean installs, frontend/backend, migrations/PostgreSQL and Docker.
