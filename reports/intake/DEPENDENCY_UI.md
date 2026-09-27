# Exact dependency binding interface (#23)

Observed: TypeScript typecheck, 16 mocked auth tests, real Identity Platform production build and 16 dependency API tests passed. No new local full-backend/PostgreSQL/migration result is asserted; changes are frontend only. One upstream Starlette/httpx warning remains.

Commands:

```sh
npm --prefix frontend run typecheck
npm --prefix frontend run test:auth
npm --prefix frontend run build
backend/.venv/bin/python -m pytest backend/tests/test_dependencies.py -q --junitxml=reports/intake/dependency-ui-backend.xml
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
```

Browser: temporary localhost SQLite/mock app with two synthetic drafts and one synthetic reference. Selected the other staged source, verified exact literal text/edition/locator/revision and the missing-approval warning. Submission without relationship confirmation was rejected. Confirmed the synthetic relationship and saved a request-changes decision. Private history retained reference ID, target source ID, exact revision/policy/locator. No current technical approval. Raw JSON history clipped long lines; replaced with readable cards and expandable wrapped JSON, rebuilt and repeated the successful journey. Screenshot dependency-ui.png. Temporary servers/tabs stopped. No actual professional review or source acquisition; fixtures excluded from coverage.

Limits: picker uses existing bounded editorial worklist; broader source search/pagination and corpus-scale accessibility remain. Current binding controls do not unblock inherited output controls/mandatory notices: runtime continues withholding those dependencies pending derived-output accounting. Browser download completion remains unverified. No paid resources, production or live inference/billing/SMS/notifications.

Implementation 6ef2a736a89a9a7c8b74c57c8c5994f30856ed81 passed main CI 36360220468: Python 3.11/3.13 clean installs, frontend/backend, migrations/PostgreSQL and Docker. Content/hash/queue/generated-progress/publication checks also passed locally.
