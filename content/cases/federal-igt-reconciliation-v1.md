# Federal interentity reconciliation: explain differences before proposing corrections

> **AI-assisted editorial draft — not professionally reviewed.** Version 1.0.0, 2026-09-29. All entities, balances, documents and follow-up results below are fictional. Proposed procedures have not been performed for a real entity. This free educational case is not a recognition policy, filing instruction, audit opinion or approved Agent evidence.

This workbook practices reconciliation evidence and review, within the library's Auditing category. Its setting is U.S. federal reporting, not state/local GASB reporting or corporate U.S. GAAP. It does not select a USSGL account, reciprocal category or federal reporting attribute for a real transaction.

## Sources and verification

Two retained Treasury Financial Manual Volume I, Part 2, Chapter 4700 appendices provide context:

- [Appendix 5, June 2026, physical/printed page 5, Section 2, IGT Reporting Guidance](https://tfx.treasury.gov/media/26/download?inline) [treasury-tfm4700-app5-jun2026]. It calls for partner reconciliation before GTAS adjusted trial balance submission, supporting transaction records, and purpose-specific use of limited-use accounts. It points to Appendix 3 for account pairings.
- [Appendix 6, June 2026, physical/printed page 7, Limited Use of USSGL Accounts, Table 4](https://tfx.treasury.gov/media/1791/download?inline) [treasury-tfm4700-app6-jun2026]. Its investment-specific example restricts account 254000 to particular circumstances; it does not make that account a general balancing tool.

Those selected pages were compared with rendered originals by an AI-assisted process. Full originals were retained separately; this library does not redistribute their text. Source hashes and retrieval timestamps are in the reference records. June 2026 is the observed edition label; exact issuance, first public availability and effective dates remain unknown. An HTTP Last-Modified header is not an effective date. Neither a source download nor this comparison is independent technical, rights or applicability approval. Other source provisions, current USSGL guidance, reporting instructions and amendments must be checked before real use.

The calculations, fictional facts, template and suggested investigation below are original educational material. They are not Treasury examples or Treasury-approved procedures.

## Case 1 — A small net difference conceals separate exceptions

**Assumptions.** Entity Alder has three fictional federal partners, Birch, Cedar and Dune. Freeze both sides' September 30, 2026 extracts for one identified receivable/payable comparison. All values below are USD, not thousands. Express Alder's receivable and each partner's reciprocal payable as positive comparison magnitudes. This display convention is not a debit/credit posting rule. The extracts use the same cutoff and scope for this exercise; in practice, establish that before comparing.

| Partner | Alder receivable | Partner payable | Difference: Alder minus partner |
|---|---:|---:|---:|
| Birch | 125,000 | 113,000 | 12,000 |
| Cedar | 80,000 | 88,000 | (8,000) |
| Dune | 45,000 | 42,000 | 3,000 |
| Total | 250,000 | 243,000 | 7,000 |

Net difference = 12,000 − 8,000 + 3,000 = **7,000**. Gross absolute partner differences = 12,000 + 8,000 + 3,000 = **23,000**. Gross here measures exceptions at this chosen partner aggregation, not transaction-level errors or an audit materiality measure. It could conceal further offsets within each partner.

A reviewer who investigates only the 7,000 net cannot conclude that the Cedar exception has been resolved. Nor does the 23,000 total prove that either side needs that amount of adjustment. Obtain complete bilateral populations and relevant support, then decide which records, if any, are wrong. No automatic netting across different partners is proposed.

**Evidence to request:** exact extract revisions and hashes; entity and partner identities; reporting date; units and sign mapping; balances tied to the relevant ledger; agreement and document IDs; service/delivery and acceptance dates; invoices, settlements and reversals; preparer explanations supported by records. Preserve amounts before and after normalization. A missing partner response remains missing evidence, not a zero balance.

## Case 2 — Build an explanation bridge without pretending to post it

For this exercise only, suppose subsequent investigation establishes these additional fictional facts:

| Exception | Fictional evidence found | Proposed consequence, subject to review |
|---|---|---|
| Birch 12,000 | Acceptance record and agreement support September service; Birch omitted the supported accrual from its extract | Birch evaluates a 12,000 payable increase; Alder does not book an equal-and-opposite plug |
| Cedar (8,000) | Cedar's 88,000 includes one demonstrably duplicated 8,000 document; distinct transactions are not being mistaken for duplicates | Cedar evaluates removal of the duplicate, reducing its comparison balance by 8,000 |
| Dune 3,000 | No invoice, acceptance or subsequent settlement explains the mismatch | Keep 3,000 unresolved, with an owner and evidence request |

The proposed partner-side bridge is **243,000 + 12,000 − 8,000 = 247,000**. Against unchanged Alder receivables of 250,000, the remaining proposed difference is **3,000**. Explained gross exceptions are 20,000 of the initial 23,000, or **86.96%** rounded to two decimals. This is a teaching progress metric, not an official threshold, audit assurance or permission to submit.

Even under those fictional facts, the original recorded difference stays **7,000** until authorized changes are actually recorded and new extracts checked. Maintain separate columns for recorded, explained, approved and posted amounts. A preparer's explanation does not update the ledger. Reperform the comparison after posting; retain both snapshots and tie changes to the approved exact revisions.

**Counterexamples.** If Birch's services were delivered after cutoff, the omission story may be wrong. If Cedar's two documents represent different deliveries with the same amount, removing one could create an error. If Dune supplies an extract in thousands, correct the comparison units before treating the difference as accounting error. None of these alternatives can be settled by matching totals alone. Assess recognition and period treatment with applicable authority and authorized reviewers.

## Case 3 — Totals agree while partner assignment is wrong

A separate fictional extract shows Alder receivables of 40,000 from Birch and 10,000 from Cedar. Partner records show payables to Alder of 35,000 and 15,000 respectively. Both totals are **50,000**, but the differences are **5,000** and **(5,000)**: net zero, gross **10,000**.

A 5,000 document may have been assigned to the wrong partner, but that is a hypothesis. Compare agreement parties, transaction identifiers and supporting records before proposing a reclassification. Do not use this example to swap actual Treasury identifiers or select a reciprocal category. Equal aggregate balances are insufficient evidence of correct counterparties, reporting attributes or complete elimination.

Likewise, a text parser returning all account numbers from a two-column source table does not establish their correct pairings. Verify the actual table's rows, headers and notes. Do not pair numbers by extracted token order. If the pairing is unresolved, preserve the original table locator and keep the mapping unapproved.

## Case 4 — A restricted account cannot cure an unexplained difference

A preparer proposes using account 254000 to clear Dune's unresolved 3,000 because it appeared in an investment table. This case supplies no investment transaction facts establishing its permitted use. The cited Appendix 6 limitation is a reason to investigate applicability, not authorization to post. Reject the shortcut in this exercise and retain the unresolved difference.

Obtain transaction purpose, relevant account definition and attributes, applicable reporting edition, and any necessary authorized determination. Prepare a question for the responsible accounting owner; no message or permission request has been sent. A subscription, general system access or a model's suggested account does not grant posting authority or source-operation rights.

## Reusable reconciliation and review template

Create one record per partner/category/period comparison, retaining transaction-level detail separately:

| Field | Required evidence or explicit unresolved state |
|---|---|
| Scope | Entities; partner identifiers and their provenance; comparison category; period/cutoff; currency, units and sign conventions |
| Snapshots | Both original extract IDs/hashes, retrieval times, ledger ties, completeness checks and access restrictions |
| Difference | Each side's recorded balance; signed difference; gross exceptions at a stated aggregation; missing populations |
| Investigation | Document IDs and exact locators; observed facts; assumptions; alternative explanations; evidence requested |
| Proposed change | Which entity/record changes, amount and rationale; applicable authority and unresolved account/attribute questions |
| Review | Actual authorized reviewer, exact reviewed revision/hash, scope, date and decision; leave blank until performed |
| Implementation | Approval and posting references, or “not posted”; subsequent extract hashes and recalculated residual |
| Open items | Owner, target follow-up date, precise blocker, escalation route and closure evidence |

Do not insert real client documents, credentials or private correspondence into the public example. Rights to view source material, process it with AI, retain derivatives and export it must be assessed separately. Retain applicable notices and access limits.

## Evaluation prompts and limits

1. Can a reviewer reproduce both the 7,000 net and 23,000 gross exceptions from the first table? Expected: yes; neither establishes the required journal amount.
2. After explaining Birch and Cedar, has the recorded difference become 3,000? Expected: no; 3,000 is the proposed bridge residual until posting and re-extraction are evidenced.
3. Does the zero net difference in Case 3 demonstrate correct partner reporting? Expected: no; two 5,000 partner exceptions remain.
4. Can two repeated amounts establish a duplicate? Expected: no; transaction identity and supporting facts are required.
5. Does the downloaded investment table authorize using 254000 for Dune? Expected: no; transaction applicability and authorized review are missing.

These are draft study expectations, not professionally adjudicated benchmark answers. Arithmetic checks cover the numerical examples only. Real source rights, complete source/layout validation, entity-specific accounting analysis, independent professional review, posting approval and historical applicability remain outstanding. License for this original case: CC BY 4.0; that license does not relicense cited third-party works.
