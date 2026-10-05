# Debt replacement: compare revised cash flows before choosing a gain or loss

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

**Ray Sang Annotation**

**Original educational explanation · Version 1.0.0 · 2026-10-04**

By Open Source Accounting contributors. No human professional review is recorded; this brand does not imply that Ray Sang personally reviewed the article.

## A threshold is one part of the analysis

Replacing loan documents can change interest, payment timing, principal and other rights. The accounting question is not answered by the document's label or by the borrower's wish to defer a cost.

OCC's selected borrowing discussion distinguishes modification from extinguishment and describes a present-value difference of at least 10%, measured using the original effective rate, as one substantially-different indicator. This article illustrates that quantitative comparison. It does not provide a complete ASC 470 assessment or establish that a result below 10% automatically means modification.

## Original contract and two unaccepted proposals

A fictional business has a plain $50,000 term borrowing. Immediately after a scheduled interest payment, three annual payments remain: $3,000 interest in one year, $3,000 in two years, and $53,000 principal plus interest in three years. The original effective annual rate is 6%, with no remaining discount, premium or issuance cost.

Two mutually exclusive proposals from the same creditor shorten final maturity to two years. Each requires $10,000 principal repayment after one year and the remaining $40,000 after two years. Proposal A charges 12% annually on the outstanding principal; proposal B charges 14%.

For this exercise, there are no immediate payments, fees, accrued unpaid interest, third-party costs, embedded conversion rights, guarantees, lender changes or distressed-borrower concessions. No proposal is stipulated to be accepted. A real comparison must identify any such omitted feature and determine whether it changes scope or the cash flows to include.

These are independently designed staged repayments. They do not reproduce the source's FHLB advance or rolled-prepayment-penalty example.

## Construct cash flows before discounting

Proposal A's first payment is $10,000 principal plus 12% × $50,000 interest, or $16,000. After that principal repayment, its second payment is $40,000 plus 12% × $40,000, or $44,800.

Proposal B similarly produces $17,000 after one year and $45,600 after two. Neither calculation charges a second year's interest on the $10,000 already repaid.

| Years after comparison date | Original borrowing | Proposal A | Proposal B |
|---|---:|---:|---:|
| 1 | $3,000 | $16,000 | $17,000 |
| 2 | $3,000 | $44,800 | $45,600 |
| 3 | $53,000 | $0 | $0 |
| Undiscounted total | $59,000 | $60,800 | $62,600 |

The undiscounted totals are a completeness check, not the specified present-value test. Proposal B's total exceeds the original by only $3,600, or approximately 6.10% of the original total. That comparison ignores the earlier repayment dates and answers a different question.

## Use one discount rate for both sides

Discount every schedule at the original 6% effective rate. Do not discount each proposal at its own stated coupon rate; doing so would erase part of the difference the comparison is meant to measure.

Original PV = $3,000 / 1.06 + $3,000 / 1.06² + $53,000 / 1.06³ = $50,000.

Proposal A PV = $16,000 / 1.06 + $44,800 / 1.06² = $54,966.180135….

Proposal B PV = $17,000 / 1.06 + $45,600 / 1.06² = $56,621.573514….

For this stipulated comparison, calculate absolute PV difference divided by original PV:

| Proposal | Absolute difference | Percentage, before coarse rounding | Quantitative observation |
|---|---:|---:|---|
| A | $4,966.18 | 9.932360…% | Below 10% |
| B | $6,621.57 | 13.243147…% | At least 10% |

Rounding A to a whole percent would display 10%, but its unrounded result is below the threshold. Compare at sufficient precision before formatting the result for a memo. A threshold is not permission to manipulate the payment population or rounding convention.

## Separate the result from the journal entry

A's result does not independently prove modification accounting. Qualitative changes, model scope and completeness still need assessment. B meets the illustrated quantitative indicator, but final treatment still requires an applicable model and a complete supported fact pattern.

Neither $4,966.18 nor $6,621.57 is automatically an extinguishment loss. Those figures are differences in a test using the original rate. They are not a current fair-value measurement of replacement debt, a settlement amount, or a determination of treatment for any unamortized costs.

No journal entry is proposed at this unaccepted-proposal stage. If an agreement is executed, first establish the applicable modification or extinguishment conclusion, relevant measurement inputs and any cost treatment. Only then construct the entry and reconcile the old liability, cash, replacement liability and recognized result.

## Changed facts and precise source

An immediate creditor fee, principal paid at signing or a new conversion right would require revisiting the analysis. Preserve those facts explicitly rather than appending them after the threshold result has been approved.

- [OCC Bank Accounting Advisory Series](https://www.occ.treas.gov/publications-and-resources/publications/banker-education/files/pub-bank-accounting-advisory-series.pdf): August 2026, section 6B questions 1–2, printed pages 116–117. Staff interpretation, not OCC rules; issue-observation cutoff March 31, 2026
- Publisher authority pointer: ASC 470-50; [FASB Codification homepage](https://asc.fasb.org/), reference only

Checked October 4, 2026, not an effective-date determination. Current publisher-standard text, amendments and entity applicability remain unverified. Professional review and Agent admission remain unperformed.

New first-party text is expressly designated **LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0** under [CONTENT-TERMS.md](https://github.com/ChipmunkRPA/open-source-accounting/blob/4ffc83f154a152c453438eafe63e8b6b77f27a93/CONTENT-TERMS.md), only to the extent rights exist and are controlled. Facts, third-party material and existing grants are excluded.
