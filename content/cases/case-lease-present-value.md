# Worked case: a three-payment present-value schedule

> **AI-assisted editorial draft — not professionally reviewed.** Original educational content, not authoritative guidance. **Primary ASC text was not accessed.** Paragraph references are verification tasks, not evidence that current authoritative wording was reviewed. Confirm the framework, reporting period, elections, and source versions before use. All company names and transactions in examples are fictional.

## Hypothetical input contract
Assume payments of 10,000 at the end of each of three years, a confirmed effective annual rate of 6%, and no other cash flows. The case is a mathematical exercise after input confirmation, not a lease identification or classification opinion. [fasb-asc, Topic 842 references require verification]

## Calculation and rounding
Present value = 10,000/1.06 + 10,000/1.06² + 10,000/1.06³ = approximately 26,730.12. Carry higher precision internally and round displayed amounts to cents. At each year-end, interest equals the opening balance times 6%; the payment reduces the balance by 10,000.

| Year | Opening balance | Interest (6%) | Payment | Closing balance |
|---|---:|---:|---:|---:|
| 1 | 26,730.12 | 1,603.81 | 10,000.00 | 18,333.93 |
| 2 | 18,333.93 | 1,100.04 | 10,000.00 | 9,433.96 |
| 3 | 9,433.96 | 566.04 | 10,000.00 | 0.00 |

The table displays independently rounded high-precision figures; displayed rows can differ by a cent from calculations using only the rounded preceding row. The executable check uses high precision and tests the final residual.

## Boundary
This schedule does not establish a right-of-use asset amount, expense pattern, current/noncurrent split, rate selection, lease term, modification treatment, or financial-statement presentation. Each requires additional verified accounting inputs.

## Reviewer questions
Were the payments actually in arrears? Does the first payment occur at commencement instead? Are there incentives, options, other components, or variable amounts? Is the 6% rate approved for the entity and arrangement? These questions must be resolved before adapting the mathematical result to a real contract.

## Sources and verification

- [FASB Accounting Standards Codification](https://asc.fasb.org/) — standard; Topic and paragraph identifiers are research references. Current Codification text was not independently accessed for this starter pack.


---
Original content: Open Accounting contributors · CC BY 4.0 · Draft 2026-09-27. Third-party sources retain their own rights.
