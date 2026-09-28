# DOCX body-order extraction (#24)

Private uploads use `docx-body-order-2`. The adapter walks the main document body in XML order, preserving interleaved paragraphs and table rows rather than collecting all paragraphs first. Existing stored documents are not rewritten. No new public-source DOCX ingestion route or operation rights are granted by this change.

Each block records `word/document.xml`, an indexed namespace-qualified XML path, a normalized block hash, parser version and review limits. Table rows retain cell values (including empty cells and signs), row-header declarations, individual cell/paragraph paths and boundaries. Chunk character ranges are zero-based and end-exclusive within extracted block text, not raw bytes or rendered pages. Table text escapes literal pipes and internal paragraph newlines; structured cell values retain their original extracted strings. Local `Paragraph N` / `Table N, row M` locators are not legal clause identifiers.

Visible hyperlink text, relationship targets and anchors are retained as untrusted data. Targets are never fetched. Declared paragraph numbering properties are retained but automatic numbers and style inheritance are not resolved; no clause number is invented. Layout, rendered pages and complete-document meaning are unreviewed. Agent preprocessing carries these limits, with unknown order/revision coverage for old documents lacking version metadata.

## Explicit unresolved cases

The entire upload fails with `DOCX_PARSE_BLOCKED`, a reason, package part and XML path when it contains supported detections of tracked revisions, comments requiring review, hidden text, fields, drawings/embedded objects, external templates, unsupported body/content-control structures, nested tables or merged cells. A merge is reported specifically rather than silently flattening it. Text-bearing headers, footers, footnotes and endnotes also require explicit review instead of being silently dropped. The adapter does not accept or reject Word revisions on behalf of the user, choose a legal version, remove comments or evaluate field instructions.

Unknown/unresolved content requires a reviewed source version or a future supported adapter. Do not delete legally relevant material merely to make the upload pass. Comments and supplemental stories remain an outstanding implementation scope, not completed content coverage. Blank cells are preserved; an entirely empty table does not count delimiter characters as source text.

## Package and execution limits

Parsing runs inside the existing private worker after upload authorization, size/signature checks and configured malware scanning. It reads at most 12 MiB input, 2,000 ZIP members and 40 MiB declared expansion, rejects excessive compression, encrypted/duplicate/unsafe members, DTD/entities and unsupported XML encodings, and bounds XML depth/elements and extracted characters. Internal relationships must resolve to retained package members and the main relationship must select the supported main part. Active external relationships and embedded executable content are rejected. This complements isolation/scanning, not a complete malware proof.

No document record or stored upload is created on parser failure. Successful uploads retain their original raw checksum and metadata under existing workspace controls. The original file remains necessary for independent review. Tests are entirely original synthetic packages; no publisher permission, human review or professional approval is inferred. Actual commands/results: `reports/intake/DOCX_EXTRACTION.md`.

Next multiformat work: bounded XLSX/CSV ingestion with worksheet/cell locators, formula-versus-cache distinctions and external-link/macro controls, alongside the remaining DOCX supplemental-story/revision review workflow.
