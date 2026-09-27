# Worked case: an explicitly assumed foreign-currency payable

**AI-assisted editorial draft · v0.6.0 · 2026-09-27 · No professional review recorded.**

A unit-checked numerical scenario; all accounting classification assumptions require separate confirmation.

## Stipulated inputs

An entity has a USD functional currency and a EUR 100,000 payable. For this exercise only, assume the initial applicable rate is USD 1.10 per EUR and the closing applicable rate is USD 1.12 per EUR. Assume the balance is unpaid at period-end and is measured using those rates. This example does not determine functional currency or the correct rate policy.

## Calculation

Initial USD amount: EUR 100,000 × USD 1.10/EUR = USD 110,000. Closing USD amount: EUR 100,000 × USD 1.12/EUR = USD 112,000. The stipulated liability increases by USD 2,000. A draft entry under those assumptions would debit exchange loss and credit the payable by USD 2,000. It must not be automatically posted.

## Counterexample and control

If the quoted rate were EUR per USD, the calculation would require a different conversion operation. Multiplying the same number without checking units is an error even if the result looks plausible. Settlement, hedge relationships, a different functional currency, or specialized balances require separate research.

## Reviewer and Agent tests

Require explicit rate direction, source date, amount, currency, and measurement assumptions. Reject missing rate units. Keep transactional exchange analysis separate from consolidation translation. The example is suitable for checking arithmetic, not for proving that an ERP's exchange-rate configuration complies with GAAP.

## Sources and verification

- [FASB Accounting Standards Codification](https://asc.fasb.org/) — reference only; current Codification text not reviewed.

Original educational content by Open Source Accounting contributors, AI-assisted. Licensed under **CC BY 4.0**. No third-party standard text is relicensed. Do not use this draft as an audit opinion, certification, or final accounting conclusion.
