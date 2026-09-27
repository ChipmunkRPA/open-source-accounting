# Durable model-attempt validation — 2026-09-27

All model responses, usage, charges, accounts and reviewers are synthetic. No
Cloud credentials were discovered, inference sent, resources provisioned or
actual operator approval asserted. Exact application behavior and remaining
spending/retention gates: `docs/MODEL_ATTEMPTS.md`.

- `initial.log/xml`: `backend/.venv/bin/python -m pytest backend/tests/test_api_workflows.py backend/tests/test_runtime_rights.py backend/tests/test_gemini_contract.py --junitxml=reports/model-ledger/initial.xml` — **113 passed**.
- `targeted.log/xml`: `backend/.venv/bin/python -m pytest backend/tests/test_model_attempts.py --junitxml=reports/model-ledger/targeted.xml` — **24 passed**. An earlier 21-case run also passed. Two further cases are included in the final full suite.
- `backend.log/xml`: final `backend/.venv/bin/python -m pytest backend/tests --junitxml=reports/model-ledger/backend.xml` — **551 passed / 13 skipped**, Python 3.11.9. All 26 new ledger cases passed. Intermediate full runs were 549/12, 550/12 and 551/12 while cases were added; the final receipts replace those logs.
- `postgres-migrations.log`: `OSA_MIGRATION_TEST_DATABASE_URL=<empty disposable UTF-8 PostgreSQL database> backend/.venv/bin/python scripts/check_migrations.py` — preserved the prior synthetic output ledger through upgrade; schema parity, downgrade and re-upgrade passed; **33 application tables**.
- `postgres.log/xml`: final `OSA_POSTGRES_TEST_URL=<migrated disposable database> OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py --junitxml=reports/model-ledger/postgres.xml` — **13 passed**, PostgreSQL 17.11 via a local Unix socket. The two new tests prove exclusive dispatch ownership across processes and a stable report snapshot during concurrent completion. Earlier 12- and 13-case runs also passed; final rerun includes a stronger exact-run snapshot assertion. Local PostgreSQL stopped after validation.
- Changed Python modules passed `backend/.venv/bin/ruff check --select F ...`.
- `backend/.venv/bin/python scripts/export_contracts.py` regenerated actual contracts, including the typed admin report.
- `scripts/check_content.py`, `scripts/check_queue.py`, `scripts/content_progress.py --check`, `scripts/sec_core_progress.py --check` passed with the backend Python.
- `backend/.venv/bin/python scripts/release_preflight.py --check` passed with zero configured sensitive-pattern findings. This remains a heuristic, not a full security audit.

No test failures occurred. Initial inspection used several incorrect legacy module
paths; actual files were then found with `rg`. Code review caught the need for
explicit restart IDs, invalid-usage cost withholding and a consistent report
snapshot before publication. No safety test was weakened. One upstream
Starlette/httpx warning remains. No new local frontend/browser/live identity or
Cloud result is claimed; CI covers clean frontend builds, PostgreSQL and Docker.

Model/version: requested `gemini-3.8-flash`, REST v1, `google-auth 2.58.1`,
`requests 2.34.2`; cost catalog `google-cloud-gemini-3.8-flash-standard-2026-09-27`.
Public provider verification is inherited from #50, not rerun or represented as
project access. Source parser remains `source-intake-1/sec-core-0.7.0`; no source
pack revision, acquisition, professional review or production-index admission changed.
