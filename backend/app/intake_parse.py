"""Isolated parser subprocess; raw source bytes are data, never executable instructions."""
import sys
import resource
import json
from .sec_core import parsers
from .sec_core.core import canonical


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    if sys.platform != 'darwin':
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    raw = sys.stdin.buffer.read(parsers.MAX_BYTES + 1)
    if len(raw) > parsers.MAX_BYTES:
        raise ValueError('Oversized source')
    parser, family, title, cfr_title = sys.argv[1:5]
    if parser == 'annual_cfr_xml':
        from .annual_cfr import parse, AnnualCfrError
        try:
            output = parse(raw, cfr_title, json.loads(sys.argv[5]))
        except AnnualCfrError as exc:
            sys.stderr.write(json.dumps({'annual_cfr_error': exc.code, 'source_xml_path': exc.path}))
            raise SystemExit(2)
    elif parser == 'ecfr_xml':
        from .ecfr_parser import parse, EcfrError
        try:
            output = parse(raw, cfr_title)
        except EcfrError as exc:
            sys.stderr.write(json.dumps({'ecfr_error': exc.code, 'source_xml_path': exc.path}))
            raise SystemExit(2)
    elif parser == 'structural_html':
        output = parsers.html(raw, family, title)
    elif parser == 'pdf':
        from .pdf_parser import parse, PdfError
        try:
            output = []
            for item in parse(raw):
                p = parsers.passage(f'PDF page {item["pdf"]["physical_page"]}', item['text'], 'pdf_page_unreviewed_layout')
                p['pdf'] = item['pdf']
                output.append(p)
        except PdfError as exc:
            sys.stderr.write(json.dumps({'pdf_error': exc.code, 'physical_page': exc.page}))
            raise SystemExit(2)
    elif parser in {'xlsx', 'csv'}:
        from .spreadsheet_parser import parse_xlsx, parse_csv, SpreadsheetError
        try:
            if len(raw) > 12_000_000:
                raise SpreadsheetError('input_byte_limit')
            rows = (parse_xlsx if parser == 'xlsx' else parse_csv)(raw, 1_000_000)
            output = []
            for item in rows:
                p = parsers.passage(item['locator'], item['text'], 'spreadsheet_cells_unreviewed')
                p['spreadsheet'] = item['spreadsheet']
                output.append(p)
        except SpreadsheetError as exc:
            sys.stderr.write(json.dumps({'spreadsheet_error': exc.code, 'source_part': exc.part, 'locator': exc.locator}))
            raise SystemExit(2)
    elif parser == 'text':
        from .services.documents import parse_bytes
        output = [parsers.passage(p['locator'], p['text']) for p in parse_bytes(raw, '.txt', 1_000_000)]
    else:
        raise ValueError('Unknown parser')
    sys.stdout.buffer.write(canonical(output))


if __name__ == '__main__':
    main()
