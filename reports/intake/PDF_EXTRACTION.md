# PDF coverage validation — 2026-09-27

Original synthetic PDF fixtures only. No live source acquisition, professional review, OCR/provider call or cloud deployment.

Observed commands:

- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pdf_parser.py backend/tests/test_documents_agents.py backend/tests/test_source_intake.py --junitxml=/tmp/osa-pdf-targeted.xml`: 70 passed in 6.90 seconds after adding workflow coverage metadata.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests --junitxml=/tmp/osa-pdf-backend.xml`: **932 passed / 28 optional PostgreSQL skips / zero failures** in 47.69 seconds. The last image-only-page fixture was added after this run's collection.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pdf_parser.py --junitxml=/tmp/osa-pdf-final.xml`: final **15 PDF cases passed**, 3.22 seconds, including the added image-only fixture.
- `backend/.venv/bin/ruff check --select F backend/app/pdf_parser.py backend/app/services/documents.py backend/app/parse_worker.py backend/app/intake_parse.py backend/app/services/intake.py backend/app/agents/workflows.py backend/tests/test_pdf_parser.py`: passed.
- Actual API/model contract export and unchanged-schema diff, content and queue checks passed: 63 items / 26 references / 58 questions / 3 arithmetic checks; 38-task DAG / 32 family recipes / 63 hashes / 47 topics / 16 workflows.

No test failures observed. One upstream Starlette/httpx warning remains. Initial searches named nonexistent test_documents.py/services/jobs.py/routers/documents.py and services/agents.py; repository discovery located the actual modules. No frontend or schema migration changed; local frontend/PostgreSQL/migration checks were not rerun. Temporary JUnit files are local receipts, not approved source evidence.

Tests cover declared versus physical page labels, full-page hash/chunk ranges, blank/mixed/image-only pages, nested annotation actions and embedded attachments, encryption/page/character limits, private-upload no-row failure, authorized metadata access, raw retention/no partial source extraction, stage/review separation, and Agent preprocessing with new and legacy-unknown coverage. Scope and unresolved visual/layout limits: `docs/PDF_EXTRACTION.md`.
