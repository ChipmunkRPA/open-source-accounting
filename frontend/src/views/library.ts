import {sourceNotices} from '../source-notices.js';
import {api} from '../api.js';
import {el,button,link,heading,badge,textarea,field,notice,card,select,input,checkbox,table,modal,textBlock,dateText,empty} from '../ui.js';
import type {App,Json} from '../types.js';

export async function sourcesView(app:App){
  const q=input('search','','source-search');q.placeholder='Search source title or publisher';const list=el('div');
  const framework=select([['','All frameworks'],['US_GAAP','U.S. GAAP'],['IFRS','IFRS'],['BOTH','Cross-framework'],['AUDIT','Auditing']]);
  async function refresh(){const rows=(await api(`/sources?q=${encodeURIComponent(q.value)}&framework=${framework.value}`)).items;
    list.replaceChildren(...rows.map((s:Json)=>el('article',{class:'source-row'},el('div',{},el('h2',{},s.title),el('p',{class:'muted'},`${s.publisher} · ${s.kind}`)),badge(s.access,s.access==='reference_only'?'warning':'neutral'),link(app,'Inspect source','/sources/'+encodeURIComponent(s.id),'button secondary'))));
    if(!rows.length)list.append(empty('No matching sources','Try a broader topic or remove the framework filter.'));
  }
  q.oninput=()=>void refresh();framework.onchange=()=>void refresh();
  app.content.replaceChildren(heading('Sources you can inspect.','Coverage and reuse rights are evaluated separately from your subscription.'),
    notice('The open library contains original editorial drafts. This directory separately lists sources admitted through rights review, not a complete standards corpus.'),
    el('div',{class:'filters'},field('Search',q),field('Framework',framework)),list);await refresh();
}

export async function topicsView(app:App){
  const rows=(await api('/topics')).items;
  app.content.replaceChildren(heading('Learn the research process.','Original educational material. No proprietary standards have been copied into the starter corpus.'),
    link(app,'Browse the full open library →','/library'),
    el('div',{class:'grid two'},...rows.map((r:Json)=>card(r.title,badge('ORIGINAL CONTENT','free'),el('p',{class:'muted'},r.summary),sourceNotices(r.source_attributions),button('Read guide',async()=>{const s=await api('/sources/'+r.id);modal(s.title,textBlock(s.text||''),sourceNotices(s.source_attributions));},'secondary')))));
}

export async function settingsView(app:App,logout:()=>void){
  const me=app.me!;const reduced=checkbox('Reduce interface motion',!!me.preferences.reduced_motion),compact=checkbox('Prefer compact display',!!me.preferences.compact);
  const framework=select([['US_GAAP','U.S. GAAP'],['IFRS','IFRS'],['UNKNOWN','Ask each time']],me.preferences.default_framework||'US_GAAP');
  const message=el('div');const save=button('Save preferences',async()=>{try{await api('/me/preferences','PUT',{reduced_motion:reduced.input.checked,compact:compact.input.checked,default_framework:framework.value});await app.refreshAccount();message.replaceChildren(notice('Preferences saved.'));}catch(e){app.showError(e);}});
  const category=select([['accuracy','Accounting accuracy'],['citation','Citation'],['copyright','Content rights'],['privacy','Privacy'],['interface','Interface'],['other','Other']]);
  const feedback=textarea('','feedback-message',4);
  const submit=button('Submit feedback',async()=>{try{await api('/feedback','POST',{category:category.value,message:feedback.value});feedback.value='';message.replaceChildren(notice('Feedback saved for operator review. No email was sent.'));}catch(e){app.showError(e);}},'secondary');
  app.content.replaceChildren(heading('Settings','Preferences, account, and support.'),
    el('div',{class:'grid two'},card('Reading and research',reduced.element,compact.element,field('Default framework',framework),message,save),
      card('Account',el('p',{},me.email),el('p',{class:'muted'},app.config.auth_mode==='dev'?'Local test identity; not production authentication.':'Session tokens are held in browser memory.'),button('Sign out',logout,'quiet'))),
    card('Report an issue',field('Category',category),field('Description',feedback),submit),
    card('Privacy and retention',el('p',{},'Private workspaces are isolated by membership. Source text is supplied to the configured model only through the authorized research path. Document deletion clears its source text and dependent generated content.'),
      el('p',{class:'muted'},'This starter does not represent a completed production privacy program. Cloud-provider retention, backups, regional controls, and legal obligations require deployment review.')));
}
