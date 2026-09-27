# Parser-review workbench validation (#23)

Observed backend **717 passed / 20 optional PostgreSQL skipped**, with **6 new worklist cases**. Combined worklist/parser targeted run **24 passed**. JUnit: parser-ui-backend.xml and parser-ui-targeted.xml. No Python test failures; one upstream Starlette/httpx warning remains.

Frontend typecheck initially failed on a nullable child passed to replaceChildren. Replaced it with a conditional array spread. Then typecheck, **16 mocked auth cases**, and the real production Identity Platform bundle passed. No PostgreSQL/schema change; no new local migration or PostgreSQL result is asserted.

Commands actually run:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_parser_review_listing.py backend/tests/test_parser_review.py -q --junitxml=reports/intake/parser-ui-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/parser-ui-backend.xml
backend/.venv/bin/python scripts/export_contracts.py
backend/.venv/bin/python -m ruff check backend/app/api/library.py backend/tests/test_parser_review_listing.py --select F
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
# From frontend:
npm run typecheck
npm run test:auth
npm run build
```

Manual browser: isolated temporary SQLite/mock app at 127.0.0.1:8779, synthetic XML and seeded local test reviewer. Opened Parser review, inspected exact hashes/locator/plain text, explicitly checked the single passage, filled synthetic scope/findings/private evidence reference/hash/expiry, submitted changes_requested and verified the saved decision/history. The success button stayed disabled pending reload. Screenshot parser-ui.png. No real review, real MFA, external source acquisition or paid provider call occurred. Closed temporary server/tab afterward.

The browser journey covers one synthetic passage, not a full accessibility audit or large-corpus usability assessment. Pagination bounds/metadata-only reads/role restriction and dynamic export permissions are API-tested. Raw/JSON download completion was not re-tested; the earlier download-event timeout remains unresolved, not a pass. Runtime downloads re-request the authorized packet and refuse changed revisions. File-path reads initially used two nonexistent paths and were corrected without edits.
