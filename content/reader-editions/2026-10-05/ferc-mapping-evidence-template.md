# FERC ledger-to-report evidence worksheet

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

> **Editorial draft — not professionally reviewed.** Original research aid, not FERC instructions, an accounting determination or a completed regulatory return. All numerical inputs are fictional.

## Assignment and frozen inputs

| Field | Evidence or unresolved question |
|---|---|
| Entity/legal identifier; industry; jurisdiction basis | |
| Filing category and reporting period | Unverified until supported |
| Ledger export identifier, date and SHA-256 | |
| Currency, scale and debit/credit conventions | |
| Entity and transaction population; exclusions | |
| GAAP framework and separate regulatory basis | |
| Applicable rule/order/instruction edition and amendments | |
| Exact form edition and reporting deadline evidence | |

## Mapping register — repeat for each balance

Record mapping ID; source ledger account; opening balance; period movements; ending balance; gross/contra/net role; proposed regulatory account; exact instruction locator; proposed form/schedule/row/column or taxonomy concept; entity and period; rule/order authority class; artifact SHA-256; issued/available/effective/retrieved dates; amendment/rescission dependencies; unresolved assumptions; and evidence owner. Leave unverified destination fields blank rather than guessing them.

## Adjustment and scenario register

| ID | Amount/unit/sign | Facts and computation | Exact authority locator | Proposed/accepted/rejected | Reviewer/revision |
|---|---|---|---|---|---|
| | | | | Proposed; no approval | |

Keep accepted amounts separate from proposed scenarios. Show ledger + accepted adjustments = accepted bridge, and separately ledger + specified proposals = scenario. If there are no accepted adjustments, say so; do not relabel a proposed bridge as accepted. Retain rejected proposals and reasons in history.

## Reconciliation checks

| Check | Result and unresolved evidence |
|---|---|
| Input units, sign and population agree | |
| Beginning + movements = ending | |
| Gross less contra = net, where the stated convention applies | |
| Bridge against independently sourced target; residual convention | |
| Entity/account-level differences, net and gross absolute totals | |
| Duplicate, missing, intercompany and cutoff investigation | |
| Rounding differences and documented tolerance rationale | |
| Prior-period/version changes and comparative implications | |

A tolerance is a documented review decision, not permission to discard an unexplained amount. Record unresolved differences explicitly even if the total is small or nets to zero.

## Filled fictional mapping record

Assume a ledger export has 75 source rows totaling 900 thousand USD. Sixty rows totaling 720 have candidate mappings, ten rows totaling 150 have conflicting candidate destinations, and five rows totaling 30 have no destination. These three groups are stipulated to be disjoint and exhaustive. Candidate mapping does not mean accepted mapping.

| Group | Rows | Amount, thousand USD | Status |
|---|---:|---:|---|
| One candidate destination identified | 60 | 720 | Criteria/evidence review still required |
| Conflicting candidate destinations | 10 | 150 | Unresolved |
| No destination identified | 5 | 30 | Unresolved |
| Total source population | 75 | 900 | Ties to supplied export |

Count coverage of rows with one candidate is **60/75 = 80%**; amount coverage is **720/900 = 80%**. They happen to agree here. A different population could yield very different percentages. Neither demonstrates that the sixty candidate mappings are correct or approved. The unresolved amount is **150 + 30 = 180**, and the unresolved row count is **10 + 5 = 15**.

## One source row can need multiple supported destinations

Suppose one 100-thousand-USD ledger row contains two identifiable components, 70 and 30. A validly supported split would preserve the parent key, both component identities, their destination criteria and a **70 + 30 = 100** reconciliation. Two output rows are not automatically duplicates. Conversely, repeating the entire 100 in both destinations creates 200 and overstates coverage by 100.

This is an original mapping-control example, not a prescribed FERC allocation. Do not invent an allocation percentage from a convenient target. Establish the underlying components and authorized treatment, or leave the split unresolved.

## Minimum evidence for a mapping change

When a proposed mapping changes, preserve the old map, new map, affected source rows, reason, relevant authority/version, and the actual approval. Recalculate affected totals and identify impacts on comparative periods. If a destination changes but the total remains 900, numerical reconciliation alone will not reveal the classification change.

Attach the review to the exact map and source snapshot, not merely to a workpaper title. If the ledger changes after approval, determine which mappings and totals need rechecking. A previous signature cannot approve unknown later facts. Leave release authority separate from the preparer's ability to edit a spreadsheet.

## Red flags worth retaining in the output

An unmatched row; two destinations claiming the same entire amount; a source unit mismatch; a negative balance forced positive; a stale taxonomy; a historical instruction treated as current; a proposed adjustment labeled accepted; or an unexplained residual hidden within tolerance. Each has a different remedy. A single status named “validated” can conceal the distinctions, so report exactly which checks passed and which decisions remain open.

## Distinct gates before use

Record permission for each source operation, workspace/user access, technical and date-applicability reviews, and exact workpaper revision/hash. The specialist must supply actual identity, review date, scope and findings; leave fields blank until performed. An automated calculation or second model pass is not independent review. Fresh Agent entitlement is separate from all evidence permissions.

Complete manual review and separately obtain operator authorization before any posting or filing. This template creates neither permission nor an approval. Selected official regulatory passages were checked as described below; they do not resolve transaction-specific blank authority fields or replace the unverified form instructions.

## Sources and verification

Editorial checking on October 4, 2026 reached the exact existing [FERC accounting index](https://ferc.gov/accounting-matters-1) [ferc-accounting-directory] and [electric forms index](https://ferc.gov/general-information-0/electric-industry-forms) [ferc-electric-forms-directory]. The earlier HTTP 403 observation is historical; it is not the outcome of this check. The accounting index distinguishes regulations, orders and Chief Accountant guidance, and visibly labels some entries rescinded or superseded. The forms index contains separate Form 1, 1-F and 3-Q sections; its linked Form 1 instructions page is dated August 3, 2022. The linked PDF could not be opened by this review tool, so its detailed instructions were not verified.

The accounting index led to [18 CFR Part 101](https://www.ecfr.gov/current/title-18/chapter-I/subchapter-C/part-101), General Instructions 2 and 3. The inspected eCFR display stated that Title 18 was current through September 21, 2026 and was authoritative but unofficial. Selected passages address intelligible supporting records, account-number reconciliation and the distinction between account sequence and report-form sequence. This is limited source context, not a complete intervening-amendment search or a determination of the fictional entity's obligations.

Only short factual descriptions and official links are included; no government form, third-party filing, protected standard, diagram or source table is reproduced. No broad rights in all FERC-hosted material are assumed. Account, schedule, taxonomy and entity-specific applicability questions remain unapproved.

## Standard education and Premium execution

This original article remains free Standard educational content under CC BY 4.0. Premium licenses private software workflow execution only where the feature is available and the required permissions exist. It does not sell ownership of government text, supply publisher rights, establish a correct accounting treatment, or create professional approval. No real filing, posting, model call or private workflow was executed for this lesson.


---
Original content: Open Accounting contributors · CC BY 4.0 · Version 1.0.0 · 2026-10-04. Third-party sources retain their own rights.
