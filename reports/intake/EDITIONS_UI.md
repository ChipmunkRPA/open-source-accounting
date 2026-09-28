# Multipart inventory UI validation — #8 / #23

Scope: source administrator `/editions` screen; no backend/schema/provider changes. Parent #5. Work directly on main per operator direction.

Observed local commands (2026-09-27):

- `npm --prefix frontend run typecheck` — passed.
- `npm --prefix frontend run test:auth` — 16 passed, zero failures.
- `npm --prefix frontend run build` — passed; local Identity Platform bundle produced.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_intake_editions.py -q --junitxml=reports/intake/editions-ui-targeted.xml` — 23 passed, zero failures; one upstream Starlette/httpx deprecation warning.

Browser: disposable local SQLite/demo identity, mock provider, loopback port 8782. Member denied scoped administration. Administrator created inventory revision 1 with one acquired synthetic component and one missing required appendix; report showed 1/2 required receipts. Saved revision 2 explicitly making the appendix optional, report showed 1/1 required and 0/1 optional with no complete-publication/approval claim. Inspected revision 1: historical warning, preserved 1/2 count, disabled Prepare next revision, and link to current revision. Existing extraction remained pending. Screenshot `editions-ui.png` contains synthetic data only. The prior temporary tab was automatically closed at turn end; reopened the same running demo and verified persisted revisions before saving the screenshot.

These are synthetic browser/API checks, not independent accounting review, live identity, source acquisition or GCP validation. No production database, source body, provider or paid resource was accessed. No new genuine acquisition, parsing, rights, technical/applicability approval, indexing or adjudicated evaluation coverage.

Limits: declared inventories are not independently verified publisher inventories. Real full-edition artifacts, byte/table reconciliation, professional approvals and corpus-scale measurements remain outstanding. CI evidence will be recorded after the implementation commit completes.
