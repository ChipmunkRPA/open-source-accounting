# Worked case: an explicitly assumed foreign-currency payable

**AI-assisted editorial draft · v1.0.0 · 2026-10-04 · No professional review recorded.**

A unit-checked numerical scenario; all accounting classification assumptions require separate confirmation.

## Stipulated inputs

An entity has a USD functional currency and a EUR 100,000 payable. For this exercise only, assume the initial applicable rate is USD 1.10 per EUR and the closing applicable rate is USD 1.12 per EUR. Assume the balance is unpaid at period-end and is measured using those rates. This example does not determine functional currency or the correct rate policy.

## Calculation

Initial USD amount: EUR 100,000 × USD 1.10/EUR = USD 110,000. Closing USD amount: EUR 100,000 × USD 1.12/EUR = USD 112,000. The stipulated liability increases by USD 2,000. A draft entry under those assumptions would debit exchange loss and credit the payable by USD 2,000. It must not be automatically posted.

## Counterexample and control

If the quoted rate were EUR per USD, the calculation would require a different conversion operation. Multiplying the same number without checking units is an error even if the result looks plausible. Settlement, hedge relationships, a different functional currency, or specialized balances require separate research.

## Extend the chronology to settlement

Continue only the stipulated payable example. Assume the entire EUR 100,000 is settled after year end at a hypothetical USD 1.15/EUR, with no fees, discounts, hedges, partial payments or other movements. Settlement cash is **USD 115,000**. Relative to the stipulated closing liability of USD 112,000, the additional increase is **USD 3,000**. Relative to initial USD 110,000, the total increase is **USD 5,000**.

The bridge is **110,000 + 2,000 + 3,000 − 115,000 = 0**. It separates the supplied period-end measurement from the later settlement event. It does not decide subsequent-event reporting, the applicable accounting framework or the actual accounts to post. In a real file, retain each date, the unpaid status at cutoff, the applicable measurement authority and the settlement evidence.

If the settlement record includes a separate USD 500 bank charge, total cash paid becomes **USD 115,500**. The extra 500 is not explained by changing the EUR/USD rate in this fact packet. Keep it separate and research its classification. A composite bank debit does not prove that every dollar is an exchange difference.

## Partial settlement changes both the population and the bridge

Use a separate scenario from inception. EUR 40,000 of the EUR 100,000 payable is settled before period-end at USD 1.11/EUR. Assume the initial measurement was USD 1.10/EUR for all units, and the remaining EUR 60,000 is measured at USD 1.12/EUR at cutoff.

- Initially measured portion settled: **40,000 × 1.10 = USD 44,000**
- Cash for that portion: **40,000 × 1.11 = USD 44,400**
- Difference for the settled portion: **USD 400**
- Initially measured portion remaining: **60,000 × 1.10 = USD 66,000**
- Closing remaining balance: **60,000 × 1.12 = USD 67,200**
- Difference for the remaining portion: **USD 1,200**

The stipulated overall bridge is **110,000 + 400 + 1,200 − 44,400 = 67,200**. Applying the closing rate to all EUR 100,000 would ignore the partial settlement. Subtracting EUR 40,000 directly from a USD balance would mix currencies. Every quantity and conversion must remain explicit.

## A receivable is a different position

For a separate teaching scenario, replace the liability with a EUR 100,000 receivable measured at the same assumed USD 1.10 and 1.12 rates. Its USD amount also increases by 2,000, but the economic direction for the holder differs from the payable example. A template that copies the label “exchange loss” merely because a number increased would be misleading. Actual recognition and presentation still require applicable authority and facts.

Do not net unrelated receivables and payables to obtain a favorable-looking total without establishing whether netting is permitted and meaningful. A net exposure schedule is a distinct analytical view from each recorded balance or required presentation.

## Study checks

1. Why is the post-year-end movement 3,000 rather than 5,000? The supplied closing balance already contains the 2,000 change from initial measurement.
2. Why does the partial-payment closing balance equal 67,200? Only EUR 60,000 remains under that separate scenario.
3. Does the 500 bank charge prove an additional exchange loss? No; the facts identify a separate charge with its own classification question.
4. Does a balanced bridge approve posting? No; it verifies only the supplied arithmetic and chronology.

## Reviewer and Agent tests

Require explicit rate direction, source date, amount, currency, and measurement assumptions. Reject missing rate units. Keep transactional exchange analysis separate from consolidation translation. The example is suitable for checking arithmetic, not for proving that an ERP's exchange-rate configuration complies with GAAP.

## Sources and verification

The [FASB homepage](https://fasb.org/) [fasb-asc] is a human research starting point only. Current project source review identified FAF/FASB/GASB restrictions on AI use, automated collection and non-homepage linking. No restricted standard body, alternate copy or current accounting paragraph was acquired for this revision. Exact applicable Codification text, effective dates, elections and transition remain unverified.

AI editorial checking on October 4, 2026 covers the original explanations and calculations under explicit assumptions. It is not a human CPA/auditor attestation or a claim that an unavailable source has been reviewed. The publication does not create source-operation rights or automatic Agent admission.

## Standard education and Premium execution

This original article remains free Standard educational content under CC BY 4.0. Premium licenses private software workflow execution only where available and authorized. It does not grant publisher rights, settle accounting conclusions, or supply professional review. The examples do not perform a private workflow, model run, configuration change, filing or journal posting. Feature availability and execution permissions require separate verification.

Original educational content by Open Source Accounting contributors, AI-assisted. Licensed under **CC BY 4.0**. No third-party standard text is relicensed. Do not use this draft as an audit opinion, certification, or final accounting conclusion.
