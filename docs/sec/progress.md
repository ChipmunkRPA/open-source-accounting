<!-- SEC-CORE:START -->

## SEC source development — 0.7.0, September 27, 2026

**Current slice:** source-reading preview, explicit intake commands, exact locators, and integration with the existing review gates. SEC Core is not complete.

**34 source targets; 7 sources with selected excerpts; 28 excerpts (3,514 words).**

Zero complete source documents, zero original HTTP artifacts, zero independently reviewed sources, and zero Agent-approved SEC passages in the shipped seed. Transcribed official-source excerpts are not raw downloads. Original educational content counts remain separate.

| Collection | Inventoried targets | Sources excerpted | Excerpts | Complete documents | Agent approved |
|---|---:|---:|---:|---:|---:|
| cfi | 2 | 1 | 12 | 0 | 0 |
| forms | 9 | 1 | 2 | 0 | 0 |
| frm | 11 | 2 | 4 | 0 | 0 |
| reg_g | 1 | 0 | 0 | 0 | 0 |
| reg_sk | 2 | 1 | 6 | 0 | 0 |
| reg_sx | 1 | 0 | 0 | 0 | 0 |
| sab | 8 | 2 | 4 | 0 | 0 |

Catalog target units overlap and vary in size; these counts are not a percentage of all SEC coverage. Successfully parsing a source does not establish technical accuracy or effective dates.

### Ordered work queue

| Position | Workstream | State | Dependency |
|---:|---|---|---|
| 1 | [SEC-CORE #1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1) | in_progress | None |
| 2 | [SEC-PRACTICE #2](https://github.com/ChipmunkRPA/open-source-accounting/issues/2) | in_progress | SEC-CORE |
| 3 | [SEC-AUDIT-ENFORCEMENT #3](https://github.com/ChipmunkRPA/open-source-accounting/issues/3) | queued | SEC-CORE, SEC-PRACTICE:pilot |

**Queued means a GitHub development issue, not unattended execution.** No scheduled crawler, cloud job, future delivery or billing action was enabled.

### Implementation and release gates

- [x] Add government-host catalog, normalized excerpt hashes and per-passage provenance.
- [x] Implement read-only FTS preview, public API and `/sec-core` frontend.
- [x] Implement explicit bounded HTTP intake, conservative parsers and raw/snapshot storage.
- [x] Reparse and hash-check acquired snapshots before idempotent database staging.
- [x] Keep rights/technical approval separate; preserve exact locators in Agent retrieval.
- [x] Add privileged revision-bound applicability review; never use import date as effective date.
- [x] Create GitHub issues #1, #2, #3 with acceptance criteria and dependencies.
- [ ] Complete native publication of the earlier full application; addon publication alone is insufficient.
- [ ] Acquire and validate complete Core source publications; live network intake blocked in this environment.
- [ ] Review HTML selectors, PDF/table layouts and citation completeness against actual full sources.
- [ ] Exercise the shared PostgreSQL rate budget and controlled egress on deployed infrastructure.
- [ ] Perform real independent rights, technical and historical-applicability reviews.
- [ ] Validate authorized persistent retrieval on the real corpus; PostgreSQL lexical GIN has a 10,001-source synthetic fixture, while scoped/semantic retrieval and adjudicated recall remain open.
- [ ] Create professionally adjudicated accounting/citation benchmarks and source-update monitoring.

Observed local checks: 248 Python tests passed (203 baseline + 45 new); TypeScript typecheck and demo build passed. Mocked acquisition/reviewer fixtures are not live downloads or real professional approvals. No live Gemini, Identity Platform, PostgreSQL or cloud deployment was performed.

Commands: `PYTHONPATH=backend python -m app.sec_core validate`; `python scripts/sec_core_progress.py --write`; `python scripts/sec_core_progress.py --check`. Full details: `docs/sec/README.md`.

<!-- SEC-CORE:END -->
