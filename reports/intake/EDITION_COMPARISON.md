# Immutable inventory comparison — #8 / #23

Selected and immediate-predecessor inventory declarations are compared by exact IDs and hashes. Added/removed/changed components, all persisted per-component fields (including known delivery hashes), ordering, required/optional counts, scope notes and separate combined representations are exposed. Required removals and required-to-optional changes are explicit. Initial declarations do not imply acquisition. Missing/inconsistent predecessors or tampered manifests fail closed. Later policy/delivery/review state is not reconstructed or confused with the frozen declaration.

Actual local validation, 2026-09-27:

- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_edition_comparison.py backend/tests/test_intake_editions.py -q --junitxml=reports/intake/edition-comparison-targeted.xml` — **34 passed** (11 new comparison cases), no failures/skips.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests -q --junitxml=reports/intake/edition-comparison-backend.xml` — **867 passed / 28 optional PostgreSQL skipped**, no failures/errors. One upstream Starlette/httpx warning.
- `npm --prefix frontend run typecheck` and `npm --prefix frontend run build` — passed after fixing three initially missing callback type annotations. Repeated after human-readable field labels; passed.
- `backend/.venv/bin/ruff check backend/app/services/editions.py backend/app/api/intake.py backend/tests/test_edition_comparison.py --select F` — passed.
- `backend/.venv/bin/python scripts/export_contracts.py` — actual OpenAPI updated.

Browser: disposable SQLite, local demo administrator, mock provider, synthetic acquired component and missing appendix. Inspected revision 2 versus revision 1; verified required count 2 → 1, optional 0 → 1, appendix warning, exact hashes, changed scope text and required true → false. This is not real acquisition/review evidence. Final screenshot `edition-comparison-ui.png`; demo server stopped and tab closed. No schema changes or newly claimed local PostgreSQL/migration execution.

Real content coverage remains unchanged: 32 families / 47 topics; 63 draft original items / 0 professional approvals / 0 Agent admissions. SEC 34 targets / 28 selected excerpts / 7 excerpted sources / 0 complete original HTTP artifacts / 0 technical or applicability approvals / 0 approved production index / 0 human-adjudicated evaluations. Government packets: 17 overlapping metadata candidates / 3 families / 0 new acquisition/parsing/rights/review/index additions. Synthetic fixtures excluded. Parser source-intake-1/sec-core-0.7.0; discovery html-index-1/crossref-works-1; requested gemini-3.8-flash unchanged, no model calls.

Remaining: actual authorized complete artifacts, independently verified publisher inventories, professional reviews, corpus-scale reconciliation and production cloud/provider evidence. No rights, review or deployment approval fabricated. CI pending publication.
