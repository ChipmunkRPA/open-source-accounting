# Worked case: units, duplicate meters and an intensity claim

**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.

> **Editorial draft — not professionally reviewed.** Original educational material. No standard text or real emissions factors are reproduced. No compliance, materiality, assurance or accounting conclusion is established.

## Hypothetical inputs

Juniper Works is fictional. Its one-month demonstration includes only two named sites. All factors below are invented teaching constants, not an official factor database or a recommended method. No classification as Scope 1, 2 or 3, market/location-based treatment, offset treatment or reporting boundary has been approved.

| Input ID | Site | Activity as received | Fictional factor | Status |
|---|---|---|---|---|
| A-01 | A | 12,500 kWh | 0.40 kg CO2e/kWh | Unique observation |
| B-01 | B | 18 MWh | 0.25 kg CO2e/kWh | Unique observation; convert units |
| B-01-copy | B | Copy of the same meter period as B-01 | Same | Duplicate, excluded after matching meter/period |
| C-01 | C | Unknown | Unknown | Outside the two-site demonstration; unresolved for any entity claim |

A document filename is not a uniqueness key. Compare entity, meter, period and reading identifiers; retain the excluded duplicate's provenance. Distinct meters with equal quantities are not automatically duplicates.

## Reproducible arithmetic

Use 1 MWh = 1,000 kWh and 1 tonne = 1,000 kg. Site A: 12,500 × 0.40 = 5,000 kg CO2e = 5.0 tonnes. Site B: 18 × 1,000 × 0.25 = 4,500 kg CO2e = 4.5 tonnes. The two-site illustrative total is **9.5 tonnes**. Input energy is 30,500 kWh. Multiplying the raw number 18 by 0.25 without conversion understates B by a factor of 1,000. Including B twice produces 14.0 tonnes rather than 9.5.

C is unknown, not zero; 9.5 is not a complete entity total. An undocumented zero factor for B would produce 5.0 tonnes, but no evidence justifies that substitution. Keep credits, certificates and avoided-emissions claims in a separate unresolved register rather than subtracting them from this teaching calculation.

## Counterexample: intensity improves while the total rises

Suppose an otherwise comparable earlier two-site demonstration reported 8.0 tonnes and 2,000 units of output, while this month produced 2,500 units. Earlier intensity is 8,000 / 2,000 = 4.0 kg/unit; current intensity is 9,500 / 2,500 = 3.8 kg/unit. Intensity decreased 5%, while absolute calculated emissions increased 18.75%. Neither statement alone proves overall environmental performance improved. Product mix, scope and measurement comparability remain assumptions.

## Sensitivity and stop conditions

If A's invented factor changes from 0.40 to 0.44 with activity held constant, total becomes 10.0 tonnes, a 0.5-tonne increase entirely from the assumed factor change. This is a sensitivity illustration, not an uncertainty interval or operational change.

Stop a compliance or assurance conclusion when factor authority, source rights, boundary or applicable edition is missing. Zero output makes kg/unit undefined; do not print zero intensity. A negative meter adjustment needs an evidenced correction/reversal trail; do not simply delete its sign or accept it as negative consumption. Blank input is not zero, and kg CO2 must not be combined with kg CO2e without a justified method.

## A bridge separates activity, factor and boundary changes

Use a separate fictional two-period dataset. In the prior period, Site A used 10,000 kWh at an invented factor of 0.40 kg CO2e/kWh; Site B used 15,000 kWh at 0.25. The earlier total is **4,000 + 3,750 = 7,750 kg CO2e**. In the current period, A uses 12,500 kWh and B uses 18,000 kWh, while A's factor changes to 0.44 and B's factor stays 0.25. No real emissions-factor choice is implied.

An activity-first bridge holds old factors fixed:

- A activity effect: **(12,500 − 10,000) × 0.40 = 1,000 kg**
- B activity effect: **(18,000 − 15,000) × 0.25 = 750 kg**
- A factor effect at current activity: **12,500 × (0.44 − 0.40) = 500 kg**
- Bridge: **7,750 + 1,000 + 750 + 500 = 10,000 kg**

The total increased by **2,250 kg**, of which this chosen decomposition attributes 1,750 to activity and 500 to the factor. This is a mathematical ordering convention, not a causal finding. A factor-first decomposition would assign the interaction differently while reaching the same total. State the chosen method rather than presenting the split as a unique scientific result.

Now separately add an acquired Site C with a supplied illustrative 2,000 kg calculation for the current period. The expanded-boundary total becomes **12,000 kg**. Comparing 12,000 to 7,750 without identifying the added site mixes boundary and existing-site changes. This example does not prescribe whether or how a real baseline should be recalculated; that requires applicable criteria, acquisition facts and review.

## Time overlap can hide inside distinct filenames

Suppose the file “B-April-final” contains April 1–30 and “B-April-correction” contains April 16–30 as a revised partial reading. Different filenames do not prove two additive activity populations. Determine whether the second replaces part of the first, supplies incremental missing activity, or is a duplicate. Without that evidence, summing both creates an unsupported result.

For a separate numerical illustration, a full-month original shows 18,000 kWh, including 8,000 for the second half. Supported revised second-half activity is 7,500. If the replacement relationship is established, corrected full-month activity is **18,000 − 8,000 + 7,500 = 17,500 kWh**, not 25,500. Preserve the superseded 8,000 and the revision identity. With the same invented 0.25 factor, B's corrected quantity is **4,375 kg**.

## Unit-checking without a factor database

Track quantity units through every multiplication. kWh multiplied by kg/kWh yields kg; MWh must first be aligned with a per-kWh factor. A unit conversion is exact within the stipulated units, but the suitability of the factor is a separate question. An accurately converted obsolete, wrong-geography or wrong-gas factor can still produce an inappropriate measurement.

Do not report more precision than the input quality supports. Keep unrounded values for reproducibility, then document the display rule. A missing factor cannot be resolved by rounding. A range produced by changing a teaching constant is a sensitivity range, not a statistical confidence interval.

## Educational questions and expected limits

1. What is the two-site total? 9.5 tonnes using only the fictional assumptions.
2. Does excluding C prove it is outside the real reporting boundary? No; actual boundary criteria and facts are unresolved.
3. Does a 5% intensity decrease imply lower total emissions? No; this case has an 18.75% total increase.
4. Can an Agent issue an assurance opinion from this worksheet? No; arithmetic checks are not an engagement or professional review.


## Sources and verification

The [GHG Protocol directory](https://ghgprotocol.org/standards) [ghg-standards-directory] and [GRI directory](https://www.globalreporting.org/how-to-use-the-gri-standards/gri-standards-english-language/) [gri-standards-directory] were observed on October 4, 2026 as discovery routes. Rights checks then identified restrictions; no standards bodies or factor datasets were acquired.

[GHG Protocol terms](https://ghgprotocol.org/terms-use), February 2023, section 1 and section 3, restrict extraction and public/commercial reuse. [GRI terms](https://www.globalreporting.org/media/mgspa4n4/gri-global-website-term-of-use-mpgc-05222025_25-august.pdf), August 28, 2025, physical page 4, sections 3–4, restrict automated access, derivatives and software/tool use without the specified authorization. GRI's [copyright policy](https://www.globalreporting.org/copyright/) also describes permission requirements. Acquisition stopped at those rights findings; no workaround, publisher permission or software certification is claimed.

The substantive material here is original reasoning and fictional arithmetic, not a paraphrase of a complete protected standard. Applicable editions, legal adoption, reporting criteria, real factors and source-operation rights remain unresolved. Editorial checking of this article does not resolve those gaps or constitute professional assurance.

## Standard education and Premium execution

This original article remains free Standard educational content under CC BY 4.0. Premium licenses private software workflow execution only where the feature is available and the required permissions exist. It does not sell ownership of government text, supply publisher rights, establish a correct accounting treatment, or create professional approval. No real filing, posting, model call or private workflow was executed for this lesson.


---
Original content: Open Accounting contributors · CC BY 4.0 · Version 1.0.0 · 2026-10-04. Third-party materials retain their own rights.
