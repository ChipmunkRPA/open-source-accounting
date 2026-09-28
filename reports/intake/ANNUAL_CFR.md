# Annual CFR adapter validation — 2026-09-27

Scope: #8/#24, original synthetic fixtures only, API/normalization changes. No acquired legal artifacts, real independent reviews, model requests or deployments.

Observed commands:

- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_annual_cfr.py backend/tests/test_source_intake.py backend/tests/test_parser_review.py backend/tests/test_parser_review_listing.py backend/tests/test_sec_core_unit.py --junitxml=/tmp/osa-annual-targeted.xml` — 121 passed in 5.00 seconds.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests --junitxml=/tmp/osa-annual-backend.xml` — final 896 passed / 28 optional PostgreSQL skips / zero failures in 51.20 seconds. One upstream Starlette/httpx deprecation warning.
- `backend/.venv/bin/python scripts/export_contracts.py` — passed; actual OpenAPI updated.
- `backend/.venv/bin/ruff check --select F backend/app/annual_cfr.py backend/app/intake_schemas.py backend/app/intake_parse.py backend/app/services/intake.py backend/tests/test_annual_cfr.py` — passed.
- `backend/.venv/bin/python scripts/check_content.py` — 63 items / 26 references / 58 questions / 3 arithmetic checks.
- `backend/.venv/bin/python scripts/check_queue.py` — 38-task DAG / 32 family recipes / 63 hashes / 47 topics / 16 workflows.
- `backend/.venv/bin/python scripts/content_progress.py --check`, `backend/.venv/bin/python scripts/sec_core_progress.py --check`, `backend/.venv/bin/python scripts/release_preflight.py --check`, `git diff --check` — passed.

Failures resolved: initial new test used `text_sha256` instead of existing `sha256`; first full run passed 895 with one legacy-manifest expectation failure. The expectation dynamically included the new nullable field. Evaluating the committed pre-change schema established the historical fixture hash `b99cd83d0f9c224f43930d65bfa1761962bde3c32995726f382c9e2e1373310e`; test now pins that value. No safety check was disabled.

JUnit files are local temporary receipts, not content/reviewer evidence. No frontend or database migration changes; local frontend/migration/PostgreSQL checks were not rerun in this slice. CI validation is recorded separately once observed. Known unsupported layouts and actual acquisition/review gates: `docs/ANNUAL_CFR_PARSER.md` and `progress.md`.
