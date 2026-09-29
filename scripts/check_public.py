"""Fail closed on unexpected public source and generated modules."""
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
EXACT = set('''AGENTS.md LICENSE NOTICE.md license-notice.md .gitignore .dockerignore README.md CONTRIBUTING.md SECURITY.md PUBLISHING.md progress.md
.github/workflows/public.yml scripts/check_public.py scripts/serve_public.py
frontend/package.json frontend/package-lock.json frontend/tsconfig.json
frontend/public/index.html frontend/public/styles.css
frontend/scripts/build-vendor.mjs frontend/scripts/copy-assets.mjs frontend/scripts/clean.mjs frontend/scripts/build-library.mjs
frontend/vendor/identity.mjs frontend/vendor/machine.mjs frontend/tests/identity.test.mjs
frontend/src/main.ts frontend/src/api.ts frontend/src/authentication.ts frontend/src/entry.ts frontend/src/markdown.ts frontend/src/source-notices.ts frontend/src/types.ts frontend/src/ui.ts
frontend/src/views/chat.ts frontend/src/views/library.ts frontend/src/views/open-library.ts frontend/src/views/source-reader.ts frontend/src/views/sec-core.ts frontend/src/views/asu-tracking.ts frontend/src/views/sec-comments.ts'''.split())
def allowed(name):
    return name in EXACT or (name.startswith('content/') and Path(name).suffix in {'.md', '.json'})
names = subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().split('\0')
errors=[]
for name in set(names)-{''}:
    p=ROOT/name
    if not p.exists() and not p.is_symlink(): continue  # pending deletions
    if p.is_symlink() or not allowed(name): errors.append(name)
if '--dist' in sys.argv:
    expected={p.removeprefix('frontend/src/').removesuffix('.ts')+'.js' for p in EXACT if p.startswith('frontend/src/')}
    expected |= {p+'.map' for p in expected}
    expected |= {'index.html','styles.css','vendor/identity.js','vendor/identity.js.LEGAL.txt'}
    import json
    manifest=json.loads((ROOT/'content/manifest.json').read_text())
    expected |= {'library/index.html'} | {'library/'+i['id']+'.html' for i in manifest['items']}
    dist=ROOT/'frontend/dist'
    actual={p.relative_to(dist).as_posix() for p in dist.rglob('*') if p.is_file()}
    errors += ['dist/'+p for p in actual-expected]
    errors += ['missing dist/'+p for p in expected-actual]
    errors += [str(p) for p in dist.rglob('*') if p.is_symlink()]
if errors:
    raise SystemExit('Public boundary rejected:\n'+'\n'.join(sorted(errors)))
print('Public file boundary passed'+(' (including generated assets)' if '--dist' in sys.argv else ''))
