# Spreadsheet extraction — literal values, not recalculation

Issue #24 under #5; private upload/security and Agent context #29/#31. `spreadsheet-cells-2` supports `.xlsx` and UTF-8 comma-separated `.csv` to the existing authorized private-document upload path. It uses the same workspace/subscription controls, malware scanner, size limits, isolated process and storage/deletion path. Private uploads do not become public content.

## Preserved data

CSV preserves every field as a string, including leading zeros, signs, parentheses, empty fields, quoted commas and embedded newlines. It records logical row/cell/range locators and the physical line interval. It does not infer a header, numbers, units or dates, guess a locale/delimiter, or execute formula-like strings. Comma-separated UTF-8 is the explicit supported contract; uneven rows and malformed quoting fail.

XLSX preserves worksheet order/names/state, stored row/cell coordinates (including gaps), hidden row/column metadata and declared merged ranges. Values retain their raw type and exact scalar spelling; shared/inline strings are resolved without executing anything. Formulas retain their text and attributes separately from cached values. Missing numeric caches, blank string caches and non-formula cells are distinct. Shared/array formula attributes remain literal; shared formulas are not translated into fabricated per-cell expressions. Errors such as `#DIV/0!` stay errors.

Number-format IDs/custom codes and cell style attributes remain metadata, not a rendered-display claim. Workbook date system (1900/1904), ISO date cells, defined names, calculation properties and sheet header/footer text are retained. Excel serial dates are **not converted**, including serial 60: no fake date or locale-dependent display is invented. Units may appear in source cells/headers/footers; the parser does not verify or infer them. Cached values may be stale even when present. [Microsoft's cell-value documentation](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.cellvalue) distinguishes stored values and cached formula results; [Microsoft's date-system documentation](https://support.microsoft.com/en-gb/excel/date-systems-in-excel) explains why the workbook's system matters.

Each row chunk has an exact quoted sheet/cell-range locator, source part, parser version, preserved cell objects, a normalized text hash and character ranges if a long row is split. A range does not imply that absent cells were stored. Empty worksheets have explicit markers with **zero cells**, never invented A1 data. Workbook declarations and headers/footers have separate non-cell locators. Existing raw-file checksums remain on the private document. Agent preprocessing explicitly supplies the extraction limitations; no rendered accuracy, formula correctness, unit interpretation or professional approval is granted.

## Limits and blocked structures

Input remains bounded by upload and isolated-worker limits. XLSX additionally limits expanded ZIP size to 40 MiB, 2,000 members, 50,000 stored cells, 100 sheets, XML depth/node count, compression ratio and total extracted text. The worker has CPU/address-space/time/output limits; parser output is never silently truncated to make it fit. Duplicate ZIP members, unsafe paths, encryption, invalid package/workbook bindings, malformed XML/DTD/entities, invalid cell ordering/types/styles, bad shared-string indexes and inconsistent dates fail. CSV has row/column/field/character limits and rejects binary/non-UTF-8 input.

No macro, binary embedding, external relationship, data connection, query table or macro sheet is executed. Such package features are rejected. Formulas themselves remain untrusted source strings: this is not a formula engine or sanitized workbook generator. Downloaded originals remain the original user-supplied bytes.

Charts/drawings, comments, extension content, pivot tables, unsupported phonetic text and orphan worksheet parts currently block the whole upload with `SPREADSHEET_PARSE_BLOCKED` and a scoped reason/part/locator. They need additional extraction adapters, not a fake review approval. Standard style/print/layout interpretation, conditional formatting, inherited visual formats and number rendering remain unverified. A supported literal-cell extraction is not certification of workbook completeness, accounting correctness or visual layout.

## Scope still open

Both private uploads and explicitly authorized source intake use this parser. No real spreadsheet artifacts were acquired and no professional approval was created. Visual checks, source rights, technical/applicability review and Agent evidence admission remain separate gates. Comments and measured rendering reconciliation remain open; unsupported parts are not silently discarded.

## Structured tables

Version 2 retains table definitions as separate normalized passages with table-part and sheet/range locators. Column labels, header/totals row declarations, totals labels/functions, calculated-column and totals formulas, styles, filters and sort declarations remain literal metadata. Row chunks link to overlapping table row ranges. Stored cell values remain separate, even if they disagree with declared column headers. Filters are not applied, formula declarations are not expanded into invented cells, and missing totals are not calculated.

The adapter validates table relationship bindings, unique workbook identities, nonoverlapping ranges, column width/count/identities, header/totals counts, filter-column bounds and filter ranges. Duplicate, missing or orphan bindings, external/query tables, XML mappings and unsupported extensions fail the whole extraction. Up to 100 table parts are supported within the existing XML/ZIP/text budgets. An absent stored cell inside a table range stays absent.

The implementation follows [Microsoft's SpreadsheetML table model](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/working-with-tables) and [table-column declarations](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.tablecolumn). Existing version-1 extractions remain immutable; a new parse receives the version-2 identity and requires its own review.

## Authorized source intake

The shared source pipeline now supports `xlsx` and `csv` manifests with exactly their registered MIME (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` or `text/csv`) and at most 12,000,000 input bytes. Other parsers cannot declare these MIME types. Existing manifest serialization is unchanged; the parser version changes explicitly when new bytes are normalized.

`source-intake-1/spreadsheet-cells-2` runs in the bounded intake subprocess. Every normalized row/declaration retains the spreadsheet metadata, exact sheet/cell locator, text hash and unreviewed status. Immutable raw/normalized objects and artifact receipts use the existing source-operation authorization. Staging and explicit recovery revisions copy metadata into `intake_spreadsheet`; no private upload is published. The independent review packet includes the original bytes, complete normalized metadata and a spreadsheet-specific checklist. Formula caches, display formatting, units and professional conclusions remain unverified.

Unsupported/unsafe spreadsheet content returns `SPREADSHEET_PARSE_BLOCKED`, retaining the original without staging partial content. Existing parser limits, one-million-character extraction limit, 10,000-passage intake ceiling, subprocess CPU/memory/time limits and output-byte ceiling apply. No macros/formulas/external links execute. This enables authorized source-family ingestion; it does not acquire a real workbook or grant rights, parser, technical or applicability approval.

Reviewed-source retrieval preserves spreadsheet cell/range locators with paragraph/character subranges and explicit date-system/calculation/rendering limits. This does not bypass existing model-input and independent review checks.
