#!/usr/bin/env python3
"""Offline rendering checks of compiled library components, NOT deployed-origin E2E.
Requires Playwright and an installed Chromium. No URLs are navigated or fetched.
"""
from pathlib import Path
import json
import shutil
import sys
from urllib.parse import urlparse,parse_qs
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.content import Library
from playwright.sync_api import sync_playwright


def main():
    library=Library(ROOT/'content');checks=[]
    def fixture(path,*args):
        parsed=urlparse(path)
        if parsed.path.startswith('/library/'):
            return library.get(parsed.path.split('/')[-1])
        q=parse_qs(parsed.query)
        return library.search(q.get('q',[''])[0],q.get('topic',[''])[0],q.get('kind',[''])[0],int(q.get('offset',[0])[0]),int(q.get('limit',[24])[0]))
    scripts=[]
    for rel in ['ui.js','markdown.js','views/open-library.js']:
        text=(ROOT/'frontend/dist'/rel).read_text()
        text='\n'.join(line for line in text.splitlines() if not line.startswith('import '))
        text=text.replace('export async function','async function').replace('export function','function')
        scripts.append(text)
    executable=shutil.which('chromium')
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,**({'executable_path':executable} if executable else {}))
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.set_content('<html><head></head><body><aside class="sidebar"><div class="wordmark">oa / open source accounting</div><nav><span>Chat · Free</span><span>Agent studio</span><span>Open library</span></nav></aside><div class="main-shell"><header class="topbar">Open library · component rendering test</header><main id="main" class="content"></main></div></body></html>')
        page.add_style_tag(content=(ROOT/'frontend/public/styles.css').read_text())
        requests=[];page.on('request',lambda request:requests.append(request.url))
        page.expose_function('libraryFixture',fixture)
        # about:blank is not a secure application origin: deterministic IDs are test-only.
        page.add_script_tag(content="let fixtureId=0;if(!crypto.randomUUID)crypto.randomUUID=()=>('fixture-'+(++fixtureId));")
        source='\n'.join(scripts)+'''
const api=(path,...args)=>window.libraryFixture(path,...args);
window.testApp={content:document.getElementById('main'),navigate:path=>openLibraryView(window.testApp,path.startsWith('/library/')?path.split('/').pop():undefined),showError:error=>{throw error;}};
window.renderLibrary=id=>openLibraryView(window.testApp,id);
window.renderMarkdown=text=>markdown(text).element;
'''
        page.add_script_tag(content=source)
        page.evaluate('window.renderLibrary()')
        assert page.get_by_role('heading',name='An open library. Built for careful research.').count()==1;checks.append('library heading')
        assert page.locator('.library-grid .card').count()==24;checks.append('first-page 24 articles')
        page.get_by_role('button',name='Next',exact=True).click();page.wait_for_timeout(120)
        assert page.locator('.library-grid .card').count()==18;checks.append('pagination')
        page.get_by_label('Content type').select_option('case');page.wait_for_timeout(120)
        assert page.locator('.library-grid .card').count()==5;checks.append('case filter')
        page.get_by_label('Search library').fill('26730');page.wait_for_timeout(400)
        # Most formatted numbers use commas; zero results must render cleanly.
        assert page.get_by_text('No matching articles',exact=True).count()==1;checks.append('empty search')
        page.evaluate('window.renderLibrary()');page.screenshot(path=str(ROOT/'reports/library-desktop.png'),full_page=False)
        page.evaluate("window.renderLibrary('case-lease-present-value')")
        assert page.locator('tbody tr').count()==3;checks.append('safe Markdown table')
        assert page.get_by_role('link',name='FASB Accounting Standards Codification ↗',exact=True).count()==1;checks.append('source provenance')
        assert page.get_by_text('AI-ASSISTED · UNREVIEWED',exact=True).count()==1;checks.append('draft disclosure')
        page.screenshot(path=str(ROOT/'reports/library-article.png'),full_page=False)
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth');checks.append('390px no page overflow')
        page.screenshot(path=str(ROOT/'reports/library-mobile.png'),full_page=False)
        safe=page.evaluate("(text)=>{const node=window.renderMarkdown(text);return {scripts:node.querySelectorAll('script').length,links:node.querySelectorAll('a').length,text:node.textContent}}", '[bad](javascript:alert(1))\n\n<script>alert(1)</script>')
        assert safe['scripts']==0 and safe['links']==0 and '<script>' in safe['text'];checks.append('HTML/script and unsafe link rendered inert')
        assert requests==[];checks.append('no network requests')
        browser.close()
    report={'passed':len(checks),'checks':checks,'mode':'offline compiled-component rendering with local library fixture',
      'deployed_origin_tested':False,'browser_navigation':'Local URL navigation was blocked by environment policy; no policy was changed.',
      'download_flow_tested':False}
    (ROOT/'reports/library-components.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
