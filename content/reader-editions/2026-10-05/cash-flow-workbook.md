# Cash flows: reconcile the bank population before classifying it

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

**Educational draft · v1.1.0 · 2026-10-04 · Editorial checks only; no human professional review.**

This original fictional packet separates imported rows, bank movements, internal transfers, noncash information and accounting classification. Its arithmetic is reproducible. Its bank population, source records and amounts are stipulated for education. They are not actual client evidence or an approved cash-flow statement.

## Scope and authority map

Candidate research starting point: **ASC 230**, together with the guidance relevant to each underlying transaction. Current Codification text was not obtained or independently reviewed for this revision. The platform has not reproduced that text or approved this article as Agent evidence. A reference link does not establish the applicable paragraph, reporting-period version, exceptions or permission to reuse source text.

The illustration uses one fictional entity, two USD bank accounts and an illustrative September. The reporting year, applicable reporting requirements and reporting entity's accounting policies are unspecified. Accounts A and B form the **stipulated bank working population** for the calculations below. That choice does not establish which balances qualify as cash, cash equivalents or restricted cash for financial reporting, or whether the population represents the correct consolidation scope. Resolve those questions before repurposing the worksheet as a statement of cash flows.

The example supplies no foreign-currency, acquisition-scope-change, restricted-cash or cash-equivalent facts. A real intake still needs beginning and ending bank reconciliations, the cash general ledger, restricted-balance schedules, debt/lease and acquisition rollforwards, and foreign-currency movements where relevant. Record absent populations as missing evidence; do not assume their amounts are zero because they are outside this packet.

## Original packet and row identities

The opening bank balances are A USD 125,000 and B USD 75,000, totaling USD 200,000. The supplied closing balances for September 30 are A USD 260,000 and B USD 130,000, totaling USD 390,000. These are fixture facts; no actual bank confirmation or review occurred.

The raw import contains ten rows. A positive amount is a receipt into the named bank account; a negative amount is a payment from it. The date column is the stipulated bank movement date, not the import time or a legal recognition date. Descriptions reproduce the fictional preparer's labels and do not determine accounting classification.

| Import row | Bank | September day | Packet event | Description | USD movement |
|---|---|---:|---|---|---:|
| R01 | A | 5 | E01 | Customer Cedar receipt | +120,000 |
| R02 | A | 6 | E02 | Supplier payment | -45,000 |
| R03 | A | 10 | E03 | Payroll payment | -30,000 |
| R04 | A | 12 | T04 | Transfer to included Bank B | -25,000 |
| R05 | B | 12 | T04 | Transfer from included Bank A | +25,000 |
| R06 | B | 18 | E05 | Described as financing receipt | +80,000 |
| R07 | B | 20 | E06 | Described as equipment payment | -50,000 |
| R08 | A | 24 | E07 | Customer refund | -5,000 |
| R09 | A | 28 | E08 | Customer Flint receipt | +120,000 |
| R10 | A | 5 | E01 | Demonstrated import copy of R01 | +120,000 |

The packet expressly identifies R10 as a second import of the **same original bank record** as R01, with the same bank account, original statement-row reference, movement date, currency, bank reference and source-record bytes. It was imported on October 1. That later import date does not create another September receipt. This is a declared property of the fictional packet, not a general rule that matching amounts or similar descriptions prove duplication.

R09 is a different receipt with a different customer, bank reference, source row and date. Its amount equals R01's amount, but both movements remain in the bank population. R04 and R05 intentionally share transfer-event identifier T04: they are separate bank legs needed to reconcile two included accounts. A transaction identifier and a bank-row identifier serve different purposes.

## Reproduce the reconciliation

Retain the raw import, the proposed removal and its supporting identity evidence. Do not silently rewrite the original file. For this fixture only, remove the demonstrated R10 copy from the working population; retain the other nine bank legs.

| Population | Gross receipts USD | Gross payments USD | Net movement USD | Opening plus net USD |
|---|---:|---:|---:|---:|
| Ten raw imported rows, including the copy | 465,000 | 155,000 | 310,000 | 510,000 |
| Nine bank legs after removing only R10 | 345,000 | 155,000 | 190,000 | 390,000 |
| Seven external events after removing both matched transfer legs from this presentation | 320,000 | 130,000 | 190,000 | 390,000 |

The raw import implies USD 510,000, exceeding the supplied USD 390,000 closing balance by USD 120,000. The demonstrated copy explains that difference within this stipulated packet. After removing it, receipts of USD 345,000 less payments of USD 155,000 give USD 190,000 net movement.

The separate account bridges are:

- A: 125,000 + 120,000 - 45,000 - 30,000 - 25,000 - 5,000 + 120,000 = **260,000**
- B: 75,000 + 25,000 + 80,000 - 50,000 = **130,000**
- Combined: 200,000 + 190,000 = **390,000**

Both transfer legs remain in their respective account bridges. For the separate external-movement presentation, remove the USD 25,000 receipt and USD 25,000 payment together. External receipts are 120,000 + 80,000 + 120,000 = **320,000**. External payments are 45,000 + 30,000 + 50,000 + 5,000 = **130,000**. The internal transfer elimination changes gross movement totals by USD 25,000 on each side and leaves the USD 190,000 net unchanged.

This result depends on both bank accounts actually being included in the stipulated working population and the two legs being the same transfer. A payment to an account outside that population cannot simply be removed under this fixture's explanation. Do not create an unexplained balancing line when a transfer leg, account or currency is missing.

## Counterexamples that a balanced total can conceal

**Deduplicating equal amounts removes real events.** If R09 is discarded after R10 has been removed, the worksheet loses a separate USD 120,000 receipt. It predicts closing bank balances of USD 270,000 rather than USD 390,000. The first two customer receipts cannot be merged solely because their amounts match.

**Collapsing a shared transfer ID loses a bank leg.** If a one-row-per-event routine retains R04 and drops R05, the combined worksheet predicts USD 365,000. If it retains R05 and drops R04, it predicts USD 415,000. Neither is a valid substitute for preserving both bank legs and, where appropriate for a separate presentation, eliminating them as a matched pair. A shared event ID is not a duplicate-row verdict.

**A net tie-out does not validate gross presentation.** Both the nine-leg working file and seven-event external presentation reconcile to USD 390,000. Calling USD 345,000 and USD 155,000 external receipts and payments would still include the internal transfer in each gross total. A net-only check would not identify that presentation error.

**A bank tie-out does not assign operating, investing or financing categories.** The packet's words “financing” and “equipment” are descriptions to investigate. The worksheet has not established applicable accounting requirements or how multi-component settlements, fees, refunds and unusual transactions should be classified. Do not label the whole USD 190,000 net movement “operating cash flow” because the bank balances reconcile.

## Keep noncash information out of the bank-movement arithmetic

A separate fictional acquisition packet proposes two nonoverlapping components: the USD 50,000 Bank B payment already recorded in R07 and USD 60,000 financed without a bank movement in this working population. If those assumptions are complete and accurate, their arithmetic bridge is **50,000 + 60,000 = 110,000**.

That USD 110,000 is a proposed acquisition bridge, not another bank payment, an approved capitalized asset amount or a valuation. The USD 60,000 has no bank leg by the fixture's explicit assumption. Adding it to bank payments would overstate the working population's external payments from USD 130,000 to USD 190,000, reduce its net movement to USD 130,000 and imply closing balances of USD 330,000. Counting the existing R07 payment a second time would create a separate duplicate-counting error.

Obtain the actual arrangement, invoice, settlement documents and relevant primary requirements before deciding capitalization, measurement, liabilities, statement classification or disclosures. A balance-sheet asset increase alone does not establish the amount paid through the bank accounts. The exercise neither concludes that a particular disclosure is required nor treats noncash information as irrelevant to the broader reporting analysis.

For unusual settlements, identify payer and recipient, economic purpose, legal arrangement and potentially separate components. Research fees, interest, taxes, acquisitions, supplier finance, leases and securities against the applicable current primary requirements. If preparing an indirect-method analysis, distinguish reconciliation adjustments from actual bank movements; do not infer every cash classification from a comparative trial-balance change. These are research workstreams, not resolved rules or categories.

## Proposed evidence and classification worksheet

These are **proposed work items**. No named reviewer, independent confirmation, completed task or accounting approval is implied by a populated row. Record the eventual exact record/revision, preparer, review date, period and decision separately.

| Work item | Packet fact or open question | Evidence to obtain or reconcile | Current disposition |
|---|---|---|---|
| Population and period | A/B are stipulated; reporting year and accounting cash definition are unresolved | Entity/scope register, reporting requirements, cash-account policy, restricted balances and period evidence | Unresolved for reporting use |
| Opening and closing balances | A 125,000→260,000; B 75,000→130,000 | Full original bank records and reconciliations, including outstanding items | Fixture arithmetic only |
| Import copy R10 | Packet declares the same source record as R01 | Original source-row identity, bank reference and retained bytes; import lineage | Proposed removal of this copy only |
| Equal receipts R01/R09 | Different customers, references, rows and dates | Separate receipts and supporting records; completeness checks | Retain both in this fixture |
| Transfer T04 | Two included-bank legs net to zero | Both bank records, common transfer evidence, account ownership/scope and currency | Preserve two legs; paired presentation adjustment only |
| Transaction classifications | Seven external events remain unclassified | Underlying arrangements, components, settlement terms and applicable current primary passages | No category conclusion |
| Acquisition bridge | 50,000 bank payment plus stipulated 60,000 without a bank movement | Vendor/financing documents, ledger rollforward, overlap/completeness and measurement evidence | Conditional arithmetic only |
| Cutoff and contradictions | A proposed later bank item or conflicting ledger date is outside the supplied packet | Original movement date, ledger posting date, bank timing and reconciliation evidence | Investigate; do not insert a balancing amount |

Preserve contradictions and missing records. A later import date, a ledger posting date and a bank movement date describe different events. The worksheet supplies no universal cutoff conclusion for an additional item. Reconcile an actual exception using the applicable period and evidence before changing the population.

## Five original practice questions

1. Why does the raw import predict USD 510,000? Identify the duplicated evidence and explain why the USD 120,000 difference alone would not prove which row to remove in a real file

2. Why must R09 remain even though its amount equals R01? List the distinct identity evidence and reproduce the incorrect USD 270,000 result if it is dropped

3. Why are there nine legitimate bank legs but seven external events? Reconcile both accounts and show how the paired USD 25,000 presentation adjustment leaves the net unchanged

4. How can two presentations both reach USD 390,000 while one overstates gross external movements? Explain which checks a net-only reconciliation misses

5. Why does the proposed USD 110,000 acquisition bridge not justify a USD 110,000 bank outflow? Reproduce the USD 330,000 incorrect closing result and identify the accounting and source questions still unanswered

These questions have not been professionally adjudicated. These embedded questions are new educational prompts within this article. They do not add adjudicated answers to the separate question bank or establish a professional benchmark.

## Deliverable and review gate

Prepare a retained raw import, explicit row-identity decisions, two account bridges, the separate external-movement presentation, a noncash-information register, unresolved classification questions and the proposed evidence worksheet. A reviewer should be able to reproduce every number and inspect each proposed adjustment without relying on account names as accounting conclusions.

Use **supported**, **conditional** or **unresolved** for the particular claim and state its basis. Here, arithmetic is supported only by the stipulated fictional inputs; reporting applicability, population completeness and classifications remain unresolved. Do not convert successful arithmetic tests into source verification, human review or Agent eligibility. Any real approval must identify the exact article or workpaper revision, actual reviewer, date and scope.

## Completed editorial checks and a retained limit

The raw/unique/external counts, each account bridge, all counterexamples and the five question prompts were checked for this exact revision. The matched internal transfer changes gross receipts and payments while leaving the net unchanged; the demonstrated copy changes the net. Those are different operations on different identities. The verified arithmetic does not resolve the reporting population or transaction classification.

## Sources and verification

- [FASB Codification home](https://asc.fasb.org/): research entry point only; current primary text and applicable amendments were not accessed. Publisher-use restrictions identified October 4, 2026 remain unresolved; no further retrieval or ASU/ASC body acquisition followed that finding

Source access, permitted operations and current reporting-period applicability require separate authorized review. Original arithmetic and editorial checks do not close those gaps.

Original educational content by Open Accounting contributors. Licensed under **CC BY 4.0**. The original records, examples, questions and worksheet remain freely readable. No third-party standard text is reproduced or relicensed; no professional approval, publisher-use permission, Agent admission, posting or assurance conclusion is granted.
