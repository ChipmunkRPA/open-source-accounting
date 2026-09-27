"""Isolated parser subprocess; raw source bytes are data, never executable instructions."""
import sys
import resource
from .sec_core import parsers
from .sec_core.core import canonical


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    if sys.platform != 'darwin':
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    raw = sys.stdin.buffer.read(parsers.MAX_BYTES + 1)
    if len(raw) > parsers.MAX_BYTES:
        raise ValueError('Oversized source')
    parser, family, title, cfr_title = sys.argv[1:]
    if parser == 'ecfr_xml':
        output = parsers.ecfr_xml(raw, title=cfr_title)
    elif parser == 'structural_html':
        output = parsers.html(raw, family, title)
    elif parser == 'pdf':
        output = parsers.pdf(raw)
    elif parser == 'text':
        from .services.documents import parse_bytes
        output = [parsers.passage(p['locator'], p['text']) for p in parse_bytes(raw, '.txt', 1_000_000)]
    else:
        raise ValueError('Unknown parser')
    sys.stdout.buffer.write(canonical(output))


if __name__ == '__main__':
    main()
