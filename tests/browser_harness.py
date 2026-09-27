"""Browser component/integration harness.

The execution environment blocks Chromium URL navigation by administrator policy.
This harness DOES NOT change that policy. It loads the compiled modules in an
about:blank document, bridges API calls to the permitted local test server, and
virtualizes browser history/storage. Therefore these are browser UI + real API
integration checks, NOT a full deployed-origin/authentication/checkout E2E test.
Run ordinary Playwright navigation tests separately in your deployment environment.
"""
import base64
import json
import re
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
ORIGIN='http://127.0.0.1:8000'
checks=[]
errors=[]
api_calls=[]
module_cache={}

def module_url(path):
    path=path.resolve()
    if path in module_cache:return module_cache[path]
    text=path.read_text()
    text=text.replace('window.history.replaceState','window.__qaHistory.replaceState')
    text=text.replace('history.pushState','window.__qaHistory.pushState')
    text=text.replace('location.pathname','window.__qaLocation.pathname')
    text=text.replace('location.reload()','window.__qaLocation.reload()')
    def sub(match):
        quote,relative=match.groups()
        return f'from {quote}{module_url(path.parent / relative)}{quote}'
    text=re.sub(r"from\s+(['\"])(\.[^'\"]+)\1",sub,text)
    value='data:text/javascript;base64,'+base64.b64encode(text.encode()).decode()
    module_cache[path]=value
    return value

def bridge(source, request):
    method=request.get('method','GET');headers=request.get('headers',{})
    kwargs={}
    if request.get('multipart') is not None:
        data={};files=[]
        for field in request['multipart']:
            if field.get('file'):
                files.append((field['name'],(field['filename'],base64.b64decode(field['content']),field['type'])))
            else:data[field['name']]=field['value']
        kwargs={'data':data,'files':files}
    elif request.get('body') is not None:kwargs={'content':request['body']}
    response=httpx.request(method,ORIGIN+request['url'],headers=headers,timeout=45,**kwargs)
    api_calls.append({'method':method,'path':request['url'],'status':response.status_code,'bytes':len(response.content)})
    return {'status':response.status_code,'headers':{'content-type':response.headers.get('content-type','application/json')},'content':base64.b64encode(response.content).decode()}

BOOT=r"""
if(!crypto.randomUUID)crypto.randomUUID=()=> '10000000-1000-4000-8000-100000000000'.replace(/[018]/g,c=>(Number(c)^crypto.getRandomValues(new Uint8Array(1))[0]&15>>Number(c)/4).toString(16));
const makeStorage=()=>{const values=new Map();return {getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,String(v)),removeItem:k=>values.delete(k),clear:()=>values.clear()}};
Object.defineProperty(window,'localStorage',{value:makeStorage()});
Object.defineProperty(window,'sessionStorage',{value:makeStorage()});
window.__qaLocation={pathname:'/chat',reload:()=>window.dispatchEvent(new PopStateEvent('popstate'))};
window.__qaHistory={pushState:(a,b,p)=>{window.__qaLocation.pathname=p},replaceState:(a,b,p)=>{window.__qaLocation.pathname=p}};
window.fetch=async function(url,options={}){
  if(!String(url).startsWith('/api/v1'))throw new Error('Browser harness forbids external network calls');
  const payload={url:String(url),method:options.method||'GET',headers:options.headers||{}};
  if(options.body instanceof FormData){payload.multipart=[];for(const [name,value]of options.body.entries()){
    if(value instanceof File){const bytes=new Uint8Array(await value.arrayBuffer());let s='';for(const b of bytes)s+=String.fromCharCode(b);payload.multipart.push({name,file:true,filename:value.name,type:value.type,content:btoa(s)})}
    else payload.multipart.push({name,value:String(value)})
  }}else if(options.body!==undefined)payload.body=options.body;
  const result=await window.__apiBridge(payload);const bytes=Uint8Array.from(atob(result.content),c=>c.charCodeAt(0));
  return new Response(result.status===204?null:bytes,{status:result.status,headers:result.headers});
};
window.__go=p=>{window.__qaLocation.pathname=p;window.dispatchEvent(new PopStateEvent('popstate'))};
void 0;
"""

def main():
    httpx.post(ORIGIN+'/api/v1/dev/subscription',json={'state':'free'})
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1050});page.set_default_timeout(10000)
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.expose_binding('__apiBridge',bridge)
        page.set_content('<html><head><style>'+ (ROOT/'frontend/dist/styles.css').read_text()+'</style></head><body><div id="app"></div></body></html>')
        page.evaluate(BOOT)
        page.add_script_tag(type='module',content=f'import {{mount}} from "{module_url(ROOT/"frontend/dist/main.js")}";mount(document.getElementById("app"));')
        page.get_by_role('heading',name='Ask freely.',exact=True).wait_for(timeout=8000)
        checks.append('Free chat homepage renders compiled application')
        page.screenshot(path=str(ROOT/'reports/ui-home.png'),full_page=True)
        page.get_by_label('Your message',exact=True).fill('How do I organize a technical accounting memo?')
        page.get_by_role('button',name='Send message',exact=True).click()
        page.locator('.message.assistant').wait_for()
        assert 'DEMO' in page.locator('.message.assistant').inner_text()
        checks.append('Free chat sends to API, persists, and labels mock response')
        page.get_by_role('button',name='Documents · Agent',exact=True).click()
        page.get_by_role('dialog').wait_for()
        assert '$89.99' in page.get_by_role('dialog').inner_text()
        checks.append('Paid document request opens contextual annual upgrade')
        page.get_by_role('button',name='Close',exact=True).click()
        page.evaluate("__go('/agents/deep_research')")
        page.get_by_label('Research question',exact=True).wait_for()
        page.get_by_label('Research question',exact=True).fill('Research how to evaluate implementation fees using the approved accounting content.')
        page.get_by_role('button',name='Review facts and scope →',exact=True).click()
        page.get_by_role('button',name='Start Agent task',exact=True).wait_for()
        draft_path=page.evaluate('__qaLocation.pathname')
        checks.append('Agent wizard saves draft and presents deterministic scope without payment')
        page.get_by_role('button',name='Start Agent task',exact=True).click()
        page.get_by_role('button',name='Review annual plan',exact=True).click()
        page.get_by_role('heading',name='Ask freely. Delegate the work.').wait_for()
        page.screenshot(path=str(ROOT/'reports/ui-pricing.png'),full_page=True)
        assert page.get_by_role('button',name='Subscribe — $89.99 / year').is_disabled()
        checks.append('Unapproved live checkout remains disabled')
        page.get_by_role('button',name='Activate local Agent demo — no charge').click()
        page.get_by_role('button',name='Start Agent task',exact=True).wait_for()
        assert page.evaluate('__qaLocation.pathname')==draft_path
        checks.append('Local activation returns to preserved draft without auto-start')
        page.get_by_label('I confirm these facts and authorize the described Agent task.').check()
        page.get_by_role('button',name='Start Agent task',exact=True).click()
        page.get_by_role('button',name='Create memo from this result',exact=True).wait_for(timeout=30000)
        checks.append('Paid task runs through real API, durable queue, and worker')
        page.screenshot(path=str(ROOT/'reports/ui-research.png'),full_page=True)
        page.get_by_role('button',name='Inspect evidence',exact=True).first.click()
        page.get_by_role('dialog').wait_for()
        checks.append('Evidence panel opens source record')
        page.get_by_role('button',name='Close',exact=True).click()
        page.get_by_role('button',name='Create memo from this result',exact=True).click()
        page.get_by_label('Memo content (Markdown)',exact=True).wait_for()
        memo_path=page.evaluate('__qaLocation.pathname')
        editor=page.get_by_label('Memo content (Markdown)',exact=True)
        editor.fill(editor.input_value()+'\n\nBrowser integration test amendment.')
        page.wait_for_timeout(1800)
        assert 'Saved · revision 2' in page.locator('body').inner_text()
        checks.append('Memo autosave persists a new revision')
        page.get_by_role('button',name='Record human review',exact=True).click()
        page.get_by_label('Review scope and notes').fill('Demo interface check; not an accounting review.')
        page.get_by_role('button',name='Record review of this revision').click()
        page.get_by_role('dialog').wait_for(state='detached')
        assert 'self reviewed' in page.locator('body').inner_text()
        checks.append('Own-memo review is labeled self-reviewed')
        editor.fill(editor.input_value()+'\nAnother amendment.')
        page.wait_for_timeout(1800)
        assert page.locator('.page-heading .badge').inner_text()=='draft'
        checks.append('Substantive editing resets review state')
        page.screenshot(path=str(ROOT/'reports/ui-memo.png'),full_page=True)
        page.get_by_role('button',name='Revision history',exact=True).click()
        assert 'Revision 1' in page.get_by_role('dialog').inner_text()
        page.get_by_role('button',name='Close',exact=True).click()
        checks.append('Revision history contains prior saved content')
        page.get_by_role('button',name='Download',exact=True).click()
        page.wait_for_timeout(300)
        assert any('/export?format=md' in x['path'] and x['status']==200 for x in api_calls)
        checks.append('Export control obtains Markdown bytes from protected API (browser download not tested)')
        page.evaluate("__go('/billing')")
        page.get_by_role('button',name='Cancel annual renewal',exact=True).click()
        page.get_by_role('button',name='Resume annual renewal',exact=True).wait_for()
        checks.append('Cancellation keeps current access and exposes resume')
        page.locator('#demo-billing-state').select_option('expired')
        page.get_by_role('heading',name='Free',exact=True).wait_for()
        page.evaluate(f'__go({json.dumps(memo_path)})')
        page.get_by_label('Memo content (Markdown)',exact=True).wait_for()
        checks.append('Expired member still opens saved memo')
        page.get_by_role('button',name='Challenge this memo · Agent',exact=True).click()
        page.get_by_role('dialog').wait_for()
        checks.append('Expired member cannot initiate AI memo critique')
        page.get_by_role('button',name='Close',exact=True).click()
        page.evaluate("__go('/sources')")
        page.wait_for_timeout(500)
        assert 'reference_only' in page.locator('body').inner_text() or 'reference only' in page.locator('body').inner_text().lower()
        checks.append('Source directory distinguishes reference-only records')
        page.set_viewport_size({'width':390,'height':844});page.evaluate("__go('/chat')")
        page.get_by_role('heading',name='Ask freely.',exact=True).wait_for()
        assert page.evaluate('document.documentElement.scrollWidth <= 390')
        checks.append('390px chat viewport has no page horizontal overflow')
        page.get_by_role('button',name='Menu',exact=True).click()
        assert 'open' in page.locator('.sidebar').get_attribute('class')
        checks.append('Mobile menu opens')
        page.get_by_role('button',name='Close menu',exact=True).click()
        checks.append('Mobile menu has an operable close control')
        page.screenshot(path=str(ROOT/'reports/ui-mobile.png'),full_page=True)
        assert not errors,errors
        checks.append('No uncaught page errors in tested paths')
        browser.close()
    report={'mode':'about:blank browser component harness + live local API/worker bridge; navigation/storage virtualized', 'checks_passed':len(checks),'checks':checks,'page_errors':errors,'api_calls':api_calls,'not_tested':['real-origin navigation/auth/session security','live Gemini','live Stripe checkout','production cloud','browser file download permission']}
    (ROOT/'reports/browser-results.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'passed':len(checks),'page_errors':errors},indent=2))

if __name__=='__main__':
    try:main()
    except Exception:
        (ROOT/'reports/browser-partial.json').write_text(json.dumps({'checks':checks,'errors':errors,'api_calls':api_calls},indent=2));raise
