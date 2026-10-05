# Open Source Accounting — free client and educational content

This public repository contains the free web client, original educational library, and source-reference inventories. Proprietary hosted Agent workflows, backend, prompts, review tools, deployment configuration, and premium UI are maintained in a separate private repository. Free chat and live source readers use the hosted API; they are not offline model services.

## Local preview

Use Node 22 and Python 3.11 or newer:

```sh
npm --prefix frontend ci --ignore-scripts
npm --prefix frontend run typecheck
npm --prefix frontend run test:auth
npm --prefix frontend run build
npm --prefix frontend run test:content
python3 scripts/check_public.py --dist
python3 scripts/serve_public.py
```

Open http://127.0.0.1:8080/assets/library/index.html for the hash-verified reader editions. The application root explains that hosted APIs are unavailable locally. No simulated chat, signed-in account, source acquisition or professional approval is supplied. In hosted operation `/api` must be routed to the separately operated service, which enforces verified email, MFA, permissions and source rights.

For reading and Markdown downloads on GitHub, use the [current 124-item reader index](content/README.md). Historical canonical article and review records remain preserved separately from the active reader links.

## Scope and rights

General AI chat and public educational/source-reading content remain free. Hosted Agent operations are US$89.99/year; no monthly plan or usage allowance is promised here. ASU tracking and SEC comment-letter reading interfaces remain public, but their live feeds require the hosted service. The inventories distinguish original articles, selected references and bounded acquired government-source snapshots; they are not a complete or professionally approved accounting corpus. See `content/manifest.json` and `progress.md`.

Public code remains MIT. Original educational material uses its stated content license; third-party sources retain their own rights. The private migration does not revoke licenses on code already published in public Git history. Do not place proprietary implementation, private prompts, credentials, client documents or licensed corpora here.

## Free accounting systems directory

The Standard client includes 33 researched system profiles across 13 finance workflows: AP, procurement, expenses, AR, billing/revenue, close, consolidation, FP&A, treasury, tax, audit/controls/reporting, data integration and core accounting/ERP. Build the frontend and open `/assets/systems/index.html`. It works without an API or sign-in and links from the free library and app navigation. Profiles contain original introductions, editorial company-size fit, integration questions, current official sources and logo provenance.

Three official media-kit logos are included; 30 profiles use text while brand-asset conditions remain unresolved. Vendor names and marks are excluded from MIT and CC BY. See [directory documentation](content/systems/README.md) and [third-party notices](content/systems/NOTICE.md). No working integration or vendor endorsement is implied.

## Downloadable federal regulatory corpus

The [2026-10-04 GovInfo eCFR snapshot](corpus/govinfo/ecfr/2026-10-04/README.md)
contains 31,604 dated regulatory section records from Titles 12, 17, 26, 31 and 48,
representing 31,603 distinct normalized texts. Five compressed shards and a local
search loader are included. These come from five source XML containers, not 31,604
independent publications or original articles. Ten notice/ownership-review sections
and 2,215 metadata-only entries are excluded from the public shards.

Each record retains its source, exact hashes, per-volume amendment date and rendering
limits. The dataset does not claim current-law completeness, an official certified
edition, professional review or Agent admission. It is available for local research;
publishing this repository snapshot does not deploy the hosted library.

## Important U.S. federal tax cases

The [tax case-law catalog](content/tax-case-law/README.md) adds 32 original educational decision briefs and official opinion links across 14 topics. It includes dated reversal, jurisdiction and 2026 procedural-history warnings. Raw judicial PDFs are retained separately, not included in this catalog. No complete-citator, current-law or professional-review claim is made.

## Core standards research maps

The [core standards directory](content/core-standards/README.md) provides five original
research outlines with 20 manually curated tracks across FASB, GASB, AICPA, ESG and
IRS literature. These are research questions and work-product designs, not acquired
standards or a publisher index. No publisher standard bodies, automated collection,
source-operation grants or professional approvals are included.

## State and local tax source coverage

The [SALT research catalog](content/salt/2026-10-04/README.md) adds a dated 51-jurisdiction coverage matrix, representative state/city sources and explicit acquisition gaps. It publishes metadata only, with IRS referrals, pages, whole PDFs and candidate links counted separately; no current-rate or exhaustive-coverage claim is made.

## Ray Sang Annotation and prospective content terms

Our original descriptions, standards/law/case interpretations and examples are
branded **Ray Sang Annotation**. This is a presentation label, not a claim of
personal authorship or professional review. Publisher/government text and original
creator credits remain distinct. `content/annotation-policy.json` records the
original-library revision bindings without altering retained article bytes.

[CONTENT-TERMS.md](CONTENT-TERMS.md) applies the custom noncommercial/no-unapproved-AI
license only to explicitly marked NEW first-party material within our rights.
All prior MIT, CC BY, third-party, public-domain, statutory and platform grants
remain intact. Existing Standard content is not retrospectively restricted. These
custom terms are not an OSI-open-source license. The Standard repository remains
public. `robots.txt` is advisory and does not control GitHub's domain robots,
cloning, APIs or existing forks; it cannot block access or override agreements.

New copyright-detection fiction is private-Premium source only, even when displayed
on the Standard-access website. It is visibly labeled per item, belongs in the same
standards category/list, is not secret after display, and never counts as authoritative
coverage or enters authoritative retrieval, Agent citations or conclusions.
