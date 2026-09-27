# Gemini REST contract validation — 2026-09-27

All provider responses, usage and cost inputs are synthetic. No ADC lookup, live
inference, project access check, paid resources or deployment occurred. Public
documentation observations and remaining gates: `docs/GEMINI_CONTRACT.md`.

- `targeted.log/xml`: `backend/.venv/bin/python -m pytest backend/tests/test_gemini_contract.py backend/tests/test_calculations_model.py --junitxml=reports/gemini/targeted.xml` — **78 passed** before six final response-state cases were added.
- First full regression: **519 passed / 11 PostgreSQL tests skipped**. That log was replaced by the final run below; the observation was retained here.
- `backend.log/xml`: final `backend/.venv/bin/python -m pytest backend/tests --junitxml=reports/gemini/backend.xml` — **525 passed / 11 skipped**, Python 3.11.9. The provider file contributes 64 new cases. All skipped cases require a disposable PostgreSQL instance; none was run locally in this slice. CI runs these with migration/schema checks.
- `backend/.venv/bin/ruff check --select F backend/app/providers backend/app/config.py backend/tests/test_gemini_contract.py` — passed.
- `backend/.venv/bin/python scripts/export_contracts.py` and `git diff --exit-code -- docs/openapi.json docs/analysis.schema.json docs/research-plan.schema.json` — passed; contracts unchanged.
- `backend/.venv/bin/python scripts/check_content.py`, `scripts/check_queue.py`, `scripts/content_progress.py --check`, `scripts/sec_core_progress.py --check` — passed (each run with the backend Python).

No test failure occurred. Two inspection commands referenced nonexistent legacy
module paths, then the actual `backend/app/agents/orchestrator.py` was inspected.
One upstream Starlette/httpx deprecation warning remains. No frontend changes or
new local browser, real identity or live model test is claimed. CI covers clean
frontend installation/build, Python 3.11/3.13, PostgreSQL and the Docker build.

The publication heuristic includes this receipt directory, checks configured
sensitive patterns, and is not a complete security audit. Source/model version:
requested `gemini-3.8-flash`; REST v1; public docs observed 2026-09-27;
`google-auth 2.58.1`, `requests 2.34.2`; price catalog
`google-cloud-gemini-3.8-flash-standard-2026-09-27`. No resolved live model version
or actual token bill exists. Source parser remains `source-intake-1/sec-core-0.7.0`.
