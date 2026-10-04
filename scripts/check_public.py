"""Fail closed on unexpected public source and generated modules."""
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
EXACT = set('''AGENTS.md LICENSE NOTICE.md license-notice.md .gitignore .dockerignore README.md CONTRIBUTING.md SECURITY.md PUBLISHING.md progress.md
CONTENT-TERMS.md robots.txt
frontend/src/annotation.ts frontend/public/robots.txt frontend/public/content-terms.txt
frontend/tests/content-policy.test.mjs scripts/tests/test_content_policy.py
.github/workflows/public.yml scripts/check_public.py scripts/serve_public.py
frontend/package.json frontend/package-lock.json frontend/tsconfig.json
frontend/public/index.html frontend/public/styles.css frontend/public/systems.js frontend/public/systems.css
frontend/scripts/build-vendor.mjs frontend/scripts/copy-assets.mjs frontend/scripts/clean.mjs frontend/scripts/build-library.mjs frontend/scripts/build-systems.mjs
frontend/vendor/identity.mjs frontend/vendor/machine.mjs frontend/tests/identity.test.mjs frontend/tests/systems.test.mjs
frontend/src/main.ts frontend/src/api.ts frontend/src/authentication.ts frontend/src/entry.ts frontend/src/markdown.ts frontend/src/source-notices.ts frontend/src/types.ts frontend/src/ui.ts
frontend/src/views/chat.ts frontend/src/views/library.ts frontend/src/views/open-library.ts frontend/src/views/source-reader.ts frontend/src/views/sec-core.ts frontend/src/views/asu-tracking.ts frontend/src/views/sec-comments.ts
corpus/govinfo/ecfr/2026-10-04/README.md
corpus/govinfo/ecfr/2026-10-04/ecfr-title-12.jsonl.gz
corpus/govinfo/ecfr/2026-10-04/ecfr-title-17.jsonl.gz
corpus/govinfo/ecfr/2026-10-04/ecfr-title-26.jsonl.gz.part01
corpus/govinfo/ecfr/2026-10-04/ecfr-title-26.jsonl.gz.part02
corpus/govinfo/ecfr/2026-10-04/ecfr-title-31.jsonl.gz
corpus/govinfo/ecfr/2026-10-04/ecfr-title-48.jsonl.gz
corpus/govinfo/ecfr/2026-10-04/manifest.json
tools/govinfo/collect_ecfr.py
tools/govinfo/export_ecfr.py
tools/govinfo/index_ecfr.py
tools/govinfo/load_snapshot.py
tools/govinfo/search_corpus.py'''.split())
TAX_CASE_FILES = {'content/tax-case-law/README.md', 'content/tax-case-law/BRIEFS.md', 'content/tax-case-law/case-catalog.json', 'content/tax-case-law/topic-index.json'}
CORE_STANDARDS_FILES = {
    'content/core-standards/README.md',
    'content/core-standards/directory.json',
    'content/core-standards/fasb-research-map.md',
    'content/core-standards/gasb-research-map.md',
    'content/core-standards/aicpa-research-map.md',
    'content/core-standards/esg-research-map.md',
    'content/core-standards/irs-research-map.md',
}
SALT_FILES = {'content/salt/2026-10-04/sources.json', 'content/salt/2026-10-04/README.md', 'content/salt/2026-10-04/local-layers.json', 'content/salt/2026-10-04/manifest.json', 'content/salt/2026-10-04/source-links.json', 'content/salt/2026-10-04/jurisdictions.json'}
def allowed(name):
    if any(part in {'fictional_annotations', 'copyright_detection', 'premium_private'} for part in Path(name).parts):
        return False
    if name.startswith('content/salt/'):
        return name in SALT_FILES
    if name.startswith('content/core-standards/'):
        return name in CORE_STANDARDS_FILES
    if name.startswith('content/tax-case-law/'):
        return name in TAX_CASE_FILES
    return name in EXACT or name in {'content/systems/logos/ramp.svg','content/systems/logos/chargebee.svg','content/systems/logos/xero.svg'} or (name.startswith('content/') and Path(name).suffix in {'.md', '.json'})

def contains_private_fiction(value):
    """Detect forbidden data recursively, not just an expected top-level schema."""
    if isinstance(value, dict):
        if (value.get('content_purpose') == 'fictional_copyright_detection'
                or value.get('storage_scope') == 'premium_private'
                or str(value.get('id', '')).startswith('osa-fiction-detection-')):
            return True
        return any(contains_private_fiction(v) for v in value.values())
    if isinstance(value, list):
        return any(contains_private_fiction(v) for v in value)
    return False

def fiction_file_error(path):
    import json
    if path.suffix == '.json':
        try:
            def unique(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError('Duplicate public content key')
                    result[key] = value
                return result
            return contains_private_fiction(json.loads(path.read_text(), object_pairs_hook=unique))
        except (ValueError, UnicodeError):
            return True  # Invalid content cannot prove the boundary.
    if path.suffix == '.md':
        # An actual private item ID in content is forbidden even without metadata.
        return 'osa-fiction-detection-' in path.read_text()
    return False

names = subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().split('\0')
errors=[]
for name in set(names)-{''}:
    p=ROOT/name
    if not p.exists() and not p.is_symlink(): continue  # pending deletions
    if p.is_symlink() or not allowed(name): errors.append(name)
    elif name.startswith('content/') and fiction_file_error(p): errors.append(name+' (private fiction)')
if '--dist' in sys.argv:
    expected={p.removeprefix('frontend/src/').removesuffix('.ts')+'.js' for p in EXACT if p.startswith('frontend/src/')}
    expected |= {p+'.map' for p in expected}
    expected |= {'index.html','styles.css','robots.txt','content-terms.txt','vendor/identity.js','vendor/identity.js.LEGAL.txt'}
    import json
    manifest=json.loads((ROOT/'content/manifest.json').read_text())
    expected |= {'library/index.html'} | {'library/'+i['id']+'.html' for i in manifest['items']}
    systems=json.loads((ROOT/'content/systems/catalog.json').read_text())
    expected |= {'systems/index.html','systems/methodology.html','systems/systems.js','systems/systems.css'}
    expected |= {'systems/'+s['id']+'.html' for s in systems['systems']}
    expected |= {'systems/'+s['logo']['path'] for s in systems['systems'] if s['logo']['status']=='official_media_asset'}
    dist=ROOT/'frontend/dist'
    actual={p.relative_to(dist).as_posix() for p in dist.rglob('*') if p.is_file()}
    errors += ['dist/'+p for p in actual-expected]
    errors += ['missing dist/'+p for p in expected-actual]
    errors += [str(p) for p in dist.rglob('*') if p.is_symlink()]
    errors += [str(p)+' (private fiction in generated page)' for p in dist.rglob('*.html')
               if 'osa-fiction-detection-' in p.read_text()]
if errors:
    raise SystemExit('Public boundary rejected:\n'+'\n'.join(sorted(errors)))
print('Public file boundary passed'+(' (including generated assets)' if '--dist' in sys.argv else ''))
