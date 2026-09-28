# eCFR parser correction validation — 2026-09-27

Original synthetic fixtures only. No content acquisition, real professional review, cloud/model request or deployment.

Observed:

- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_ecfr_parser.py backend/tests/test_source_intake.py backend/tests/test_annual_cfr.py backend/tests/test_sec_core_unit.py --junitxml=/tmp/osa-ecfr-targeted.xml`: **119 passed**, 1.94 seconds.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests --junitxml=/tmp/osa-ecfr-backend.xml`: **918 passed / 28 optional PostgreSQL skips / zero failures**, 46.27 seconds. One upstream Starlette/httpx warning. No failed test run in this slice.
- `backend/.venv/bin/ruff check --select F backend/app/ecfr_parser.py backend/app/intake_parse.py backend/app/services/intake.py backend/tests/test_ecfr_parser.py backend/tests/test_annual_cfr.py`: passed.
- `backend/.venv/bin/python scripts/export_contracts.py` followed by exact schema diff: passed, API/model schemas unchanged.
- `backend/.venv/bin/python scripts/check_content.py`: 63 items / 26 references / 58 questions / 3 arithmetic checks; no professional approval.
- `backend/.venv/bin/python scripts/check_queue.py`: 38-task DAG / 32 family recipes / 63 baseline hashes / 47 topics / 16 workflows.

New coverage: 22 synthetic parser/API cases, including actual old-parser normalized bytes stored alongside a separate version-2 extraction; old object hash/bytes unchanged and retry returns the new extraction. Table headers, empty and numeric cells, captions/notes, exact paths, dangerous XML and unsupported layouts are tested. Historical SEC snapshot replay tests remain passing. Temporary JUnit receipts are local, not legal-source or professional-review evidence.

No frontend or database schema changed; local PostgreSQL/migration/frontend checks were not rerun in this slice. CI results recorded separately when observed. Known limits and operator sequence: `docs/ECFR_PARSER.md`.
