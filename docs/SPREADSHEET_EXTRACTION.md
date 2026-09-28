# Spreadsheet extraction — literal values, not recalculation

Issue #24 under #5; private upload/security and Agent context #29/#31. `spreadsheet-cells-1` adds `.xlsx` and UTF-8 comma-separated `.csv` to the existing authorized private-document upload path. It uses the same workspace/subscription controls, malware scanner, size limits, isolated process and storage/deletion path. Private uploads do not become public content.

## Preserved data

CSV preserves every field as a string, including leading zeros, signs, parentheses, empty fields, quoted commas and embedded newlines. It records logical row/cell/range locators and the physical line interval. It does not infer a header, numbers, units or dates, guess a locale/delimiter, or execute formula-like strings. Comma-separated UTF-8 is the explicit supported contract; uneven rows and malformed quoting fail.

XLSX preserves worksheet order/names/state, stored row/cell coordinates (including gaps), hidden row/column metadata and declared merged ranges. Values retain their raw type and exact scalar spelling; shared/inline strings are resolved without executing anything. Formulas retain their text and attributes separately from cached values. Missing numeric caches, blank string caches and non-formula cells are distinct. Shared/array formula attributes remain literal; shared formulas are not translated into fabricated per-cell expressions. Errors such as `#DIV/0!` stay errors.

Number-format IDs/custom codes and cell style attributes remain metadata, not a rendered-display claim. Workbook date system (1900/1904), ISO date cells, defined names, calculation properties and sheet header/footer text are retained. Excel serial dates are **not converted**, including serial 60: no fake date or locale-dependent display is invented. Units may appear in source cells/headers/footers; the parser does not verify or infer them. Cached values may be stale even when present. [Microsoft's cell-value documentation](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.cellvalue) distinguishes stored values and cached formula results; [Microsoft's date-system documentation](https://support.microsoft.com/en-gb/excel/date-systems-in-excel) explains why the workbook's system matters.

Each row chunk has an exact quoted sheet/cell-range locator, source part, parser version, preserved cell objects, a normalized text hash and character ranges if a long row is split. A range does not imply that absent cells were stored. Empty worksheets have explicit markers with **zero cells**, never invented A1 data. Workbook declarations and headers/footers have separate non-cell locators. Existing raw-file checksums remain on the private document. Agent preprocessing explicitly supplies the extraction limitations; no rendered accuracy, formula correctness, unit interpretation or professional approval is granted.

## Limits and blocked structures

Input remains bounded by upload and isolated-worker limits. XLSX additionally limits expanded ZIP size to 40 MiB, 2,000 members, 50,000 stored cells, 100 sheets, XML depth/node count, compression ratio and total extracted text. The worker has CPU/address-space/time/output limits; parser output is never silently truncated to make it fit. Duplicate ZIP members, unsafe paths, encryption, invalid package/workbook bindings, malformed XML/DTD/entities, invalid cell ordering/types/styles, bad shared-string indexes and inconsistent dates fail. CSV has row/column/field/character limits and rejects binary/non-UTF-8 input.

No macro, binary embedding, external relationship, data connection, query table or macro sheet is executed. Such package features are rejected. Formulas themselves remain untrusted source strings: this is not a formula engine or sanitized workbook generator. Downloaded originals remain the original user-supplied bytes.

Charts/drawings, comments, extension content, structured Excel tables/pivots, unsupported phonetic text and orphan worksheet parts currently block the whole upload with `SPREADSHEET_PARSE_BLOCKED` and a scoped reason/part/locator. They need additional extraction adapters, not a fake review approval. Standard style/print/layout interpretation, conditional formatting, inherited visual formats and number rendering remain unverified. A supported literal-cell extraction is not certification of workbook completeness, accounting correctness or visual layout.

## Scope still open

This version serves **private uploads only**. Public source acquisition/manifest MIME support and source-extraction staging for XLSX/CSV are not enabled by this change. They require a separate immutable intake integration and actual operation permissions. No source artifacts or licensed spreadsheet corpus were acquired, and no professional approval was created. Raw/normalized acquisition, visual table checks, source rights, technical/applicability review and Agent evidence admission remain separate gates.

Next implementation: reuse this parser through the public-source intake contract with exact sheet/cell metadata and versioned hashes, then add explicit support for structured tables/comments and measured rendering reconciliation. Do not discard unsupported parts or substitute CSV exports as if they preserved workbook formulas/styles.

## Authorized source intake

The shared source pipeline now supports `xlsx` and `csv` manifests with exactly their registered MIME (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` or `text/csv`) and at most 12,000,000 input bytes. Other parsers cannot declare these MIME types. Existing manifest serialization and parser identities are unchanged.

`source-intake-1/spreadsheet-cells-1` runs in the bounded intake subprocess. Every normalized row/declaration retains the spreadsheet metadata, exact sheet/cell locator, text hash and unreviewed status. Immutable raw/normalized objects and artifact receipts use the existing source-operation authorization. Staging and explicit recovery revisions copy metadata into `intake_spreadsheet`; no private upload is published. The independent review packet includes the original bytes, complete normalized metadata and a spreadsheet-specific checklist. Formula caches, display formatting, units and professional conclusions remain unverified.

Unsupported/unsafe spreadsheet content returns `SPREADSHEET_PARSE_BLOCKED`, retaining the original without staging partial content. Existing parser limits, one-million-character extraction limit, 10,000-passage intake ceiling, subprocess CPU/memory/time limits and output-byte ceiling apply. No macros/formulas/external links execute. This enables authorized source-family ingestion; it does not acquire a real workbook or grant rights, parser, technical or applicability approval.

Reviewed-source retrieval preserves spreadsheet cell/range locators with paragraph/character subranges and explicit date-system/calculation/rendering limits. This does not bypass existing model-input and independent review checks.
