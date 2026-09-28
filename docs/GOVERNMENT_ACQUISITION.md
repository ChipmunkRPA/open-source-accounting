# Government source acquisition packet — issues #7/#8/#15/#23

This packet prepares eight work candidates across **GAO and FASAB**, observed on 2026-09-27. It adds no runtime grants, preserved original HTTP documents, parser approvals, technical approvals, index entries or adjudicated benchmarks. See [candidate metadata](../reports/intake/government-candidates.json) and [12 original draft review scenarios](../reports/intake/government-review-cases.json). The scenarios are review prompts, not executed tests or approved accounting answers.

## Findings that change the retrieval plan

The [2024 Yellow Book product](https://www.gao.gov/products/gao-24-106786) and [current landing page](https://www.gao.gov/yellowbook) need distinct provenance. The landing page contains a federal audit organization deferral absent from the original implementation notice. Financial engagements use period-start triggers; performance audits use audit-start triggers. Keep both the publication and dated implementation notice, with separate rights and applicability review. Preserve GAO-21-368G for the historical route; that historical artifact is not included in this eight-work batch.

The [2025 Green Book](https://www.gao.gov/products/gao-25-107721) uses a fiscal-year trigger. Nonfederal adoption and linked COSO material need their own treatment. The [quality-management FAQ](https://www.gao.gov/products/gao-26-108710) is interpretive guidance, not a new Yellow Book edition. Its normal and accessible PDFs have different page counts, so they cannot share page locators without verified mapping.

The [FASAB landing page](https://fasab.gov/accounting-standards/) links a complete handbook whose filename says 2025, while [TR 24](https://files.fasab.gov/pdffiles/handbook_tr_24.pdf) displays a Version 25 (9/26) header. Preserve this discrepancy until actual covers and contents can be reconciled. The landing page lists TB 2025-1, SIG 64.1 and TR 24 outside the complete handbook and separately marks SFFAS 65 pending. Do not use file year, download date or chapter header as a universal effective date. The chapter index redirects to `https://fasab.gov/accounting-standards/document-by-chapter/`.

The complete-handbook PDF failed in web retrieval with `Internal Error`. A read-only request to the official landing page recovered its exact href. This is an observed tool failure, not proof the publisher blocks access. No mirror was used, and no HTTP-body hash or successful acquisition is claimed.

## Concrete review scope before acquisition

The [GAO reuse policy](https://www.gao.gov/copyright) supports entire-publication copying/distribution in the United States, with attribution, no misleading endorsement, and separate treatment of third-party components and recognizable people. TB 2025-1 and SIG 64.1 also have whole-work notices on PDF page 2. These observations support a narrow rights proposal; they do not activate every operation or prove all components are open.

The requested first decision is work-specific **acquire and store_raw** for complete official publications in an internal US review collection. Assign an actual rights approver, exact edition and notice evidence, retention/location scope and route before recording a runtime grant. Then separately decide **extract and store_text** after component screening. Keep **embed, model_input, display_full, quote, export, redistribute and train** disabled unless individually authorized. No publisher request has been sent and no approval owner has accepted this packet.

For each approved work, use the existing authenticated intake registration → independent rights approval → acquisition path in [SOURCE_INTAKE.md](SOURCE_INTAKE.md). Record original bytes/hash, final URL, response metadata, retrieval time, edition and all available date fields. A web-tool PDF text view is not this receipt. Inspect the PDF for third-party credits; keep whole-work and component permissions distinct. Do not import the planning JSON as a runtime grant or use synthetic reviewers to unblock it.

For parsing, compare PDF page positions with printed page/paragraph identifiers, headings, notes and tables. Preserve both coordinates. Validate numeric/table extraction and omitted-page counts before proposing parser approval. No OCR is authorized by a discovery failure; use it only after a measured extraction failure and scoped review. Technical and historical/entity applicability decisions remain separate from parsing and rights.

## Remaining government scope and handoff

| Scope | Next concrete action | Current blocker / owner |
|---|---|---|
| Three GAO candidates | Approve exact whole-work acquisition scope; retain current implementation notice separately; retrieve approved originals | Independent rights approver unassigned; no runtime grant |
| Five FASAB candidates | Resolve handbook failure/edition; inspect notices per work; keep pending SFFAS 65 informational | Independent rights approver unassigned; handbook original unverified |
| GAO historical editions | Resolve original GAO-21-368G and GAO-14-704G artifacts and dated scope | Outside current batch; independent discovery can proceed |
| FASAB full categories | Expand chapter inventory across concepts, standards, interpretations, bulletins, releases and staff guidance with amendment edges | Eight-work packet is not full handbook/component coverage |
| OMB/Treasury | Discover current A-123/A-136, annual Compliance Supplements and Treasury instructions from official navigation | No edition inventory in this packet; independent discovery can proceed |
| Human evaluation | Reviewer adjudicates all 12 scenarios against approved primary text and exact current notice revisions | Specialist owner unassigned; zero gold cases |

This packet touches **2 of 32** agreed families. OMB/Treasury remains part of #15, and the other source issues remain in the dependency queue. The existing [all-family rights matrix](rights/family-rights-status.json) remains unchanged. Production source/model availability, GCP project/region/spend approval and all launch gates remain unresolved.
