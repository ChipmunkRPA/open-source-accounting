# General applicability interface (#23)

Observed: TypeScript typecheck, 16 mocked auth tests, real Identity Platform production build and 23 applicability API tests passed. One upstream Starlette/httpx warning; no failures. No backend/schema change in this slice, so no new local full-regression or PostgreSQL count is claimed.

Commands:

```sh
npm --prefix frontend run typecheck
npm --prefix frontend run test:auth
npm --prefix frontend run build
backend/.venv/bin/python -m pytest backend/tests/test_applicability.py -q --junitxml=reports/intake/applicability-ui-backend.xml
backend/.venv/bin/python scripts/check_content.py
backend/.venv/bin/python scripts/check_queue.py
backend/.venv/bin/python scripts/content_progress.py --check
backend/.venv/bin/python scripts/sec_core_progress.py --check
backend/.venv/bin/python scripts/release_preflight.py --check
```

Browser: temporary localhost SQLite/mock server, synthetic comparison draft reused as a general review source. Opened Review applicability, entered synthetic scope/findings/evidence/expiry and submitted Request changes. Verified saved notice, disabled form/submission and private history reporting no current approval. Screenshot applicability-ui.png. Server/tab stopped. All fixtures excluded from real coverage. No professional approval occurred.

Scope: general/original/intake sources; SEC retains its separate workflow. Conditional records do not admit automated evidence. Server enforces rights, role, revision and review prerequisites. No actual approval, full accessibility, corpus-scale usability, download completion or live identity/provider behavior is proven by this browser journey. Those gates remain open.

Implementation 4508648ad9f608b80904228bf97cc11af2f46c48 passed main CI 36359115320: Python 3.11/3.13 clean installs, frontend/backend, migrations/PostgreSQL and Docker.
