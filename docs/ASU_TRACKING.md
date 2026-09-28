# ASU tracking

The free `/asu-tracking` module connects a rolling **two-calendar-year issuance window** to selected public-company SEC disclosures. It supports ASU/subject/topic search, company/CIK and disclosure-status filters, filing pagination, official links, date precision, artifact provenance when available, and refresh freshness. It does not require a subscription or sign-in.

Parent #5; source work #9/#2, ingestion #8/#24 and periodic monitoring #37. This module does not complete those issues or replace the all-family queue.

## Current scope

`backend/app/asu_data/catalog.json`, release `asu-reference-2026-09-27.1`, contains **16 ASU references** (2024-03/04, 2025-01 through 12, 2026-01/02) and **12 ASU-to-filing reference links across two companies/two filings**. Nine ASUs have at least one starter link; seven have none. Metadata was checked against official FASB publications and SEC filings. This selected catalog is **not a verified complete issuance or filer universe**. The public FASB index was not extractable with the text reader. We did not replace it with a mirror, copy FASB standards, or claim a license.

Short subjects and filing observations are original metadata descriptions. ASU issuance is separate from company adoption, filing date, report period, acquisition time, and entity-specific effective dates. Unknown exact dates remain year/month precision or null. Home BancShares' filing date remains unverified; its report period is June 30, 2026. No day is invented from a report period or URL. The inclusive window uses UTC today minus two calendar years, February 29 clamped to February 28. An uncertain interval intersecting the boundary is shown with a warning.

All starter links are reference-only: **0 retained originals, 0 parsed filing artifacts, 0 independent technical/applicability approvals, 0 Agent admissions, 0 professionally adjudicated evaluations**. Opening a link does not change those counts. The metadata catalog itself is source-controlled application data, not an artifact hash for a downloaded filing.

Official provenance includes:

- [FASB expense disaggregation project](https://fasb.org/page/PageContent?pageId=%2Fprojects%2Frecently-completed-projects%2Fdisaggregation-income-statement-expenses.html), [2024-04 cover](https://storage.fasb.org/ASU%202024-04.pdf).
- [FASB 2026 taxonomy release notes](https://xbrl.fasb.org/resources/annualrelease/2026/GAAP_Financial_Reporting_Taxonomy_Release_Notes.pdf), [fourth-quarter 2025 chair report](https://storage.fasb.org/4Q%202025%20Chair%20Report.pdf). Exact project/announcement URLs for day-precision records are in the catalog.
- [Comtech filing index](https://www.sec.gov/Archives/edgar/data/23197/000002319726000069/0000023197-26-000069-index.html) and [accounting-updates note](https://www.sec.gov/Archives/edgar/data/23197/000002319726000069/R8.htm): eight references to standards not yet adopted.
- [Home BancShares cover](https://www.sec.gov/Archives/edgar/data/1331520/000133152026000112/R1.htm) and [recent-pronouncements note](https://www.sec.gov/Archives/edgar/data/1331520/000133152026000112/R30.htm): four references, including reported early adoption of 2025-08 effective April 1, 2026. This describes that company's disclosure, not professional approval or general applicability.

## Periodic updates

The existing worker now performs a resumable daily sweep of **authorized staged SEC filing passages**. This is an internal corpus refresh, not a newly activated external crawler. No network request, model call, paid resource, email, SMS, or notification occurs during this sweep.

After migrations, run the normal worker (`python -m app.worker`). `python -m app.worker --once` drains the current sweep in bounded batches as well as available jobs, then exits. A deployed scheduler may invoke this command; no cloud schedule was provisioned by this change. Stopping the worker stops automatic refresh; the UI shows never-run/last-completed/overdue status. Administrators can advance one bounded batch with the UI button or `POST /api/v1/admin/asu-tracking/refresh`; repeat if the response is running. Forced refresh resumes an unfinished sweep.

Each atomic transaction visits at most 200 source rows. A persistent cursor/fixed upper bound avoids the legacy 2,000-row truncation. New records behind the cursor enter the next daily sweep. PostgreSQL row locking and SQLite conflict-insert serialization protect the singleton sweep. Crashes roll back both cursor and mention writes; retry resumes the last committed batch. Matches are unique by source/ASU, so reprocessing is idempotent. Paging streams database rows and retains only the requested page, in stable reference-first/source-ID order; totals are computed after live authorization.

Only actual staged passages with consistent intake parent/artifact/extraction/hash bindings, `SEC_FILINGS` family, public-candidate access mode, exact official EDGAR document URLs and current extract/store-text/public-display/redistribution permissions qualify. Private documents and other content families never enter this register. Parent revocation, integrity holds, scope restrictions, changed text or missing artifacts immediately withhold derived matches on reads; source deletion cascades identifiers. The system stores detected ASU identifiers, not duplicate filing bodies or snippets.

`asu-mentions-1` detects explicitly labeled ASU identifiers, including typographic dashes. It **always labels automatic results “mentioned”**. Negation, future adoption, permitted early adoption and multiple ASUs make heuristic adoption inference unreliable. Starter “early adopted”/“not yet adopted” observations remain visibly unreviewed reference metadata. No automatic result is admitted to Agent evidence.

## Adding current material

1. Reconcile new ASU identities, issuance precision and official metadata references in the versioned catalog; validate it and publish a normal main commit. This catalog does not automatically crawl FASB. Rights to FASB prose remain separate.
2. Register SEC filings through the existing intake API with exact accession/document URLs, declared dates, notices and operation-specific authorization. Follow #2 discovery and #8 acquisition instructions. Obtain authorized originals, preserve immutable raw/normalized hashes, parse and stage; no reference link becomes acquired text automatically.
3. Obtain actual source-operation approvals for the relevant public use. Independent parser, accounting and applicability reviews remain separate; do not manufacture them to make a tracker row appear.
4. Run the worker or advance the admin refresh. Confirm the public material's exact locator, raw hash, parser version and current permissions. Missing company/form/date metadata remains explicitly unverified.

The pending live-feed work is official filing discovery/acquisition for a defined company cohort, actual operation authorizations and full artifacts, reconciliation of new FASB issuance metadata, independent reviews and adjudicated adoption classifications. Until then this is a functional reference module with a tested corpus-update path, **not comprehensive live monitoring**.
