# Inventory: reconcile each item before trusting the total

**AI-assisted educational draft · v1.1.0 · 2026-10-04 · AI editorial checks only; no human professional review.**

A grand-total tie can hide different errors in different items. This original workbook connects a fictional quantity rollforward to count records and stipulated cost extensions. It teaches how to preserve exceptions and the evidence still needed; it does not determine ownership, select an inventory-cost method, measure a real write-down or authorize a journal.

## Scope and research decisions

The fictional entity is EXAMPLE-STOCK, the reporting date is September 30, 2026, and monetary illustrations are in USD. A and B are distinct products, each counted in individual units. They are not interchangeable: adding their counts produces an arithmetic control, not a fungible inventory quantity or a measure of value. Every quantity, price, record ID, date and ownership classification below is invented.

For the exercise only, assume that the listed movements use the same unit and cutoff, that there are no omitted production/disposal movements within the base case, and that the four count records describe distinct quantities. Ownership and count reliability are stipulated for calculation, not established by actual contracts, observation or confirmation. The exercise's word “owned” is a supplied classification, not a legal or accounting conclusion.

ASC 330 remains a candidate research starting point. Current Codification text, method-specific measurement, industry guidance, reporting-date applicability and exceptions have not been verified for this workbook. The broader topic map identifies other accounting and auditing families, but this article's actual reference is still FASB only. It supplies no IFRS comparison or audit requirement. Verify applicable primary authority and permitted source operations separately before relying on a rule.

## 1. Preserve the recorded quantity rollforward

The original book extract reports the following quantities. These are supplied records, not verified balances.

| SKU | Opening units | Recorded receipts | Recorded shipments | Recorded ending units |
|---|---:|---:|---:|---:|
| A | 120 | 40 | 60 | 100 |
| B | 40 | 20 | 10 | 50 |
| Arithmetic sum only | 160 | 60 | 70 | 150 |

For A, 120 + 40 − 60 = 100. For B, 40 + 20 − 10 = 50. Keep the original extract, unit dictionary, location scope and movement identifiers. A mathematical rollforward tie does not establish whether movements belong to this entity or period, whether the extract is complete, or whether the underlying counts are reliable.

Do not add a balancing receipt or disposal merely to match a target closing number. Each proposed change needs its own source, rationale and unresolved status.

## 2. Separate the count records from the ownership assumptions

These four records are a fictional exercise packet. “Included” means included in this stipulated candidate population; it does not mean approved for an actual financial statement.

| Record | SKU | Location | Stated physical units | Stipulated ownership class | Candidate included units |
|---|---|---|---:|---|---:|
| C-01 | A | Entity site | 75 | Entity-owned for this exercise | 75 |
| C-02 | A | Third-party warehouse | 15 | Entity-owned for this exercise | 15 |
| C-03 | A | Entity site | 20 | Supplier-owned for this exercise | 0 |
| C-04 | B | Entity site | 60 | Entity-owned for this exercise | 60 |

The four records describe 170 physical units: 75 + 15 + 20 + 60. The candidate population includes 150 after separately excluding the stipulated 20 supplier-owned units. The 15 at the third-party warehouse are included under the exercise assumption; physical location alone neither establishes nor defeats ownership.

| SKU | Recorded ending units | Candidate included units | Candidate minus recorded |
|---|---:|---:|---:|
| A | 100 | 90 | -10 |
| B | 50 | 60 | 10 |
| Arithmetic sum only | 150 | 150 | 0 |

A's candidate quantity is 75 + 15 = 90. B's is 60. The grand totals both equal 150, while A has a ten-unit shortage relative to the recorded quantity and B a ten-unit excess. Neither difference is resolved by adding unlike SKUs. Retain both exceptions, their locations and the missing evidence instead of reporting “inventory reconciled.”

If third-party support for C-02 is unavailable in a real engagement, the answer is unresolved, not zero. Substituting zero would give A 75 and a -25 difference, but missing evidence does not prove that the 15 units do not exist or belong elsewhere. The 90-unit candidate remains conditional until the relevant facts are supported.

## 3. Apply stipulated unit costs without selecting an accounting method

For arithmetic only, use USD 10 per A unit and USD 30 per B unit for both the recorded and candidate quantities. These prices are invented inputs, not evidence of an accepted cost layer, cost formula, overhead allocation, recoverable amount or selling price. Applying the same stipulated unit cost isolates the quantity differences; it does not validate the real unit costs.

| SKU | Stipulated USD per unit | Recorded extension USD | Candidate extension USD | Candidate minus recorded USD | Absolute difference USD |
|---|---:|---:|---:|---:|---:|
| A | 10 | 1000 | 900 | -100 | 100 |
| B | 30 | 1500 | 1800 | 300 | 300 |
| Monetary arithmetic total | not one blended cost | 2500 | 2700 | 200 | 400 |

The recorded extensions are 100 × 10 + 50 × 30 = 2500. Candidate extensions are 90 × 10 + 60 × 30 = 2700. The net difference is +200, while the sum of absolute item differences is 100 + 300 = 400. Neither number is a proposed correcting entry, materiality conclusion or accepted inventory balance.

A cost error could offset a quantity error in dollars just as the item quantities offset in the first table. Reconcile item identities and quantities before interpreting extended values. The +200 net also does not prove that the smaller negative difference can be ignored or that gains and losses may be offset under an applicable measurement model.

If the supplier-owned C-03 were incorrectly included using the exercise's A price, A's candidate would become 110 and its extension 1100; the combined candidate extension would become 2900. That extra 200 is caused by the wrong population under the stated assumptions, not by an independently supported asset.

## 4. A conditional cutoff branch must change both sides consistently

Keep the base case above unchanged. Now introduce a separate hypothetical branch: a previously omitted ten-unit incoming A movement is identified. Its transport date alone does not settle recognition, ownership or cutoff. For this branch's arithmetic only, stipulate that an independently supported cutoff decision would require those same ten units in both the expected receipt rollforward and the candidate quantity population. That condition is invented; the required decision and evidence are not supplied here.

Under that stipulated branch, expected A receipts would be 50, so the cutoff-consistent expectation would be 120 + 50 − 60 = 110. The candidate quantity would be 75 + 15 + 10 = 100. The difference would still be -10.

Adding the ten units only to the candidate would make it equal the original recorded 100 and falsely appear to solve the base shortage. The conditional rollforward shows why that shortcut is misleading. The original recorded extract still says 100; the 110 expectation is a separately labelled proposed branch, not an overwritten book record or an approved adjustment.

If the condition is not established, preserve the ten-unit question as unresolved and retain the base-case calculations. Do not select the branch that makes a reconciliation look clean.

## 5. Populated evidence worksheet and stop conditions

The following IDs refer only to the fictional rows and questions in this article. They are not real evidence links, hashes, completed procedures or reviewer approvals. Replace them with actual permitted evidence and exact locators in a real workpaper; leave missing information explicit.

| Worksheet row | Record or calculation | Supplied exercise fact | Evidence or decision still needed | Current disposition |
|---|---|---|---|---|
| W-01 | A movement rollforward | 120 + 40 − 60 = 100 | Original movement extract/hash, unit definition, transaction identity and cutoff support | Arithmetic supported by stipulated inputs; completeness unresolved |
| W-02 | C-01 and C-03 at entity site | 75 entity-owned and 20 supplier-owned A units | Count time, physical condition, custody arrangement and actual ownership/recognition analysis | Ownership classes assumed for the exercise |
| W-03 | C-02 at third-party warehouse | 15 A units included conditionally | Exact location/lot/unit, warehouse record, entity relationship and relevant third-party support | Not verified by this workbook |
| W-04 | C-04 compared with B book quantity | 60 candidate versus 50 recorded B units | Count/recount records, receipt/shipment identities, duplicates, omissions and unit conversions | +10 exception remains open |
| W-05 | A and B cost extensions | Unit prices 10 and 30 USD | Supported cost layers/formula, component eligibility, allocation and ledger mapping | Conditional arithmetic; no selected method |
| W-06 | Optional ten-unit A branch | Both receipt expectation and candidate population increase by 10 | Applicable cutoff decision, source movement and relationship to the reporting date | Separate proposed branch, not a posting |
| W-07 | Recoverability and reporting | No selling-price or write-down estimate is supplied | Item condition, demand, completion/disposition costs, relevant subsequent information and applicable measurement/disclosure requirements | Unresolved; no reserve calculated |

Carry entity, SKU/lot, location, unit, count time, measurement cutoff, source ID/hash, exact locator, original quantity, candidate quantity, variance, stipulated cost, preparer and open action into the working schedule. For an actual review, record the real reviewer's identity, role, date, scope, evidence and exact revision/hash. A populated worksheet is not evidence that those procedures or that review occurred.

Stop or separate the analysis when:

- A row uses cartons while another uses individual units. A statement of 15 cartons of ten units would mean 150 units under that conversion assumption, not the exercise's 15. Verify the unit dictionary before combining records.
- Two rows have the same amount or quantity but different valid identities. Equality alone is not duplication. Conversely, an exact export duplicate must not be counted twice merely because it has a second file position.
- The ownership, count date, location or condition is disputed. Preserve the conflicting records and missing evidence rather than choosing the number closest to the ledger.
- A proposed quantity adjustment is also embedded in a changed unit cost. Separate the effects so the same issue is not corrected twice.
- An aging report or later sale is offered as a complete valuation conclusion. Investigate the applicable method, item economics and measurement-date relevance; this workbook supplies none of those decisions.
- A grand-total or monetary tie is treated as proof of existence, completeness, rights, costing or recoverability. Each remains a distinct question.

## 6. Embedded study questions

These five original questions received AI editorial checks as part of this revision, outside the unchanged 90-record question bank and any professionally adjudicated evaluation set. These questions have not been professionally adjudicated.

1. Why does the 150-to-150 quantity tie fail to resolve the case? **Answer:** A is -10 and B is +10. They are different products; the arithmetic sum hides both unresolved exceptions.
2. Why is C-03 excluded while C-02 is included? **Answer:** The exercise stipulates supplier ownership for C-03 and entity ownership for C-02. Physical custody alone is not the basis, and actual ownership/count support remains required.
3. Why are the monetary net and gross differences different? **Answer:** The stipulated item differences are -100 and +300. Their algebraic sum is +200; their absolute amounts total 400. Neither is an approved entry or materiality conclusion.
4. Does missing support for C-02 justify replacing 15 with zero? **Answer:** No. That would create A 75 and a -25 variance by assuming away an unresolved fact. Absence of evidence does not establish a zero quantity.
5. Does adding the ten-unit hypothetical incoming item resolve A's base shortage? **Answer:** Not under the stated branch. The candidate becomes 100 and the cutoff-consistent expectation 110, leaving -10; comparing only against the unchanged original book 100 hides the corresponding receipt question.

## Completed editorial checks and a retained limit

All quantity and cost tables, the net-versus-absolute differences, ownership counterexample, conditional cutoff branch and five answers were checked. The ten-unit cutoff branch changes both the expected receipt rollforward and the candidate quantity; adding it to only one side would hide the continuing shortage. No actual count, ownership, cost-layer or recoverability procedure was performed by this article.

## Sources and verification

- [FASB Codification home](https://asc.fasb.org/): research entry point only; current primary text and applicable amendments were not accessed. Publisher-use restrictions identified October 4, 2026 remain unresolved; no further retrieval or ASU/ASC body acquisition followed that finding

Source access, permitted operations and current reporting-period applicability require separate authorized review. Original arithmetic and AI editorial checks do not close those gaps.

Original educational content by Open Accounting contributors, AI-assisted. Licensed under **CC BY 4.0**. The original records, examples, questions and worksheet remain freely readable. No third-party standard text is reproduced or relicensed; no professional approval, publisher-use permission, Agent admission, posting or assurance conclusion is granted.
