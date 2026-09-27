# Runtime rights validation · 2026-09-27

Synthetic source/reviewer/provider fixtures only. No source acquisition, license,
independent professional approval, live inference or Cloud request occurred.

Commands actually run:
- `cd backend && .venv/bin/python -m pytest`: initial regression, 334 passed / 2 skipped.
- `cd backend && .venv/bin/python -m pytest tests/test_runtime_rights.py`: final targeted suite, 29 passed.
- `cd backend && .venv/bin/python -m pytest --junitxml=../reports/runtime-rights/backend.xml`: full suite, 363 passed / 2 skipped. The optional PostgreSQL tests require a disposable database; local PostgreSQL was not started for this schema-unchanged slice. CI runs them after the migration round trip.
- Ruff F checks on changed runtime/test modules passed after removing two unused imports.
- Actual API contracts regenerated without a contract diff. Content/hash/queue and generated-progress checks passed.

The first targeted run had 10 failures / 12 passes: the test correction response used
an invalid Finding schema and two upload fixtures lacked the required demo subscription.
Those fixtures were corrected; guards were not relaxed. One initial log-redirection
command failed before pytest started because the report directory was created under
the wrong working directory; rerunning from the repository root fixed that path.
The upstream Starlette/httpx deprecation warning remains. Python 3.11.9 locally.
