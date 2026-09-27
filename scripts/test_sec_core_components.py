#!/usr/bin/env python3
"""Offline compiled-component checks; no deployed browser, actual auth or network calls."""
from pathlib import Path
import json, shutil, sys
from urllib.parse import urlparse, parse_qs
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.sec_core.core import CorePack
from playwright.sync_api import sync_playwright


def main():
    pack=CorePack(ROOT/'content/sec_core');checks=[]
    def fixture(path):
        parsed=urlparse(path);q=parse_qs(parsed.query)
        if parsed.path=='/sec-core':return {**pack.report(),'sources':list(pack.entries.values())}
        if parsed.path=='/sec-core/search':return {'items':pack.preview(q.get('q',[''])[0],int(q.get('limit',['12'])[0]),q.get('family',[None])[0]),'agent_approved':False}
        if parsed.path.startswith('/sec-core/sources/'):return pack.public_source(parsed.path.split('/')[-1])
        raise ValueError('Unknown fixture endpoint')
    scripts=[]
    for rel in ['ui.js','views/sec-core.js']:
        text=(ROOT/'frontend/dist'/rel).read_text()
        text='\n'.join(line for line in text.splitlines() if not line.startswith('import '))
        scripts.append(text.replace('export async function','async function').replace('export function','function'))
    with sync_playwright() as p:
        executable=shutil.which('chromium')
        browser=p.chromium.launch(headless=True,**({'executable_path':executable} if executable else {}))
        page=browser.new_page(viewport={'width':1440,'height':1000});requests=[]
        page.on('request',lambda req:requests.append(req.url))
        page.set_content('<html><body><aside class="sidebar"><div class="wordmark">Open Source Accounting</div><nav><span>Chat · Free</span><span>Agent studio</span><span>Open library</span><span>SEC Core</span></nav></aside><div class="main-shell"><header class="topbar">SEC Core · local component validation</header><main id="main" class="content"></main></div></body></html>')
        page.add_style_tag(content=(ROOT/'frontend/public/styles.css').read_text())
        page.expose_function('secFixture',fixture)
        page.add_script_tag(content="let n=0;if(!crypto.randomUUID)crypto.randomUUID=()=>('fixture-'+(++n));")
        page.add_script_tag(content='\n'.join(scripts)+'''\nconst api=(path)=>window.secFixture(path);window.testApp={content:document.getElementById('main'),showError:e=>{throw e;}};window.renderSEC=()=>secCoreView(window.testApp);''')
        page.evaluate('window.renderSEC()')
        assert page.get_by_role('heading',name='SEC Core',exact=True).count()==1;checks.append('SEC Core heading')
        assert page.locator('tbody tr').count()==34;checks.append('34 explicit targets')
        assert page.get_by_text('FREE SOURCE READING',exact=False).count()==1;checks.append('public free-reading disclosure')
        page.get_by_label('Search official excerpts').fill('prominence')
        page.get_by_role('button',name='Search excerpts',exact=True).click();page.wait_for_timeout(160)
        assert page.get_by_role('button',name='Inspect exact excerpt',exact=True).count()>0;checks.append('source excerpt search')
        page.get_by_role('button',name='Inspect exact excerpt',exact=True).first.click();page.wait_for_timeout(80)
        assert page.get_by_role('dialog').count()==1 and page.locator('dialog pre').inner_text();checks.append('exact excerpt dialog')
        assert page.get_by_text('Text SHA-256',exact=True).count()==1;checks.append('hash provenance visible')
        assert page.get_by_role('link',name='Open official source',exact=True).get_attribute('rel')=='noopener noreferrer';checks.append('safe outbound source link')
        page.keyboard.press('Escape');page.wait_for_timeout(80)
        assert page.get_by_role('dialog').count()==0;checks.append('keyboard closes dialog')
        page.get_by_label('Collection',exact=True).select_option('reg_sx');page.wait_for_timeout(160)
        assert page.locator('tbody tr').count()==1;checks.append('collection filter')
        assert page.get_by_text('No excerpt in this starter pack matches.',exact=False).count()==1;checks.append('honest missing-text state')
        page.get_by_label('Collection',exact=True).select_option('');page.get_by_label('Search official excerpts').fill('equal prominence')
        page.get_by_role('button',name='Search excerpts',exact=True).click();page.wait_for_timeout(150)
        page.screenshot(path=str(ROOT/'reports/sec-core-desktop.png'),full_page=False)
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(120)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');checks.append('390px no page overflow')
        page.screenshot(path=str(ROOT/'reports/sec-core-mobile.png'),full_page=False)
        assert not requests;checks.append('zero network calls')
        browser.close()
    report={'passed':len(checks),'checks':checks,'mode':'compiled component with validated local source fixture','deployed_origin_tested':False,'actual_auth_tested':False}
    (ROOT/'reports/sec-core-components.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
