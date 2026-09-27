# Complete Codex execution queue

Master #5; first task #6. There are **38 actionable tasks plus the master issue**. Issues #5–#40 were created for this handoff; the three existing SEC issues were expanded. PR #4 is a separate draft code review. No tasks were scheduled for unattended execution.

## Foundation

| Issue | Task |
|---|---|
| #6 | Reconcile the complete v0.7 archive, existing main and PR #4; clean install and CI |
| #7 | Operation-level rights, scoped fair-use review and publisher permission packets |
| #8 | Unified permitted acquisition, immutable versions and source coverage accounting |

## Content retrieval — every family, not just SEC

Each issue includes official discovery URLs, permitted acquisition approach, exact locators/version fields, rights limits, dependencies and acceptance criteria. A root URL is a discovery seed, not a preapproved crawler.

| Issue | Content families | Default approach |
|---|---|---|
| #1 | S-X, S-K, Regulation G, SABs, FRM, CFIs and official forms | Official APIs/downloads, artifact/locator review; complete the excerpt-only seed |
| #2 | EDGAR filings, comment-response threads, XBRL and notes datasets | Declared issuer/period pilot; original disclosure and thread/context provenance |
| #3 | SEC independence/OCA/disclosure guidance, AAERs and reporting releases | Original guidance/orders/complaints/dispositions; distinguish procedural state |
| #9 | FASB ASC, ASUs, Concepts and implementation material | References/original analysis; body operations only after scoped clearance |
| #10 | GASB statements/codification/implementation guidance | References and permission-gated imports; distinguish federal FASAB |
| #11 | PCAOB standards, inspections and enforcement | Authorized/manual route; Public Materials reuse is not automated-crawl permission |
| #12 | AICPA AU-C/AT-C/AR-C, ethics, quality and guides | Reference-only until suitable public-AI/service rights |
| #13 | IASB/ISSB, IFRS/IAS, interpretations, SMEs and adoption | Licensed operations; editions, local adoption and languages kept distinct |
| #14 | IAASB, IESBA and IPSASB | Board/work/edition-specific owner and permission verification |
| #15 | GAO Yellow/Green Books, FASAB, OMB and Treasury | Source-cleared official downloads with notices, version and paragraph/table checks |
| #16 | Federal law, official opinions and state/local law | Official bulk/API/court sources; no proprietary headnotes/citators |
| #17 | COSO, IIA, ISACA/COBIT and NIST | Proprietary references/AI-specific permission; separate government source route |
| #18 | Big Four, other firms and commercial literature | Metadata and original analysis; no DART/paid-source AI bypass |
| #19 | Open textbooks, academic articles and contributions | Verify each actual version/license; DOI/open visibility is not full-text permission |
| #20 | Banking, tax, nonprofit and industry regulators | Declared regulator/report/year pilots; private NAIC sources need rights |
| #21 | National frameworks, endorsements and translations | Jurisdiction/language-specific rights, adoption and specialist review |
| #22 | All 63 existing original items plus topic-depth expansion | Hash-preserving disposition, actual source maps, original cases/templates and real review |

Private uploaded contracts/memos/workpapers/reports are a separate workspace-only source family under #24/#29/#31/#34, not public corpus contributions.

## Remaining engineering and product work

| Issue | Task |
|---|---|
| #23 | Independent editorial/rights/applicability review and generated progress |
| #24 | Secure HTML/XML/PDF/DOCX/XLSX/CSV parsing, tables, OCR fallback and exact locators |
| #25 | Hybrid retrieval, authority relationships, tenant/rights/date filtering and citations |
| #26 | Actual Gemini 3.8 Flash Cloud contract, structured tools, retention and costs |
| #27 | Production identity bundle, real TOTP/SMS MFA, sessions and controlled recovery |
| #28 | GCP infrastructure, PostgreSQL workers/migrations, CI/CD and rollback |
| #29 | Privacy, upload security, tenant isolation, prompt injection and deletion/retention |
| #30 | Free/paid boundary and verified US$89.99 annual Stripe lifecycle |
| #31 | Five core Agent workflows, durable execution and evidence-backed results |
| #32 | Policy, revenue, lease, close and framework-comparison Agents |
| #33 | Disclosure, benchmarking, SEC-response, audit-prep and controls Agents |
| #34 | Workspaces, review collaboration, revision-safe memo editor and exports |
| #35 | Responsive product screens, accessibility and real browser journeys |
| #36 | Professional benchmark tooling, adjudication and regression gates |
| #37 | Opt-in standards-impact watches and consented notifications |
| #38 | Observability, cost controls, source freshness, restore and support |
| #39 | Open-source notices, contributor/developer guides and reproducible releases |
| #40 | Operator-approved scoped release and actual production acceptance |

## Sequencing

Start #6, then #7/#8 and independent #26–#29 work. Build #23–#25/#36 while metadata/source discovery and #22 original-content audit proceed. Core #1 and government/open-source candidates #15/#16/#19 are useful acquisition lanes. Restricted families can complete references, request packets and synthetic adapter tests without granting themselves text rights. #2/#3 use the validated pipeline; task-specific Agents consume only approved relevant source slices. Later frameworks do not block a deliberately limited truthful launch.

Use `tasks/queue.json` in the maintainer's handoff for explicit implementation dependencies. Live issue bodies remain authoritative; re-read them before each task.

## Completion is evidence, not counts

Every PR updates progress.md: declared universe/unit; inventoried; original artifacts acquired; parsed with exact locators; rights cleared; genuinely technically reviewed; applicability reviewed; indexed; evaluated; current/stale; actual test commands/results; source/model versions; blockers; next resumable step.

Do not add overlapping part/section/passage counts as one completeness percentage. Do not call unreviewed original drafts, hyperlinks or selected excerpts complete standards coverage. A second model pass, mock user or historical test log is not professional review or new live validation.
