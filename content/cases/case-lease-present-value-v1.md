# Worked case: distinguish annual present value, displayed rounding and monthly-tool inputs

**AI-assisted educational draft · v1.1.0 · 2026-10-04 · AI editorial checks only; no human professional review.**

## Stipulated annual example

Assume three payments of USD 10000 at the ends of years one, two and three, annual compounding and a stipulated 6% effective annual rate. No other flows are included. These are mathematical premises; no actual rate selection, lease identification, classification or professional approval is supplied.

Current primary ASC text was not accessed. Topic 842 remains a research reference rather than verified authority for this calculation's accounting use. [fasb-asc]

## Present value and rollforward

Compute 10000/1.06 + 10000/(1.06²) + 10000/(1.06³) = approximately USD 26730.12. Carry higher precision internally. For each period, interest is opening balance ×6%; closing balance is opening plus interest minus the positive payment amount.

| Year | Opening | Interest | Payment | Closing |
|---|---:|---:|---:|---:|
| 1 | 26730.12 | 1603.81 | 10000.00 | 18333.93 |
| 2 | 18333.93 | 1100.04 | 10000.00 | 9433.96 |
| 3 | 9433.96 | 566.04 | 10000.00 | 0.00 |

The displayed cells are independently rounded from the higher-precision calculation. In year two, adding only the displayed opening and interest and subtracting the displayed payment gives 9433.97, one cent above the displayed high-precision closing amount. This specific difference was reproduced; “rounding” is not a blanket excuse for other unexplained differences.

The high-precision final residual is effectively zero under the stated formula. Total payments are USD 30000; the difference from the unrounded present value is approximately USD 3269.88, equal to the aggregate modeled interest before final display rounding.

## Earlier payment counterexample

Move the three payments to times zero, one and two, keeping the annual rate and amounts unchanged. Present value becomes 10000 + 10000/1.06 + 10000/(1.06²), approximately USD 28333.93. The difference from the end-of-year schedule is approximately USD 1603.81 using unrounded results.

This is a separate timing branch, not an assertion that payments in advance are required. Actual contractual payment dates and the relevant accounting criteria must be established before using either result.

## Keep the product helper's scope visible

The inspected sample helper supports monthly fixed payments in arrears and a supplied nominal annual rate divided by twelve. It does not directly calculate the three annual-payment schedule above or accept advance-payment timing. Entering these yearly payments as three monthly payments would answer a different question.

This annual table is therefore an independently calculated educational example, not a claim of full tool support. The helper also does not determine right-of-use asset adjustments, classification, rate selection, modifications, variable payments, tax or presentation.

## Requested handoff

Keep exact amounts, payment times, rate convention, formula precision, displayed rounding and omitted features next to the result. Verify current authority, entity facts and the complete arrangement before adapting the illustration to a real agreement.

The earlier case body and strict historical fixture are preserved. This successor does not rebind that fixture or turn its numeric target into a professional accounting benchmark.

## Source and permission boundary

- [FASB Codification home](https://asc.fasb.org/): research entry point only; current primary ASC text was not accessed
- [FASB home](https://fasb.org/): publisher entry point only; project/announcement references do not establish current accounting requirements or source-use permissions

Publisher restrictions were identified October 4, 2026 and further FASB retrieval stopped. No ASU/ASC body was acquired. This original exercise does not replace authorized primary-source review of scope, amendments, exceptions or reporting-period applicability.

Original educational content by Open Accounting contributors, AI-assisted. Licensed under **CC BY 4.0**. Original explanations and fictional examples remain freely readable. No third-party standard body is reproduced or relicensed. This article grants no publisher rights, professional approval or Agent admission and supplies no final accounting conclusion.
