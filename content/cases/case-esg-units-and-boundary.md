# Worked case: units, duplicate meters and an intensity claim

> **AI-assisted editorial draft — not professionally reviewed.** Original educational material. No standard text or real emissions factors are reproduced. No compliance, materiality, assurance or accounting conclusion is established.

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

## Educational questions and expected limits

1. What is the two-site total? 9.5 tonnes using only the fictional assumptions.
2. Does excluding C prove it is outside the real reporting boundary? No; actual boundary criteria and facts are unresolved.
3. Does a 5% intensity decrease imply lower total emissions? No; this case has an 18.75% total increase.
4. Can an Agent issue an assurance opinion from this worksheet? No; arithmetic checks are not an engagement or professional review.


## Sources and verification

[GHG Protocol standards directory](https://ghgprotocol.org/standards) and [GRI English standards directory](https://www.globalreporting.org/how-to-use-the-gri-standards/gri-standards-english-language/) are discovery references only. Directory pages were observed on 2026-09-29; standard bodies were not acquired or checked. Exact applicable editions, amendments, local adoption and operation permissions remain unresolved. These links do not support the fictional numerical inputs or establish compliance.

---
Original content: Open Accounting contributors · CC BY 4.0 · Version 0.6.6 · 2026-09-29. Third-party materials retain their own rights.
