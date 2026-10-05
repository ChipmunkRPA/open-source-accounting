# Mortgage commitments: separate notional, fair value and earnings

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

**Ray Sang Annotation**

**Original educational explanation · Version 1.0.0 · 2026-10-05**

By Open Source Accounting contributors. Professionally unreviewed; no human review is recorded, and this label does not imply personal review by Ray Sang. This is a bounded bank-accounting exercise using government application guidance, not an official FASB publication, an ASC substitute or a completed accounting policy.

## Decide which register an arrangement belongs in

A promise to originate a loan is not the funded loan itself. The researcher needs the contract, loan type and intended disposition before selecting a measurement model. A spreadsheet headed “pipeline” does not supply those facts.

The OCC's August 2026 Bank Accounting Advisory Series, Topic 2C, questions 5–7, distinguishes mortgage origination commitments for loans intended for sale from excluded origination commitments. The former are accounted for as derivatives with fair-value changes in earnings; the latter require their own accounting analysis. Questions 8–10 distinguish probability-sensitive valuation from gross notional reporting. These are the selected OCC staff explanations of ASC-related requirements, not independently verified current ASC paragraphs. [OCC, printed pages 38–40 / PDF pages 42–44](https://www.occ.treas.gov/publications-and-resources/publications/banker-education/files/pub-bank-accounting-advisory-series.pdf#page=42).

For an intake register, assign separate columns to intended disposition, evidence for that intention, derivative-scope conclusion, valuation version and open questions. An excluded commitment does not automatically have zero credit exposure or zero accounting consequences. Its treatment simply is not determined by the derivative calculation below.

## Synthetic close: the net total conceals three movements

All entities, amounts and circumstances below are invented. Assume a fictional bank has three already assessed groups of mortgage origination commitments for loans intended for sale. Every contract remains outstanding throughout the interval. There are no new commitments, expirations, settlements, collateral balances or fees. The independently supplied fair values already incorporate all required valuation inputs. No offsetting is assumed to be permitted.

Positive values represent assets; negative values represent liabilities. Dollar amounts are not percentages of notional.

| Group | Gross notional | Opening signed fair value | Closing signed fair value | Change in earnings |
|---|---:|---:|---:|---:|
| Cedar | $1,200,000 | $18,000 | $26,000 | $8,000 gain |
| Elm | $900,000 | $9,000 | ($4,000) | $13,000 loss |
| Maple | $600,000 | ($7,000) | ($2,000) | $5,000 gain |
| Arithmetic total | $2,700,000 | $20,000 | $20,000 | $0 net |

The $20,000 signed total is a reconciliation control, not an instruction to present one net asset. Opening gross assets are $27,000 and liabilities are $7,000. Closing gross assets are $26,000 and liabilities are $6,000. Both sides fall by $1,000 while the signed total stays unchanged.

Looking only at the $0 aggregate earnings change would miss Elm's movement through zero. Looking only at $2,700,000 of notional would miss every valuation movement. Neither shortcut explains what happened.

## Reconcile the entries by contract group

Under the exercise's supplied measurements, Cedar's change debits the commitment asset $8,000 and credits valuation gain $8,000. Elm debits valuation loss $13,000, credits its existing asset $9,000 to remove it, and credits a commitment liability $4,000. Maple debits its liability $5,000 and credits valuation gain $5,000.

Across those entries, debits and credits each total $26,000. Gains of $13,000 offset the $13,000 loss. These entries explain why a zero net earnings result can still require changes to the asset and liability registers. They do not show a $2,700,000 loan receivable or cash disbursement because the assumed commitments have not funded.

For operational control, retain the contract identifiers behind each group. A group summary should not combine positive and negative contracts so early that the gross asset and liability populations can no longer be reconstructed. The example supplies homogeneous signed balances only to keep the reconciliation small.

## Expected funding is a different calculation

Suppose an operations team separately forecasts funding rates of 80% for Cedar, 60% for Elm and 70% for Maple. Its planning calculation is $960,000 + $540,000 + $420,000 = $1,920,000 of expected funding. The difference from gross notional is $780,000.

The $1,920,000 forecast is not a replacement for the $2,700,000 notional register, the $26,000 asset total or the $6,000 liability total. It also is not a fair-value method. Multiplying the supplied fair values by these rates again would double-apply a probability adjustment if that adjustment is already embedded. Before using an input, identify which model has already used it.

Add a $2,000,000 commitment to originate mortgages intended for investment and a $750,000 nonmortgage origination commitment. The complete operational register now totals $5,450,000. The derivative population in this exercise remains $2,700,000. Route the other $2,750,000 to separate scope, credit-loss and any fair-value-option research rather than omitting it from the population or forcing it into the same model.

## Change one estimate without rewriting the facts

In a parallel sensitivity, Maple's closing liability is $6,000 instead of $2,000; all other facts stay fixed. Closing gross assets remain $26,000, liabilities become $10,000, and net signed value is $16,000. Maple's gain is then $1,000, producing a $4,000 net loss across the three groups.

That $4,000 difference is entirely a valuation sensitivity. It does not change notional, confirm a funding event or demonstrate that the chosen valuation assumptions are reasonable. A reviewer still needs the actual model inputs and their evidence.

## Source boundary and next evidence

Source ID: **osa-occ-mortgage-commitment-derivatives**. The official August 2026 OCC edition was examined October 5, 2026. The source-only checkpoint was committed before this guide was drafted. No OCC source body or protected FASB standard text is included here. Source issue month is not an entity-specific effective date.

Hedge designation and effectiveness, collateral and offsetting rights, loan funding and sale accounting, fees, tax, current ASC amendments and actual valuation construction are outside the exercise. Source rights, applicability, professional review and Agent admission remain separate gates; primary-text gaps remain and default Agent eligibility is false.

New first-party prose and examples are expressly designated **LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0** under [CONTENT-TERMS.md](https://github.com/ChipmunkRPA/open-source-accounting/blob/4ffc83f154a152c453438eafe63e8b6b77f27a93/CONTENT-TERMS.md), only to the extent rights exist and are controlled. Facts, government text, third-party rights, prior grants and statutory/platform exceptions retain their own treatment.
