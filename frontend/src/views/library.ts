import {api} from '../api.js';
import {el,button,link,heading,badge,textarea,field,notice,card,select,input,checkbox,table,modal,textBlock,dateText,empty} from '../ui.js';
import type {App,Json} from '../types.js';

export async function sourcesView(app:App){
  const q=input('search','','source-search');q.placeholder='Search source title or publisher';const list=el('div');
  const framework=select([['','All frameworks'],['US_GAAP','U.S. GAAP'],['IFRS','IFRS'],['BOTH','Cross-framework'],['AUDIT','Auditing']]);
  async function open(id:string){const s=await api('/sources/'+id);modal(s.title,badge(s.access,s.access==='reference_only'?'warning':'neutral'),el('p',{class:'muted'},`${s.publisher} · ${s.version}`),
    s.text?textBlock(s.text):notice('Reference metadata only. No primary text is reproduced or available to the model.','warning'),
    s.url?el('a',{href:s.url,target:'_blank',rel:'noopener noreferrer'},'Open publisher source ↗'):el('span'));}
  async function refresh(){const rows=(await api(`/sources?q=${encodeURIComponent(q.value)}&framework=${framework.value}`)).items;
    list.replaceChildren(...rows.map((s:Json)=>el('article',{class:'source-row'},el('div',{},el('h2',{},s.title),el('p',{class:'muted'},`${s.publisher} · ${s.kind}`)),badge(s.access,s.access==='reference_only'?'warning':'neutral'),button('Inspect source',()=>open(s.id),'secondary'))));
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
    el('div',{class:'grid two'},...rows.map((r:Json)=>card(r.title,badge('ORIGINAL CONTENT','free'),el('p',{class:'muted'},r.summary),button('Read guide',async()=>{const s=await api('/sources/'+r.id);modal(s.title,textBlock(s.text||''));},'secondary')))));
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

export async function adminView(app:App){
  const result=await api('/admin/sources');const list=el('div');
  function draw(){list.replaceChildren(table(['Source','State','Policy version','Actions'],result.items.map((s:Json)=>[
    s.title,s.enabled?(s.reviewed?'Rights approved':'Needs rights review'):'Disabled',s.policy_version,
    el('div',{class:'row-actions'},button('Policy',()=>modal(s.title,el('pre',{class:'source-text'},JSON.stringify(s.policy,null,2))),'quiet'),
      button('Approve rights',async()=>{try{if(!confirm('Confirm that you personally reviewed the rights for this exact work, version and operations. This does not grant technical accounting approval.'))return;await api(`/admin/sources/${s.id}/approve`,'POST',{expected_policy_version:s.policy_version,expected_rights_revision:s.rights_revision,confirm_actual_rights_review:true});await adminView(app);}catch(e){app.showError(e);}},'quiet'),
      button('Disable',async()=>{try{await api(`/admin/sources/${s.id}/disable`,'POST');await adminView(app);}catch(e){app.showError(e);}},'quiet danger-text'))])));}
  draw();
  const title=input('text','','source-title'),publisher=input('text','','source-publisher'),url=input('url','','source-url'),text=textarea('','source-text',6);
  const framework=select([['US_GAAP','U.S. GAAP'],['IFRS','IFRS'],['BOTH','Both'],['AUDIT','Auditing']]);
  const kind=select([['original_commentary','Original commentary'],['reference','Reference metadata'],['rule','Rule'],['standard','Standard'],['staff_guidance','Staff guidance'],['company_example','Company example']]);
  const policy=textarea(JSON.stringify({basis:'original',commercial_use:true,model_input:true,store_text:true,display_full:true,quote:true,export:true,embed:false,train:false,review_note:'Explain and independently review the reuse and acquisition basis.'},null,2),'source-policy',10);
  const message=el('div');
  const submit=button('Submit for independent approval',async()=>{try{await api('/admin/sources','POST',{title:title.value,publisher:publisher.value,canonical_url:url.value,kind:kind.value,framework:framework.value,text:text.value||null,policy:JSON.parse(policy.value)});await adminView(app);}catch(e){message.replaceChildren(notice((e as Error).message,'error'));}});
  app.content.replaceChildren(heading('Source administration','Two-person approval for publication and permission grants. Emergency restriction is immediate.'),list,
    card('Submit a new source record',el('div',{class:'grid two'},field('Title',title),field('Publisher',publisher),field('Canonical HTTPS link',url),field('Framework',framework),field('Authority category',kind)),
      field('Permitted source text (leave blank for references)',text),field('Operation-level rights policy (JSON)',policy),notice('Do not place privileged legal advice or unlicensed source material here. Submission is not legal approval.','warning'),message,submit));
}

export async function watchesView(app:App){
  const watches=(await api('/watches')).items,notes=(await api('/notifications')).items;
  const topic=input('text','','watch-topic'),workspace=select(app.workspaces.map(w=>[w.id,w.name])),cadence=select([['1','Daily'],['7','Weekly'],['30','Every 30 days']]);
  const consent=checkbox('I authorize scheduled checks of new approved platform sources and in-app notifications.');
  const create=button('Create watch · Agent',async()=>{if(!consent.input.checked){app.showError(new Error('Opt in before creating the watch.'));return;}
    try{await api('/watches','POST',{workspace_id:workspace.value,topic:topic.value,cadence_days:Number(cadence.value),consent:true});await watchesView(app);}catch(e){app.showError(e);}});
  create.disabled=!app.config.experimental_agents_enabled;
  app.content.replaceChildren(heading('Watch inbox','Checks new approved platform source records—not the unrestricted web. No emails are sent by this version.'),
    !app.config.experimental_agents_enabled?notice('The watch module is experimental and disabled in this deployment.','warning'):notice('Watches pause at subscription expiry. They do not make automatic accounting adoption decisions.'),
    el('div',{class:'grid two'},card('Create a watch',field('Topic keywords',topic),field('Workspace',workspace),field('Cadence',cadence),consent.element,create),
      card('Saved watches',watches.length?table(['Topic','Cadence','State',''],watches.map((w:Json)=>[w.topic,`${w.cadence_days} days`,w.enabled?'Enabled':'Paused',button('Pause',async()=>{await api('/watches/'+w.id,'DELETE');await watchesView(app);},'quiet')])):el('p',{class:'muted'},'No saved watches.'))),
    card('Notifications',...notes.map((n:Json)=>el('article',{class:'source-row'},el('div',{},el('h3',{},n.title),el('p',{},n.body)),badge(n.read?'Read':'New'),button('Mark read',async()=>{await api(`/notifications/${n.id}/read`,'POST');await watchesView(app);},'quiet')))));
}
