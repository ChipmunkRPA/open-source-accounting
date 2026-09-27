# Electronic audit evidence: trace the data before trusting the analysis

> **AI-assisted editorial draft — not professionally reviewed.** Original educational content, not authoritative guidance. Confirm the framework, reporting period, elections, and source versions before use. All company names and transactions in examples are fictional.

## Current research entry point
PCAOB describes amendments to AS 1105 and AS 2301 concerning technology-assisted analysis, effective for audits of fiscal years beginning on or after December 15, 2025. Its September 2025 policy statement addresses evaluating external electronic information supplied by the company, including understanding the source/process and testing information or relevant controls. Confirm the applicable version for the engagement. [pcaob-tech-amendments; pcaob-electronic-policy]

## Evidence quality
AS 1105 distinguishes the amount of evidence from its relevance and reliability. More rows of data do not automatically repair a relevance or reliability problem. The agent's summary also does not become audit evidence merely because it contains a citation. [pcaob-as1105]

## Data lineage checklist
Record original source, obtaining party, receipt date, format changes, transformation code, filters, manual edits, excluded records, and reconciliation to an independently understood population. Preserve identifiers and version hashes where practical. Ask whether the same system generated both the dataset and the number used to “reconcile” it.

## Original scenario
An auditor receives a CSV of billed transactions and runs an anomaly scan that produces zero flags. Before treating that result as useful, investigate whether unbilled transactions are relevant to the objective, whether the export is complete, and whether the chosen anomaly rules address the assertion. A zero-flag output is a procedure result under assumptions, not evidence of an error-free population.

## Procedure design
Document the objective, assertion, population, selection or analysis logic, expected exceptions, follow-up process, and conclusion supported by the work. Keep work performed separate from proposed work. A tool may help create an evidence request or identify questions; it must not claim that an auditor performed a procedure that has not occurred.

## Agent output
Return a lineage diagram in structured text, an evidence-quality matrix, proposed procedures, exceptions requiring attention, and unresolved reliability questions. Preserve the original data and actual workpaper evidence in the authorized private workspace, never in a public contribution or training dataset.

## Sources and verification

- [AS 1105 — Audit Evidence](https://pcaobus.org/oversight/standards/auditing-standards/details/AS1105) — auditing standard; Selected evidence quality and company-provided information provisions; version applicability must be checked.
- [Technology-assisted analysis amendments](https://pcaobus.org/oversight/standards/standard-setting-research-projects/amendments-related-to-certain-aspects-of-designing-and-performing-audit-procedures-that-involve-technology-assisted-data-analysis) — standard setter summary; Describes amendments effective for fiscal years beginning on/after December 15, 2025.
- [Policy statement concerning AS 1105 .10A](https://pcaobus.org/news-events/news-releases/news-release-detail/pcaob-posts-board-policy-statement-on-evaluating-the-reliability-of-external-electronic-information-provided-by-the-company) — standard setter summary; September 18, 2025 release identifies source/process understanding and information-or-control testing.


---
Original content: Open Accounting contributors · CC BY 4.0 · Draft 2026-09-27. Third-party sources retain their own rights.
