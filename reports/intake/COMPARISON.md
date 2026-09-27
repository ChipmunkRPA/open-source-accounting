# Exact revision comparison validation (#23)

Observed full backend **730 passed / 20 optional PostgreSQL skipped**, including **13 new comparison cases**. Initial targeted run **10 passed**; added intake identity/renumbering and SEC identity cases before full regression. JUnit: comparison-backend.xml and comparison-targeted.xml. No failures. One upstream Starlette/httpx deprecation warning remains.

Frontend typecheck, **16 mocked auth cases** and production Identity Platform bundle passed. No database schema change; no new local PostgreSQL/migration result is asserted. CI covers clean installs, real frontend, migrations/PostgreSQL and Docker separately.

Commands actually run:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_review_comparison.py -q --junitxml=reports/intake/comparison-targeted.xml
backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/comparison-backend.xml
backend/.venv/bin/python -m ruff check backend/app/services/review_comparison.py backend/app/editorial_schemas.py backend/app/api/library.py backend/tests/test_review_comparison.py --select F
backend/.venv/bin/python scripts/export_contracts.py
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

Manual browser: temporary local SQLite/mock app with two explicitly related synthetic drafts. Selected version 1 as baseline for version 2. Verified exact before/after line 2, edition/title changes, reference metadata/hash changes, both body hashes and no-approval notice. Screenshot comparison-ui.png. No actual accounting, rights or professional review occurred; synthetic fixtures are excluded from content coverage. Stopped temporary server/tab afterward.

Limits: comparison is bounded, display-only and requires current display rights for both versions. No URL-based equivalence, renumbering inference, historical-body reconstruction, source acquisition or approval propagation. Large corpus usability and full accessibility are not proven by one synthetic browser journey. Prior download completion remains unverified and was not retested here.

Implementation c036b4d43b22af818fcea7f772f3b1828d16d361 passed main CI 36358193754: Python 3.11/3.13 clean installs, real frontend, backend, migrations/PostgreSQL and Docker. Prior documentation main 9fb642e passed CI 36357937313.
