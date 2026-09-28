# ASU filing discovery pilot — proposal, not activation

Parent #5; implementation #2/#8/#24; ASU references #9 and refresh #37. This adds `sec-submissions-1`, a real submissions-metadata adapter usable through the existing rights-gated intake/discovery API. It does not start a crawler or change the existing free ASU reader's evidence claims.

## Declared denominator

Two issuers: **Comtech Telecommunications Corp. (CIK 0000023197)** and **Home BancShares, Inc. (CIK 0001331520)**, selected because the ASU starter catalog already links their actual disclosures. Initial filing selection is **10-K, 10-Q, 10-K/A and 10-Q/A filed September 27, 2024 through September 27, 2026 inclusive**, with report periods retained separately. Subsequent pilot snapshots must explicitly extend their observation/filing interval; this proposal is not a perpetual complete-history claim. The accounting focus is adoption, non-adoption, transition and disclosed impact of ASUs in the reader's rolling issuance window. Other Practice issues and all non-SEC families remain in scope in the main queue.

`content/asu_pilot/0000023197.json` and `0001331520.json` are valid **reference-only registration proposals**, not fetch grants. All operation flags default false. They may be registered without sending network requests. Authorizing a real acquisition requires a new reviewed acquisition manifest/edition and valid operation-level evidence; do not flip these files into a pretend approval.

The root submissions feed may include other forms/older dates. Preserve the exact authorized root metadata artifact; apply the declared form/date selection to discovered candidates and report exclusions separately. Do not use the count of metadata rows as the count of acquired filings. A recent feed alone does not establish coverage of the selected interval.

## Official route and discovery behavior

Verified against [SEC's API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) on September 27, 2026. The documented root route is `https://data.sec.gov/submissions/CIK{10-digit-CIK}.json`. Its recent history is a columnar table; older-file descriptors provide further history. The API is metadata, not the filing body. Source accessibility does not settle every reuse operation.

The adapter validates the exact root or older-history endpoint, root-reported CIK, all required parallel-array lengths, accession shape, date precision, timestamp timezone, form, primary-document names and continuation CIKs. An accession's prefix can identify a submitting filer different from the registrant: the parser does not falsely require prefix equality. Each candidate preserves its raw row, row hash and exact JSON pointer. Returned primary filenames produce exact archive URLs; a blank primary filename stays unresolved. Amendment forms are marked, but a predecessor accession is **not guessed** from matching periods.

Linked history descriptors retain name, official URL, reported date range/count and exact JSON locator. Each must be acquired under its own approved route. History files lacking a reported CIK/name are explicitly `endpoint_only` identity; their connection to the originating root descriptor still needs reconciliation. No linked URL is automatically requested. Pagination/history overlaps, missing files, amendments and full document/exhibit inventories need reconciliation before any complete-coverage claim.

Input is bounded to 16 MB, 10,000 rows, 1,000 history descriptors, depth/node/string limits and an isolated CPU/address-space-limited process. Duplicate keys/accessions, uneven columns, foreign continuations, unknown table fields, unsafe filenames and invalid values reject the whole snapshot. The supported root-field list is explicit; upstream shape changes require review. Schema validation requires extract permission **before raw persistence**. Valid artifacts retain the existing immutable hash/receipt/notices pipeline, shared request budget and access-block handling. Discovery is idempotent per artifact, adapter and family-recipe hash. `parse` returns `DISCOVERY_ONLY`: a submissions row can never become source-text evidence through this path.

## Activation decision packet — UNSENT, NO APPROVAL

An authorized operator and rights reviewer must resolve the following for each exact work/version. This is a decision checklist and draft scope, not legal advice or a permission grant.

| Stage | Proposed operations | Current evidence/state |
|---|---|---|
| SEC submissions metadata | Exact HTTP acquisition; immutable raw storage; schema extraction; normalized metadata storage; internal review/display | No actual operation approval recorded by this slice |
| Selected issuer filing bodies | Separate exact accession/document acquisition and raw storage, parsing with note/table locators | Not acquired; issuer-authored and third-party components require screening |
| Public ASU derived identifiers | Extract/store identifiers and necessary provenance; public metadata display/redistribution, retaining notices | Not activated from real source artifacts; current reader has independent reference links only |
| Authoritative analysis and output | Parser, accounting and historical-applicability review; separately authorized model/retrieval/export operations | No approval; a mention is not adoption or GAAP authority |

Before activation, assign the operator/contact for an honest SEC User-Agent, review current access terms and exact routes, approve retention/deletion and scope, and configure source fetching only through approved secret/config channels. Follow the existing shared SEC rate budget across workers, stop on access blocks and never fall back to caches, mirrors or credentials. No bulk cost, provider call, external notification or cloud schedule is authorized by this packet. No request has been sent.

## Resumable execution

1. Register the reference proposals if useful; no acquisition is possible under their policy. Independently document the actual route/operation basis, then register the acquisition edition and obtain real revision-bound rights review.
2. Acquire the exact root feed through `/admin/intake/works/{id}/acquire`; run `/admin/intake/artifacts/{id}/discover`. Retain raw receipt/hash and discovery version/hash.
3. Enumerate all linked older histories intersecting the declared filing window, record their parent locators and independently authorized acquisition receipts, then reconcile accession duplicates and exclusions. A count reported by SEC is not a completed acquisition count.
4. Resolve primary documents and attachments using returned names and official indexes; screen third-party inserts. Acquire/parse/stage exact documents through existing intake. Do not assume that `R30.htm` exists in a new filing because it existed in an earlier one.
5. After actual source-operation approvals, the existing ASU worker can detect identifiers. Independently verify adoption classifications, exact passages, parser coverage and applicability before promoting any evidence.

Current real increment: **2 reference-only feed proposals; 0 acquired feeds, 0 real discovered rows, 0 acquired filing bodies, 0 parsed/reviewed/indexed/evaluated additions**. Adapter tests are synthetic. No external periodic discovery is activated. Next task is a rights-approved root-feed snapshot and history reconciliation; absent that gate, continue independent secure parsing and the other content-family tasks.
