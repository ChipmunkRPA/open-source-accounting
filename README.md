# Open Source Accounting — free client and educational content

This public repository contains the free web client, original educational library, and source-reference inventories. Proprietary hosted Agent workflows, backend, prompts, review tools, deployment configuration, and premium UI are maintained in a separate private repository. Free chat and live source readers use the hosted API; they are not offline model services.

## Local preview

Use Node 22 and Python 3.11 or newer:

```sh
npm --prefix frontend ci --ignore-scripts
npm --prefix frontend run typecheck
npm --prefix frontend run test:auth
npm --prefix frontend run build
python3 scripts/check_public.py --dist
python3 scripts/serve_public.py
```

Open http://127.0.0.1:8080/assets/library/index.html for the hash-verified original library. The application root explains that hosted APIs are unavailable locally. No simulated chat, signed-in account, source acquisition or professional approval is supplied. In hosted operation `/api` must be routed to the separately operated service, which enforces verified email, MFA, permissions and source rights.

## Scope and rights

General AI chat and public educational/source-reading content remain free. Hosted Agent operations are US$89.99/year; no monthly plan or usage allowance is promised here. ASU tracking and SEC comment-letter reading interfaces remain public, but their live feeds require the hosted service. Current inventories are drafts and selected references, not complete acquired or professionally approved corpora. See `content/manifest.json` and `progress.md`.

Public code remains MIT. Original educational material uses its stated content license; third-party sources retain their own rights. The private migration does not revoke licenses on code already published in public Git history. Do not place proprietary implementation, private prompts, credentials, client documents or licensed corpora here.

## Free accounting systems directory

The Standard client includes 33 researched system profiles across 13 finance workflows: AP, procurement, expenses, AR, billing/revenue, close, consolidation, FP&A, treasury, tax, audit/controls/reporting, data integration and core accounting/ERP. Build the frontend and open `/assets/systems/index.html`. It works without an API or sign-in and links from the free library and app navigation. Profiles contain original introductions, editorial company-size fit, integration questions, current official sources and logo provenance.

Two official media-kit logos are included; 31 profiles use text while brand-asset conditions remain unresolved. Vendor names and marks are excluded from MIT and CC BY. See [directory documentation](content/systems/README.md) and [third-party notices](content/systems/NOTICE.md). No working integration or vendor endorsement is implied.
