"""Parser isolation entry point. Linux limits supplement, not replace, container isolation."""
import sys
import json


def main():
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
        resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024, 768 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    except (ImportError, ValueError):
        pass
    from .services.documents import parse_bytes
    data = sys.stdin.buffer.read(12 * 1024 * 1024 + 1)
    if len(data) > 12 * 1024 * 1024:
        raise ValueError('Oversized parser input')
    from .pdf_parser import PdfError
    from .docx_parser import DocxError
    from .spreadsheet_parser import SpreadsheetError
    try:
        result = parse_bytes(data, sys.argv[1], int(sys.argv[2]))
    except SpreadsheetError as exc:
        sys.stderr.write(json.dumps({'spreadsheet_error': exc.code, 'source_part': exc.part, 'locator': exc.locator}))
        raise SystemExit(2)
    except DocxError as exc:
        sys.stderr.write(json.dumps({'docx_error': exc.code, 'source_part': exc.part, 'source_xml_path': exc.path}))
        raise SystemExit(2)
    except PdfError as exc:
        sys.stderr.write(json.dumps({'pdf_error': exc.code, 'physical_page': exc.page}))
        raise SystemExit(2)
    sys.stdout.write(json.dumps(result))


if __name__ == '__main__':
    main()
