import {artifactIntegrityView} from './views/artifact-integrity.js';
import {correctionsView} from './views/corrections.js';
import {dependencyReportView} from './views/dependency-report.js';
import {secCoreView} from './views/sec-core.js';
import {showAuthentication} from './authentication.js';
import {api,configure,APIError,signOut} from './api.js';
import {el,button,link,heading,notice,badge,modal,input,field,select,busy,checkbox} from './ui.js';
import type {App,Config,Account} from './types.js';
import {chatView} from './views/chat.js';
import {studioView,taskView,runView} from './views/research.js';
import {memoView,workspacesView,documentsView} from './views/work.js';
import {pricingView,billingView} from './views/billing.js';
import {parserReviewView} from './views/parser-review.js';
import {openLibraryView,editorialView} from './views/open-library.js';
import {sourcesView,topicsView,settingsView,adminView,watchesView} from './views/library.js';

export async function mount(root:HTMLElement){
  root.replaceChildren(el('p',{class:'boot'},'Connecting to your workspace…'));
  let config:Config;
  try {config=await api<Config>('/config');configure(config);}catch{root.replaceChildren(notice('The API is unavailable. Start the backend and open its HTTP address.','error'));return;}
  const banner=el('div',{class:'global-banner','aria-live':'polite'});
  const content=el('main',{id:'main',class:'content',tabindex:-1});
  const app:App={config,me:null,workspaces:[],content,banner,
    navigate(path){if(!path.startsWith('/')||path.startsWith('//'))return;if(app.canLeave && !app.canLeave())return;history.pushState({},'',path);void render();},
    async refreshAccount(){app.me=await api<Account>('/me');app.workspaces=(await api('/workspaces')).items;updateAccount();},
    showError(error){
      const message=error instanceof Error?error.message:'The request could not be completed.';
      banner.replaceChildren(notice(message,'error'));
      if(error instanceof APIError && error.code==='SUBSCRIPTION_REQUIRED')app.upgrade();
      if(error instanceof APIError && (error.status===401||['MFA_REQUIRED','VERIFY_EMAIL','RECENT_AUTH_REQUIRED'].includes(error.code)))showAuth();
    },
    upgrade(task='Agent work'){
      if(location.pathname.startsWith('/runs/')) sessionStorage.setItem('oa_return_draft',location.pathname);
      const dialog=modal('Delegate the work with Agent',el('p',{},`${task} requires Agent. General AI chat stays free.`),
        el('div',{class:'upgrade-price'},'$89.99',el('span',{class:'muted'},' / year')),
        el('p',{class:'muted'},'One annual subscription. No automatic per-task charges. A subscription does not license unavailable source content.'));
      dialog.append(button('Review annual plan',()=>{dialog.close();app.navigate('/pricing');}),
                    button('Continue free chat',()=>{dialog.close();app.navigate('/chat');},'quiet'));
    }
  };
  const account=el('div',{class:'account'});
  const nav=el('nav',{'aria-label':'Main navigation'},
      link(app,'Chat · Free','/chat'),link(app,'Agent studio','/agents'),link(app,'My workspaces','/workspaces'),
      link(app,'Memos','/memos'),link(app,'Documents','/documents'),link(app,'Topics','/topics'),
      link(app,'Open library','/library'),link(app,'SEC Core','/sec-core'),link(app,'Sources','/sources'),link(app,'Watch inbox','/watches'),
      el('hr'),link(app,'Plans','/pricing'),link(app,'Billing & usage','/billing'),link(app,'Settings','/settings'),link(app,'Security','/security'));
  const sidebar:HTMLElement=el('aside',{class:'sidebar'},button('Close menu',()=>sidebar.classList.remove('open'),'quiet sidebar-close'),link(app,'osa / open-source-accounting','/chat','wordmark'),nav,
      el('div',{class:'sidebar-bottom'},badge(config.model_provider==='mock'?'Local demonstration':'Gemini 3.8 Flash'),
      el('p',{class:'muted'},'Ask freely. Delegate the work.')));
  const mobile=button('Menu',()=>sidebar.classList.toggle('open'),'quiet');mobile.classList.add('mobile-menu');
  const top=el('header',{class:'topbar'},mobile,el('span',{class:'top-label'},'Accounting research workspace'),account);
  function updateAccount(){
    account.replaceChildren();
    if(app.me){
      account.append(badge(app.me.access.agent_allowed?'Agent':'Free',app.me.access.agent_allowed?'paid':'neutral'),
                     el('span',{class:'account-name'},app.me.name));
      if(app.me.role==='technical_reviewer')account.append(link(app,'Content review','/editorial'),link(app,'Parser review','/parser-review'),link(app,'Dependency coverage','/dependency-report'));
      if(['admin','rights_approver'].includes(app.me.role))account.append(link(app,'Source admin','/admin'),link(app,'Corrections','/corrections'),link(app,'Artifact integrity','/artifact-integrity'));
      document.documentElement.classList.toggle('reduced-motion',!!app.me.preferences.reduced_motion);
      document.documentElement.classList.toggle('compact',!!app.me.preferences.compact);
    }else account.append(button('Sign in',()=>showAuth(),'secondary'));
    if(config.auth_mode==='dev'){
      const identity=select([['demo','Local: member'],['reviewer','Local: reviewer'],['admin','Local: admin'],['approver','Local: approver'],['editor','Local: technical reviewer']],localStorage.getItem('oa_demo_identity')||'demo','demo-identity');
      identity.setAttribute('aria-label','Local demo identity');identity.onchange=()=>{localStorage.setItem('oa_demo_identity',identity.value);location.reload();};
      account.append(identity);
    }
  }
  function showAuth(addBackup=false){
    app.cleanup?.();app.cleanup=undefined;app.me=null;app.workspaces=[];updateAccount();
    content.replaceChildren(heading('Secure sign-in required','Verify your account to access private workspaces. Public learning content remains available.'));
    void showAuthentication(async()=>{await app.refreshAccount();await render();},addBackup);
  }
  root.replaceChildren(sidebar,el('div',{class:'main-shell'},top,
    config.model_provider==='mock'?notice('LOCAL DEMO · Responses are deterministic samples. No Gemini calls or charges occur.'):null,
    banner,content));
  const page=(name:string)=>{document.title=`${name} · Open Source Accounting`;};
  async function render(){
    app.cleanup?.();app.cleanup=undefined;app.canLeave=undefined;banner.replaceChildren();sidebar.classList.remove('open');
    const path=location.pathname.split('/').filter(Boolean);
    const publicRoutes=['pricing','topics','sources','library','sec-core'];
    if(!app.me && !publicRoutes.includes(path[0]||'chat')){
      content.replaceChildren(heading('Welcome to Open Source Accounting','General AI chat is free. Agent workflows are $89.99 per year.'),button('Sign in to continue',()=>showAuth()));return;
    }
    content.replaceChildren(el('p',{class:'muted'},'Loading…'));
    try{
      switch(path[0]){
        case undefined:case 'chat':page('Free chat');await chatView(app,path[1]);break;
        case 'agents':page('Agent studio');path[1]?await taskView(app,path[1]):await studioView(app);break;
        case 'runs':page('Research');await runView(app,path[1]);break;
        case 'memos':page('Memos');await memoView(app,path[1]);break;
        case 'workspaces':page('Workspaces');await workspacesView(app);break;
        case 'documents':page('Documents');await documentsView(app);break;
        case 'sec-core':page('SEC Core');await secCoreView(app);break;
        case 'library':page('Open library');await openLibraryView(app,path[1]);break;
        case 'parser-review':page('Parser review');await parserReviewView(app);break;
        case 'dependency-report':page('Dependency coverage');await dependencyReportView(app);break;
        case 'editorial':page('Technical review');await editorialView(app);break;
        case 'sources':page('Sources');await sourcesView(app);break;
        case 'topics':page('Topics');await topicsView(app);break;
        case 'pricing':page('Plans');await pricingView(app);break;
        case 'billing':page('Billing');await billingView(app);break;
        case 'settings':page('Settings');await settingsView(app,async()=>{await signOut();location.reload();});break;
        case 'security':page('Security');content.replaceChildren(heading('Account security','Authenticator app or SMS is required for every signed-in account.'),
          notice(config.auth_mode==='dev'?'Local demo identity — MFA is not simulated or verified here.':`Current factor: ${app.me?.security?.factor||'unknown'}. Sessions expire after the configured maximum age.`),
          ...(config.auth_mode==='firebase'?[button('Reauthenticate and add a backup factor',()=>showAuth(true)),
          el('p',{},'You must sign in with your existing second factor before adding another. Enrollment ends the session; sign in again afterwards.')]:[]),
          el('p',{},'To replace a lost factor, contact the operator through the published support channel. There is no email-only MFA reset or recovery-code bypass in this application.'));break;
        case 'artifact-integrity':page('Stored artifact integrity');await artifactIntegrityView(app);break;
        case 'corrections':page('Corrections');await correctionsView(app);break;
        case 'admin':page('Source administration');await adminView(app);break;
        case 'watches':page('Watch inbox');await watchesView(app);break;
        default:content.replaceChildren(heading('Page not found','Use the navigation to return to your workspace.'));
      }
      for(const a of nav.querySelectorAll('a'))a.setAttribute('aria-current',location.pathname.startsWith(a.getAttribute('href')!)?'page':'false');
    }catch(error){app.showError(error);content.replaceChildren(heading('This view could not be loaded','Your saved work has not been changed.'),button('Try again',render,'secondary'));}
  }
  const onPopState=()=>void render();
  window.addEventListener('popstate',onPopState);
  try{await app.refreshAccount();}catch{updateAccount();}
  await render();
  return ()=>{window.removeEventListener('popstate',onPopState);app.cleanup?.();root.replaceChildren();};
}
