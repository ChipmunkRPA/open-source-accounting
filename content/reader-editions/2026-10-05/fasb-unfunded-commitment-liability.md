# Unfunded commitments: connect expected draws to a separate loss liability

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

**Ray Sang Annotation**
Original educational analysis and invented example. Editorial draft; no personal accounting review, human professional approval or Agent admission is implied.

## Source boundary

OCC excludes unconditionally cancellable commitments from this estimate. For covered exposures, expected losses reflect expected funding and are recorded in a liability, with an earnings charge. [OCC Bank Accounting Advisory Series, Topic 12E, questions 1–3](https://www.occ.treas.gov/publications-and-resources/publications/banker-education/files/pub-bank-accounting-advisory-series.pdf#page=240).

Those are the narrow source premises. The following cohort design, numbers, formulas and workpaper checks are original teaching choices. They are not a prescribed CECL model, a credit-risk forecast or an acquired copy of ASC 326.

## Resolve scope before multiplying balances

A fictional bank has three small portfolios of undrawn nonmortgage lending commitments. For this exercise, a completed contract assessment stipulates that Portfolio A and Portfolio B are within the covered population and are not unconditionally cancellable. Portfolio C is stipulated to be unconditionally cancellable. A reviewer cannot replace that contract assessment with a product label or a spreadsheet flag in real work.

There are no guarantees, letters of credit, insurance contracts, derivatives or fair-value-option contracts in the case. The bank has no funded draws during the illustrated close, no fees, no tax effects and no other liability movements. Existing funded loans are accounted for in a separate ledger. Their balances are not an input to the undrawn register.

The model deliberately separates three assumptions. The funding probability is the chance that some funding occurs over the remaining contractual exposure period. The conditional draw fraction is the share of today's undrawn limit expected to fund if that event occurs. The conditional loss rate is the stipulated lifetime loss fraction on those expected draws. It already incorporates the case's credit-loss assumptions; it is not a one-year default rate or a rate that should be multiplied by another default probability.

In each fictional portfolio, supplied homogeneous assumptions make the product below a usable teaching simplification. Real heterogeneous or correlated outcomes could require scenario-level calculations and a different estimation method.

| Portfolio | Undrawn limit | Funding probability | Conditional draw fraction | Expected funding | Conditional lifetime loss rate | Estimated loss |
|---|---:|---:|---:|---:|---:|---:|
| A, covered | $2,400,000 | 70% | 60% | $1,008,000 | 3.0% | $30,240 |
| B, covered | $1,600,000 | 50% | 80% | $640,000 | 2.5% | $16,000 |
| C, scope excluded | $800,000 | Not used | Not used | Not in estimate | Not used | $0 in this estimate |

For A, $2,400,000 × 70% × 60% = $1,008,000, followed by $1,008,000 × 3% = $30,240. For B, $1,600,000 × 50% × 80% = $640,000, followed by $640,000 × 2.5% = $16,000.

The total covered limit is $4,000,000. Expected covered funding is $1,648,000, and the required closing liability in this invented model is $46,240. The complete contract register still totals $4,800,000 because the excluded $800,000 remains visible. Exclusion from this estimate is not a claim that Portfolio C has no operational, liquidity or commercial risk.

## Reconcile the liability rather than recording the whole ending estimate again

The opening liability is $39,000. With no other movements in the stipulated case, the adjustment is $46,240 − $39,000 = $7,240. The illustrative entry debits credit-loss provision expense $7,240 and credits the off-balance-sheet credit-loss liability $7,240.

Recording a fresh $46,240 charge on top of the existing $39,000 would produce an $85,240 liability. That is not the required close. The rollforward should show the opening amount, all separately supported movements and the residual change needed to reach the new estimate. Our simple example has only that last change.

The bank separately has $5,200,000 of funded loan assets and an $84,000 related allowance. Those supplied amounts yield $5,116,000 of net loans. The $46,240 commitment liability appears separately. It is not a further reduction to the $5,200,000 gross loan balance.

If an entry instead moved the commitment liability into the funded-loan allowance, net loans would become $5,069,760 and liabilities would fall by $46,240. The net-assets result would happen to be unchanged, but both balance-sheet categories would be understated by $46,240. An equality check on total net assets alone would miss this presentation error.

## Test sensitivity without changing two inputs accidentally

In an independent higher-draw scenario, increase only Portfolio A's conditional draw fraction from 60% to 75%. Keep funding probability at 70%, loss rate at 3% and all of Portfolio B unchanged.

A's expected funding becomes $1,260,000 and estimated loss becomes $37,800. Add B's $16,000 to obtain a $53,800 liability. This is $7,560 above the base case. If starting from the same $39,000 opening liability, the total close adjustment would be a $14,800 charge. These are two different comparisons; do not post both.

As a separate algebraic boundary test, set A's expected funding to zero while leaving B unchanged. The required liability becomes $16,000. Against the same opening $39,000, that implies a $23,000 release in this isolated example. A real zero-funding conclusion would need support; a developer's boundary test is not that evidence.

## Keep assumption provenance visible

A reviewable file needs the contract population, cancellation conclusions, remaining exposure periods, cohort rationale and an explanation of each input's horizon and conditioning. Record whether a supplied loss rate already incorporates funding behavior. Multiplying a funding-adjusted rate by a second funding probability can understate the result.

Tie the liability rollforward to the general ledger and reconcile covered plus excluded commitments to the complete register. Maintain a separate funded-loan allowance reconciliation. Once an actual draw occurs, refresh both populations and analyze the transition rather than leaving the same exposure in both estimates by inertia. That subsequent transaction is outside this no-draw exercise.

## Precise reference and retained gaps

- [OCC Bank Accounting Advisory Series](https://www.occ.treas.gov/publications-and-resources/publications/banker-education/files/pub-bank-accounting-advisory-series.pdf): August 2026 edition, Topic 12E questions 1–3, printed pages 236–237 / PDF pages 240–241. Official text examined October 5, 2026; issue-observation cutoff March 31, 2026
- ASC 326-20 and ASC 326-20-30-11 are OCC-supplied authority pointers; the [FASB Codification](https://asc.fasb.org/) remains reference-only here

OCC staff commentary is not an OCC regulation or FASB-authored standard. Only metadata and locators were saved before authoring; this batch adds no complete source body or protected standard. Current applicability, cancellation-law analysis, model suitability, forecast support and professional technical review remain unresolved. Default Agent eligibility remains denied.

New first-party text is expressly designated **LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0** under [CONTENT-TERMS.md](https://github.com/ChipmunkRPA/open-source-accounting/blob/4ffc83f154a152c453438eafe63e8b6b77f27a93/CONTENT-TERMS.md), only to the extent rights exist and are controlled. Facts, third-party material, prior grants, statutory exceptions and platform agreements are preserved.
