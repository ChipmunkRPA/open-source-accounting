"""Fail closed on unexpected public source and generated modules."""
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
EXACT = set('''AGENTS.md LICENSE NOTICE.md license-notice.md .gitignore .dockerignore README.md CONTRIBUTING.md SECURITY.md PUBLISHING.md progress.md
CONTENT-TERMS.md robots.txt
frontend/src/annotation.ts frontend/public/robots.txt frontend/public/content-terms.txt
frontend/tests/content-policy.test.mjs scripts/tests/test_content_policy.py scripts/tests/test_irs_source_pilot.py
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
IRS_SOURCE_FILES = {'content/irs-source-pilot/2026-10-04/README.md': '23f66e7370976f6f997f2a616589cf402f552865dd68e4adb0548f0abeec3ee2', 'content/irs-source-pilot/2026-10-04/manifest.json': 'f4abc02491a0e6515a8a7db4771daa664e274b98821dd8d9bb8fbb62a20cef4e', 'content/irs-source-pilot/2026-10-04/originals/rr-08-26.pdf': 'aa202c190dae8428c5f6f1ab33a9cc44264411eca43f40fb192825b81aa476eb', 'content/irs-source-pilot/2026-10-04/originals/rr-19-19.pdf': '57f1ead842d713c38d7b8c884e72755a3d134c40dceb0e1d1882c8ddb4ba24d2', 'content/irs-source-pilot/2026-10-04/originals/rr-19-24.pdf': 'e0ccbbefc302668b4aefb9476058476a449b29d412f359b1fc0eb7da232407a5', 'content/irs-source-pilot/2026-10-04/originals/rr-21-02.pdf': '57b3c7e8c54c54d9a55c2329d14e676b9d07289ca0fdc451db80840d03d030ca', 'content/irs-source-pilot/2026-10-04/originals/rr-24-05.pdf': '00e323652b6a9574bb3fcc95cd8cfb5ddac98069b2f88bbf459adf99a2fee082', 'content/irs-source-pilot/2026-10-04/originals/rr-25-15.pdf': '9c9c802370e22c9bc1ff9d9b943fdbe5d4b9056dd6abb17bf7b0a2d5ce207974', 'content/irs-source-pilot/2026-10-04/originals/rr-26-16.pdf': 'b9b20f782596a26da8bfb6a0b3b87b933817194073d2e9bda9143c6b5cbed2a9', 'content/irs-source-pilot/2026-10-04/originals/rr-26-20.pdf': 'ef8b0ec3cb3000319e95bcbe320497e896ac6633deeafa814fedc030e3fe46d0', 'content/irs-source-pilot/2026-10-04/text/rr-08-26.txt': 'cb19eb785572a84da0492722473f8753855f134b4b3658d5077e25b62188b0d2', 'content/irs-source-pilot/2026-10-04/text/rr-19-19.txt': '5087494860075f4c126600f821467397ad9029ce1ed1dfd0b8fe3aac42e5ab23', 'content/irs-source-pilot/2026-10-04/text/rr-19-24.txt': 'b4a74db956bdc1f983816d5937d60de397db23d883edf838f7eac93a3db5588c', 'content/irs-source-pilot/2026-10-04/text/rr-21-02.txt': '66718ef1ea5bdde1acd561b14a47808abbdb03e160579d5c42806a5e51f004c1', 'content/irs-source-pilot/2026-10-04/text/rr-24-05.txt': '5c336c45ca66eb80c22142e971899457d21ae99958f70d87ed53c94f7bf8e667', 'content/irs-source-pilot/2026-10-04/text/rr-25-15.txt': 'ad97250529faee2287d30c5297affa2509e07a3d8ea362811079ed6bce55baba', 'content/irs-source-pilot/2026-10-04/text/rr-26-16.txt': '0de6b26bb290e803a76a9deb04b8a6fc838d84abbaced74f3a70b3d52a58b206', 'content/irs-source-pilot/2026-10-04/text/rr-26-20.txt': '204f45c59e864ea4cd320b730039c4fee4cbea6ee414fc4bc378a13cfdc4c754', 'content/irs-source-pilot/2026-10-04-batch-02/README.md': '364b1d39ad648b58099b21c14f55b5f7e3ab3590d6cdd68e116768ae1d4037e6', 'content/irs-source-pilot/2026-10-04-batch-02/manifest.json': '6c953086fc081b4e3b823c23683ac8c7531c6c34b6393e3e1289fcae25f5e026', 'content/irs-source-pilot/2026-10-04-batch-02/originals/n-25-22.pdf': 'c5386ae27e475eb5189a1d338ba1ad78acf63381607a37cb12d5b88219bce5c4', 'content/irs-source-pilot/2026-10-04-batch-02/originals/n-25-23.pdf': '7b09ec8ef561ac8c1219f1e528e20f12f332639cacfef4145c1d0ad71f687401', 'content/irs-source-pilot/2026-10-04-batch-02/originals/n-25-55.pdf': '920572c3e9b03ca351d0d122c1f21c366e4bce7acbf5c5313b3a99bbaf25f460', 'content/irs-source-pilot/2026-10-04-batch-02/originals/n-26-06.pdf': '6c61dd799979c1264dd1e4a60eb53a2d5235d0d9867e8208e31fc144dff92097', 'content/irs-source-pilot/2026-10-04-batch-02/originals/n-26-09.pdf': 'a2986be576d4834d0d751a77a78b53b70f9bbe16b278ab76accdfffcd6fb6153', 'content/irs-source-pilot/2026-10-04-batch-02/originals/n-26-52.pdf': 'c0d02ae45e20a797d8ec0d1bfc81c435530bc240079585aa9543df336672944b', 'content/irs-source-pilot/2026-10-04-batch-02/originals/rp-25-14.pdf': 'cc28893a3c0ed1d5ca67c88dc3661b2d09573f79aa85ac1c5f35f9a489f4b447', 'content/irs-source-pilot/2026-10-04-batch-02/originals/rp-26-30.pdf': '0f3186408efb9170e87689b1152ffc3f9362dc64ccd6ca8ebd6f69454cba3a3e', 'content/irs-source-pilot/2026-10-04-batch-02/text/n-25-22.txt': '5d98b78f0f0310262c50eeb6a0ca740fab1e6aac83de49a812bc3b20cadf833f', 'content/irs-source-pilot/2026-10-04-batch-02/text/n-25-23.txt': '0d9a7b07f65ad8617a0a59e5a8dfcd7c107518361ef36b1d5f6e75473a9db88b', 'content/irs-source-pilot/2026-10-04-batch-02/text/n-25-55.txt': '2fb145d160a170c48d51499ad69d47099db92d1cf75d79d0a8fb442a968a17da', 'content/irs-source-pilot/2026-10-04-batch-02/text/n-26-06.txt': '283c51c06f692e7dae9a74bccbfc19caea3713cec12a3f3b2678f8f7c7a8f102', 'content/irs-source-pilot/2026-10-04-batch-02/text/n-26-09.txt': '5b442b44150e55218f5e962506854873dc11f77ac97f2d72e6eef4324fdee752', 'content/irs-source-pilot/2026-10-04-batch-02/text/n-26-52.txt': '9a0c72c015de01816ee59cdaa384c9c9e02d2472a9ab773d65a9f7760a3d75c3', 'content/irs-source-pilot/2026-10-04-batch-02/text/rp-25-14.txt': '8993705f242777426eec4168dfbd9d6930ba532a70d0198ae3cf3fe92c89bc6d', 'content/irs-source-pilot/2026-10-04-batch-02/text/rp-26-30.txt': '7c88786259fdcc5a205697d4b29c96d2908a02dba02a2e6e00419039aebded9d'}
def allowed(name):
    if name.startswith('content/irs-source-pilot/'):
        return name in IRS_SOURCE_FILES
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
    elif name in IRS_SOURCE_FILES and __import__('hashlib').sha256(p.read_bytes()).hexdigest() != IRS_SOURCE_FILES[name]: errors.append(name+' (IRS source hash mismatch)')
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
