"""One-time, bounded source import. No cloud deployment or secret access."""
import base64
import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path.cwd().resolve()
meta_path = ROOT / '.release/import.json'
if not meta_path.exists():
    if (ROOT / 'backend/app/main.py').is_file():
        print('Source already imported; nothing to do.')
        raise SystemExit(0)
    raise SystemExit('Source manifest has not been uploaded.')
meta = json.loads(meta_path.read_text())
if meta.get('version') != '0.6.0' or not 1 <= len(meta.get('parts', [])) <= 100:
    raise SystemExit('Invalid source manifest.')
encoded = ''
for name in meta['parts']:
    path = Path(name)
    if path.parent.as_posix() != '.release' or not path.name.startswith('source-') or path.suffix != '.b64':
        raise SystemExit('Invalid payload path.')
    encoded += (ROOT / path).read_text().strip()
if len(encoded) > 2000000:
    raise SystemExit('Payload too large.')
compressed = base64.b64decode(encoded, validate=True)
if hashlib.sha256(compressed).hexdigest() != meta['sha256']:
    raise SystemExit('Compressed snapshot checksum mismatch.')
decoder = lzma.LZMADecompressor()
raw = decoder.decompress(compressed, max_length=8000001)
if len(raw) > 8000000 or not decoder.eof or decoder.unused_data:
    raise SystemExit('Invalid or oversized decompressed snapshot.')
if hashlib.sha256(raw).hexdigest() != meta['uncompressed_sha256']:
    raise SystemExit('Source snapshot checksum mismatch.')
entries = json.loads(raw)
if not isinstance(entries, list) or len(entries) != meta['files']:
    raise SystemExit('Source file count mismatch.')
allowed_roots = {'backend', 'frontend', 'content', 'docs', 'infra', 'scripts', 'tests', 'fixtures', 'reports'}
allowed_files = {'readme.md', 'progress.md', 'PUBLISHING.md', 'LICENSE', 'NOTICE.md', 'SECURITY.md', 'CONTRIBUTING.md', 'license-notice.md', 'Dockerfile', 'compose.yaml', 'Makefile', '.dockerignore'}
prepared = []
seen = set()
for entry in entries:
    name, content = entry.get('path'), entry.get('content')
    if not isinstance(name, str) or not isinstance(content, str):
        raise SystemExit('Invalid source entry.')
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or name in seen or any(ord(c) < 32 for c in name):
        raise SystemExit('Unsafe or duplicate source path.')
    github_metadata = name == '.github/pull_request_template.md' or name.startswith('.github/ISSUE_TEMPLATE/')
    if path.parts[0] not in allowed_roots and name not in allowed_files and not github_metadata:
        raise SystemExit('Unexpected source destination: ' + name)
    if any(p in {'.git', 'node_modules', '.venv', '__pycache__', 'data', '.terraform'} for p in path.parts):
        raise SystemExit('Private or generated directory in source snapshot.')
    if path.name.startswith('.env') and path.name not in {'.env.example', '.env.production.example'}:
        raise SystemExit('Private environment file in source snapshot.')
    target = ROOT / path
    for parent in [target, *target.parents]:
        if parent == ROOT:
            break
        if parent.is_symlink():
            raise SystemExit('Symlink conflict.')
    if not target.resolve().is_relative_to(ROOT):
        raise SystemExit('Source path escapes repository.')
    value = content.encode('utf-8')
    if len(value) > 5000000:
        raise SystemExit('Source entry too large.')
    if target.exists() and (not target.is_file() or target.read_bytes() != value):
        raise SystemExit('Refusing to overwrite conflicting existing source: ' + name)
    prepared.append((target, value))
    seen.add(name)
for path, value in prepared:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)
    if path.suffix == '.sh':
        path.chmod(0o755)
for name in meta['parts']:
    (ROOT / name).unlink()
meta_path.unlink()
(ROOT / '.release/import-report.json').write_text(json.dumps({
    'version': meta['version'], 'files_prepared': len(prepared),
    'source_sha256': meta['uncompressed_sha256'],
    'status': 'verified_source_prepared_for_commit',
    'cloud_deployment': False
}, indent=2) + '\n')
print('Verified and prepared', len(prepared), 'readable source files.')
