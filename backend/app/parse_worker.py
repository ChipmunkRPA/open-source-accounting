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
    data = sys.stdin.buffer.read(12 * 1024 * 1024)
    result = parse_bytes(data, sys.argv[1], int(sys.argv[2]))
    sys.stdout.write(json.dumps(result))


if __name__ == '__main__':
    main()
