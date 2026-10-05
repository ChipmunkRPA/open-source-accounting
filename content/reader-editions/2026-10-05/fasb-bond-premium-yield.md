# Purchased bond premiums: reconcile coupon cash with effective interest

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

**Ray Sang Annotation**

**Original educational explanation · Version 1.0.0 · 2026-10-04**

By Open Source Accounting contributors. No human professional review is recorded; this brand does not imply that Ray Sang personally reviewed the article.

## Why the coupon does not determine the yield

A bond's contractual coupon describes cash relative to face value. A purchaser's effective yield also reflects the price paid and payment dates. Paying more than the principal ultimately returned creates a premium that must be incorporated into that purchaser's return.

OCC's selected staff response treats purchased-security premiums and discounts as yield adjustments using the interest method, subject to separate call and prepayment exceptions. This guide illustrates only the noncallable, nonprepayable case. It is an original purchased-investment schedule, not an origination-fee example or a reproduction of OCC's callable-bond illustration.

## Define all four payment periods

A fictional investor purchases a bond immediately after a coupon date. Contractual principal is $60,000, annual cash coupons are $4,200, and principal is repaid with the fourth annual coupon. The coupon rate is 7%. The stipulated market effective yield at purchase is 5% annually.

Assume full collection, annual periods of equal length, no accrued coupon in the purchase price, no fees, no tax, no optional redemption, no prepayments, no floating rate and no credit loss. The exercise calculates amortized cost; any separately applicable fair-value or OCI layer is outside the table. It does not decide the investment category.

The independently calculated purchase price is:

$4,200 / 1.05 + $4,200 / 1.05² + $4,200 / 1.05³ + $64,200 / 1.05⁴ = $64,255.1406049948…

Thus the premium is $4,255.1406049948… above the $60,000 principal. The $64,200 final contractual receipt contains both the last $4,200 coupon and the $60,000 principal; do not count that principal twice.

## Build the carrying-value schedule

For each year, interest income equals opening amortized cost multiplied by 5%. Premium amortization equals coupon cash minus effective interest. Closing amortized cost equals opening amortized cost plus effective interest minus coupon cash.

| Year | Opening amortized cost | Effective interest | Coupon cash | Premium amortization | Closing, before principal receipt |
|---|---:|---:|---:|---:|---:|
| 1 | $64,255.14 | $3,212.76 | $4,200.00 | $987.24 | $63,267.90 |
| 2 | $63,267.90 | $3,163.39 | $4,200.00 | $1,036.61 | $62,231.29 |
| 3 | $62,231.29 | $3,111.56 | $4,200.00 | $1,088.44 | $61,142.86 |
| 4 | $61,142.86 | $3,057.14 | $4,200.00 | $1,142.86 | $60,000.00 |

The displayed amounts are rounded independently to cents from a full-precision schedule. A displayed row may consequently differ by one cent when recomputed from the rounded columns. For example, the rounded year-two opening balance less displayed amortization is $62,231.29, while multiplying that rounded opening by 5% does not preserve every underlying fraction of a cent. Keep precision and rounding policy explicit in an actual ledger.

At purchase, the illustrative entry debits the investment and credits cash for the purchase price. The first coupon entry, at displayed precision, debits cash $4,200, credits interest income $3,212.76 and credits the investment premium $987.24. The premium is part of the investment's carrying amount, not an additional future cash receipt.

After the fourth coupon, the remaining $60,000 carrying amount is cleared by debit cash $60,000 and credit investment $60,000. The schedule's final investment balance is then zero.

## Reconcile the whole investment

Four coupons total $16,800. Total effective interest is $12,544.8593950052…, and total premium amortization is $4,255.1406049948…. Their sum is exactly $16,800 before rounding.

A separate lifetime check gives the same interest: total contractual cash of $76,800 minus purchase price of $64,255.1406049948… equals $12,544.8593950052…. Cash coupons exceed effective income because part of each coupon economically recovers the amount paid above principal.

Straight-line premium amortization would be approximately $1,063.79 annually. It would not reproduce this effective-interest schedule: the first-year effective amortization is $987.24, and the last is $1,142.86. Numerical convenience is not a reason to silently change methods.

## Reverse the coupon relationship

Keep principal, maturity and the 5% effective yield unchanged, but stipulate coupons of $1,800, or 3% of principal. The independently calculated price becomes $55,744.8593950052…, a discount of $4,255.1406049948….

First-year effective interest is $2,787.24, exceeding the $1,800 cash coupon by $987.24. The difference increases amortized cost to $56,732.10. At full precision, subsequent year-end balances are $57,768.71, $58,857.14 and $60,000.00 when displayed to cents. Discount accretion moves the investment toward principal from below; premium amortization approaches it from above.

If a call feature, prepayment assumption or collection problem appears, stop and reassess the applicable model and cash-flow horizon. Neither schedule resolves those changed facts.

## Precise source and retained limits

- [OCC Bank Accounting Advisory Series](https://www.occ.treas.gov/publications-and-resources/publications/banker-education/files/pub-bank-accounting-advisory-series.pdf): August 2026, section 1A questions 16–17, printed pages 8–9. Question 17 supports scope exclusions only; its numerical example is not used. This is bank-specific staff interpretation, not OCC rules, with a March 31, 2026 issue-observation cutoff
- Publisher authority pointer: ASC 310-20; [FASB Codification homepage](https://asc.fasb.org/), reference only

Sources were checked October 4, 2026, not an effective-date determination. Current publisher-standard text, amendments and entity applicability remain unverified. Professional review and Agent admission remain unperformed.

New first-party text is expressly designated **LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0** under [CONTENT-TERMS.md](https://github.com/ChipmunkRPA/open-source-accounting/blob/4ffc83f154a152c453438eafe63e8b6b77f27a93/CONTENT-TERMS.md), only to the extent rights exist and are controlled. Facts, third-party material and existing grants are excluded.
