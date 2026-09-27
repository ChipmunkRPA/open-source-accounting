# Codex issue index

Live master queue: [#5](https://github.com/ChipmunkRPA/open-source-accounting/issues/5). Baseline task [#6](https://github.com/ChipmunkRPA/open-source-accounting/issues/6) is complete and integrated into main (2026-09-27); use `queue.json` and live issues for remaining status.

**38 actionable tasks + 1 master issue.** The three existing SEC tasks were expanded; issues #5–#40 were created for this handoff. The original PR #4 and handoff PR #41 were reconciled into main through PR #53; their former draft status is historical.

Priorities indicate importance, not a flat execution sequence. Respect dependencies. Metadata discovery, licensing-packet drafting and synthetic tests can run independently; actual rights/human approvals never become implied.

| Issue | ID | Priority | Workstream | Implementation dependencies |
|---|---|---|---|---|
| [#1](https://github.com/ChipmunkRPA/open-source-accounting/issues/1) | `SEC_CORE` | P1 | Complete SEC Core | #6, #7, #8 |
| [#2](https://github.com/ChipmunkRPA/open-source-accounting/issues/2) | `SEC_PRACTICE` | P2 | SEC filings, correspondence and structured facts | #1, #8 |
| [#3](https://github.com/ChipmunkRPA/open-source-accounting/issues/3) | `SEC_AUDIT_ENFORCEMENT` | P2 | SEC audit guidance and enforcement | #1, #2, #8 |
| [#6](https://github.com/ChipmunkRPA/open-source-accounting/issues/6) | `BOOTSTRAP` | P0 | Reconcile full v0.7 source, PR #4 and clean-install CI | None |
| [#7](https://github.com/ChipmunkRPA/open-source-accounting/issues/7) | `RIGHTS` | P0 | Operation-level permissions and licensing | #6 |
| [#8](https://github.com/ChipmunkRPA/open-source-accounting/issues/8) | `INGEST` | P0 | Unified acquisition and immutable source registry | #6, #7 |
| [#9](https://github.com/ChipmunkRPA/open-source-accounting/issues/9) | `FASB` | P1 | FASB ASC references, ASUs and permission-gated text | #7, #8 |
| [#10](https://github.com/ChipmunkRPA/open-source-accounting/issues/10) | `GASB` | P2 | GASB governmental-accounting references | #7, #8 |
| [#11](https://github.com/ChipmunkRPA/open-source-accounting/issues/11) | `PCAOB` | P1 | PCAOB standards, inspections and enforcement | #7, #8 |
| [#12](https://github.com/ChipmunkRPA/open-source-accounting/issues/12) | `AICPA` | P1 | AICPA nonissuer standards and guides | #7, #8 |
| [#13](https://github.com/ChipmunkRPA/open-source-accounting/issues/13) | `IFRS` | P1 | IASB/ISSB standards and adoption history | #7, #8 |
| [#14](https://github.com/ChipmunkRPA/open-source-accounting/issues/14) | `INTL_ASSURANCE` | P2 | IAASB, IESBA and IPSASB | #7, #8 |
| [#15](https://github.com/ChipmunkRPA/open-source-accounting/issues/15) | `GOVERNMENT` | P1 | GAO, FASAB, OMB and Treasury | #7, #8 |
| [#16](https://github.com/ChipmunkRPA/open-source-accounting/issues/16) | `LEGAL` | P1 | Official law and judicial opinions | #7, #8 |
| [#17](https://github.com/ChipmunkRPA/open-source-accounting/issues/17) | `CONTROLS` | P2 | COSO, IIA, COBIT and government IT guidance | #7, #8 |
| [#18](https://github.com/ChipmunkRPA/open-source-accounting/issues/18) | `PUBLISHERS` | P2 | Big Four and commercial literature | #7, #8 |
| [#19](https://github.com/ChipmunkRPA/open-source-accounting/issues/19) | `OPEN_LITERATURE` | P1 | Open textbooks, papers and contributions | #7, #8 |
| [#20](https://github.com/ChipmunkRPA/open-source-accounting/issues/20) | `REGULATORS` | P2 | Banking, tax, nonprofit and industry regulators | #7, #8 |
| [#21](https://github.com/ChipmunkRPA/open-source-accounting/issues/21) | `LOCAL_FRAMEWORKS` | P3 | National standards, adoption and translations | #7, #8, #13, #14 |
| [#22](https://github.com/ChipmunkRPA/open-source-accounting/issues/22) | `ORIGINAL_CONTENT` | P1 | Review every item and deepen topic coverage | #6 |
| [#23](https://github.com/ChipmunkRPA/open-source-accounting/issues/23) | `EDITORIAL` | P0 | Review administration and progress tracking | #6, #7, #8 |
| [#24](https://github.com/ChipmunkRPA/open-source-accounting/issues/24) | `PARSERS` | P0 | Secure multiformat parsing and exact locators | #6, #7, #8 |
| [#25](https://github.com/ChipmunkRPA/open-source-accounting/issues/25) | `RETRIEVAL` | P0 | Scalable search and evidence verification | #6, #7, #8, #23, #24 |
| [#26](https://github.com/ChipmunkRPA/open-source-accounting/issues/26) | `GEMINI` | P0 | Verify requested model on Google Cloud | #6, #7 |
| [#27](https://github.com/ChipmunkRPA/open-source-accounting/issues/27) | `MFA` | P0 | Real TOTP/SMS authentication and recovery | #6 |
| [#28](https://github.com/ChipmunkRPA/open-source-accounting/issues/28) | `GCP` | P0 | Cloud infrastructure and deployment pipeline | #6 |
| [#29](https://github.com/ChipmunkRPA/open-source-accounting/issues/29) | `SECURITY` | P0 | Privacy, workspace isolation and security | #6 |
| [#30](https://github.com/ChipmunkRPA/open-source-accounting/issues/30) | `BILLING` | P0 | Annual Agent subscription and free boundary | #6, #27 |
| [#31](https://github.com/ChipmunkRPA/open-source-accounting/issues/31) | `CORE_AGENTS` | P1 | Five primary Agent workflows | #6, #7, #24, #25, #26, #30 |
| [#32](https://github.com/ChipmunkRPA/open-source-accounting/issues/32) | `ACCOUNTING_AGENTS` | P2 | Accounting policy, revenue, lease, close and comparison Agents | #31 |
| [#33](https://github.com/ChipmunkRPA/open-source-accounting/issues/33) | `AUDIT_DISCLOSURE_AGENTS` | P2 | Disclosure and audit/control Agents | #31 |
| [#34](https://github.com/ChipmunkRPA/open-source-accounting/issues/34) | `MEMOS_WORKSPACES` | P1 | Editors, review collaboration and exports | #6, #7, #27, #29 |
| [#35](https://github.com/ChipmunkRPA/open-source-accounting/issues/35) | `UI_UX` | P1 | Complete responsive screens and browser journeys | #6 |
| [#36](https://github.com/ChipmunkRPA/open-source-accounting/issues/36) | `EVALUATION` | P0 | Professional benchmarks and regression gates | #6, #23, #25 |
| [#37](https://github.com/ChipmunkRPA/open-source-accounting/issues/37) | `WATCHES` | P2 | Standards change and consented impact monitoring | #8, #23, #25, #30 |
| [#38](https://github.com/ChipmunkRPA/open-source-accounting/issues/38) | `OPERATIONS` | P1 | Observability, costs, freshness, restore and support | #28, #29 |
| [#39](https://github.com/ChipmunkRPA/open-source-accounting/issues/39) | `OPEN_SOURCE` | P1 | Contributor, licensing and reproducible release docs | #6, #7 |
| [#40](https://github.com/ChipmunkRPA/open-source-accounting/issues/40) | `RELEASE` | P0 | Operator-approved scoped production release | #6, #7, #8, #23, #24, #25, #26, #27, #28, #29, #30, #31, #34, #35, #36, #38, #39 |

## Suggested execution lanes

1. **Foundation:** #6, then #7/#8; begin #27/#28/#29/#26 in parallel where environments permit.
2. **Evidence platform:** #23/#24/#25/#36; source metadata and original content audit #22 can run alongside.
3. **Core and non-SEC sources:** #1 and #15/#16/#19 first full-text candidates; #9–#14/#17/#18 build truthful reference layers and license packets while blocked.
4. **Product:** #30/#31/#34/#35; #2/#3 unlock real SEC practice and audit examples.
5. **Expansion:** #32/#33/#37 and #10/#14/#20/#21 within declared rights/specialist capacity.
6. **Release:** #38/#39/#40; ship only the reviewed, tested scope and keep later work queued.

The live issue body is the authoritative acceptance checklist. This local index is a transport snapshot; re-read current issues and user changes before execution.
