# Model budget validation — 2026-09-27

All approvals, budgets, provider responses and costs are synthetic. No real budget
was authorized, no credentials acquired and no Cloud inference/resource/deployment
operation performed. Scope and limitations: `docs/MODEL_BUDGETS.md`.

- `initial.log/xml`: ledger regression — **26 passed** after adding explicit synthetic budgets.
- `targeted.log/xml`: `backend/.venv/bin/python -m pytest backend/tests/test_model_budgets.py backend/tests/test_model_attempts.py --junitxml=reports/model-budgets/targeted.xml` — **48 passed** before final expiry cases.
- `final-targeted.log/xml`: budget-only suite — **23 passed** before the additional expired-catalog case.
- `backend.log/xml`: final `backend/.venv/bin/python -m pytest backend/tests --junitxml=reports/model-budgets/backend.xml` — **575 passed / 14 skipped**, Python 3.11.9. All 24 budget cases passed. Earlier full runs were 573/13, 573/14 and 574/14 while cases/contracts were added; final logs replace them.
- `postgres-migrations.log`: `OSA_MIGRATION_TEST_DATABASE_URL=<empty disposable UTF-8 PostgreSQL database> backend/.venv/bin/python scripts/check_migrations.py` — preserved existing output ledger and an unknown pre-budget model receipt without fabricating authorization; schema parity/downgrade/re-upgrade passed; **34 tables**.
- `postgres.log/xml`: final `OSA_POSTGRES_TEST_URL=<migrated disposable database> OSA_DISPOSABLE_TEST_DATABASE=true backend/.venv/bin/python -m pytest backend/tests/test_intake_postgres.py --junitxml=reports/model-budgets/postgres.xml` — **14 passed**, PostgreSQL 17.11. A new two-process race admits one call against a one-reservation envelope. The prior 14-case run also passed. Local PostgreSQL stopped after validation.
- Changed-module Ruff F; actual API contract regeneration; content/hash/queue/generated-progress checks; publication heuristic — passed. The latter checks configured sensitive patterns and is not a complete security audit.

The client and spawned-worker fixtures explicitly supply synthetic quote
freshness, so future clean builds don't depend on an old calendar cutoff. A
separate negative test verifies expired-catalog rejection. No production freshness
override is added. There were no test failures. One nonexistent example-file read
and one failed documentation patch context were corrected; no files were silently
overwritten. One upstream Starlette/httpx warning remains. CI covers clean
frontend/MFA assets, Python 3.11/3.13, PostgreSQL and Docker; no new local browser or
live identity/model outcome is claimed.

Model context/output bounds were re-read in the official Cloud guide on 2026-09-27.
This is a linked public-document observation, not raw artifact acquisition or
project-access evidence. Requested model `gemini-3.8-flash`, REST v1,
`google-auth 2.58.1`, `requests 2.34.2`; dated price catalog
`google-cloud-gemini-3.8-flash-standard-2026-09-27`. All source pack revisions and
parser `source-intake-1/sec-core-0.7.0` remain unchanged.
