# Electronic audit evidence: trace the data before trusting the analysis

> **AI-assisted editorial draft — not professionally reviewed.** Original educational content, not authoritative guidance. Confirm the framework, reporting period, elections, and source versions before use. All company names and transactions in examples are fictional.

## Authority boundary before using electronic information

The existing reference catalog points to PCAOB AS 1105, technology-assisted analysis amendments and an external-electronic-information policy statement. Their source bodies were not fetched or reverified for this revision because the current project rights review identified publisher restrictions on automated gathering/extraction. This article therefore does not reaffirm their substantive requirements or effective dates. Obtain an authorized applicable edition and qualified engagement review before relying on them. A source link is not permission to process the source with AI.

The exercises below teach original data reasoning. They make no claim to replace PCAOB, AICPA, GAO or international standards. Define the question first: an accurate calculation of the wrong population does not answer it, and additional rows from an unvalidated export do not prove completeness. Those are logical limits of the calculation, not claims that this lesson has verified an auditing requirement.

## Data lineage checklist
Record original source, obtaining party, receipt date, format changes, transformation code, filters, manual edits, excluded records, and reconciliation to an independently understood population. Preserve identifiers and version hashes where practical. Ask whether the same system generated both the dataset and the number used to “reconcile” it.

## Original scenario
An auditor receives a CSV of billed transactions and runs an anomaly scan that produces zero flags. Before treating that result as useful, investigate whether unbilled transactions are relevant to the objective, whether the export is complete, and whether the chosen anomaly rules address the assertion. A zero-flag output is a procedure result under assumptions, not evidence of an error-free population.

## Procedure design
Document the objective, assertion, population, selection or analysis logic, expected exceptions, follow-up process, and conclusion supported by the work. Keep work performed separate from proposed work. A tool may help create an evidence request or identify questions; it must not claim that an auditor performed a procedure that has not occurred.

## Agent output
Return a lineage diagram in structured text, an evidence-quality matrix, proposed procedures, exceptions requiring attention, and unresolved reliability questions. Preserve the original data and actual workpaper evidence in the authorized private workspace, never in a public contribution or training dataset.

## Worked case: both the count and total agree, but the records do not

Assume one row per unique billed transaction, one entity, USD, a common cutoff, and no valid splits, reversals or timing differences. The independent source register and the export are stipulated fictional inputs; a real engagement must evaluate each source's reliability and completeness.

| Source register | Amount | Export row | Amount |
|---|---:|---|---:|
| T1 | 100 | T1 | 100 |
| T2 | 200 | T2 | 200 |
| T3 | 300 | T2, duplicated | 200 |
| T4 | 400 | T5, unexpected | 500 |
| Total, four rows | 1,000 | Total, four rows | 1,000 |

The export has the same row count and dollar total. It nevertheless omits T3 and T4, duplicates T2, and introduces T5. Missing amounts total **300 + 400 = 700**; the duplicate and unexpected amounts total **200 + 500 = 700**. Net difference is zero. Equal totals do not identify which records exist, and equal counts do not establish uniqueness.

A rule that flags individual rows greater than 500 returns zero flags. That outcome says only that no tested row exceeded that chosen threshold. It does not test missing T3/T4, duplicated T2, or whether T5 belongs in the population. Selecting a threshold without connecting it to the objective can make a perfectly executed scan uninformative.

### A reproducible comparison plan

Preserve the original files and record their hashes. Define the comparison key, amount field, units, timezone, cutoff, treatment of duplicate keys and expected one-to-one or one-to-many relationships. Then compare keys and values in both directions, retaining unmatched rows rather than dropping them through an inner join. Verify that transformations preserve the expected population; do not fix source rows merely to make a comparison pass.

For this supplied dataset, the unique common keys are T1 and T2. The source-only keys are T3 and T4; the export-only key is T5; T2 appears twice in the export. A useful report preserves all four findings separately. It does not treat the 700 gross omission as the financial-statement error without further recognition, occurrence, cutoff and materiality work.

If real billing legitimately splits T4 across two lines, the single-row assumption is false. Define a stable transaction-to-line relationship and compare the total and attributes of each transaction. Do not delete the second line simply because its parent key repeats. The right duplicate rule depends on the entity's data model and the objective.

## A second case: enrichment doubles the evidence

Assume a source has two invoices for vendor V: 100 and 200. A vendor-reference file accidentally contains two rows for V. A naive one-to-many join repeats each invoice and produces four rows totaling **600**, although the invoice source totals **300**. Summing the joined output without a pre/post-join reconciliation overstates the source amount by **300**.

A transformation log should record expected cardinality, duplicate-key checks and unmatched records. If two vendor rows represent different valid historical versions, choose the applicable version using supported dates and keys; arbitrary deduplication may assign the wrong attributes even if the total returns to 300. Preserve the selection rationale, code version and rejected alternatives.

## Evidence request to conclusion: a compact workpaper

| Stage | Record | What it does not establish |
|---|---|---|
| Question | Assertion/objective and why this population addresses it | A data export is not automatically relevant |
| Acquisition | Owner, method, exact file/version, cutoff and access scope | Receipt of a file does not prove authenticity or completeness |
| Transformation | Script/version, filters, joins, manual changes and pre/post checks | A successful run does not prove the transformation is appropriate |
| Analysis | Exact rules, inputs, exceptions and reproducible output | Zero flags do not mean zero misstatement |
| Follow-up | Evidence actually inspected, executor, date and documented result | A planned investigation is not work performed |
| Conclusion | Supported scope, contradictory facts, missing evidence and real reviewer decision | A model answer is not independent professional approval |

Do not execute macros, activate live links, change access permissions or contact a third party merely to inspect the evidence. Use authorized private locations for real files. Keep confidential records out of this public lesson and do not treat an upload or subscription as permission for broader use.

## Study checks

1. Why do matching count and amount fail in the first case? Different missing, duplicated and unexpected identities offset both totals.
2. Does a zero result from the greater-than-500 rule establish complete billing? No; the rule did not address the identified omissions or duplicates.
3. What makes the join case misleading? One source invoice matches two reference rows, expanding both the row count and amount.
4. Can a corrected export be called reviewed because the earlier export was reviewed? Only an actual review covering the changed exact revision supports that statement.

## Sources and verification

- [AS 1105 reference](https://pcaobus.org/oversight/standards/auditing-standards/details/AS1105) [pcaob-as1105]: link-only; no current body or paragraph verification in this review.
- [Technology-assisted analysis reference](https://pcaobus.org/oversight/standards/standard-setting-research-projects/amendments-related-to-certain-aspects-of-designing-and-performing-audit-procedures-that-involve-technology-assisted-data-analysis) [pcaob-tech-amendments]: historical catalog pointer; dates and requirements not freshly verified.
- [External electronic information policy reference](https://pcaobus.org/news-events/news-releases/news-release-detail/pcaob-posts-board-policy-statement-on-evaluating-the-reliability-of-external-electronic-information-provided-by-the-company) [pcaob-electronic-policy]: historical catalog pointer; body not acquired.

AI editorial checking on October 4, 2026 covered the original reasoning, fictional arithmetic and honest source limits. It did not perform the described procedures for a real audit. The unresolved authoritative-text/rights gap remains visible; no automated alternative acquisition was attempted.

## Free lesson and private workflow boundary

This original educational article remains free under CC BY 4.0. Premium can license private software workflow execution where available and authorized; it does not convert a public document into proprietary standards, grant source-processing rights, or supply professional approval. No real procedure, source grant, posting, model execution or review signature is created by these examples.

---
Original content: Open Accounting contributors (AI-assisted) · CC BY 4.0 · Version 1.0.0 · 2026-10-04. The license applies to the original lesson, not linked publications.
