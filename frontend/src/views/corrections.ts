import {api,requestKey} from '../api.js';
import {el,button,field,heading,notice,select,textarea,table,link,busy} from '../ui.js';
import type {App,Json} from '../types.js';

export async function correctionsView(app:App){
  const sources=(await api('/admin/sources')).items as Json[];
  const source=select(sources.map(s=>[s.id,s.title+' · '+s.version]));
  const kind=select([['correction','Correction'],['takedown','Takedown']]),note=textarea();
  const status=select([['','All cases'],['open','Open'],['triaged','Triaged'],['resolved','Resolved'],['dismissed','Dismissed']]);
  const list=el('div'),details=el('div'),message=el('div');let offset=0,sequence=0;let createKey=requestKey();
  for(const control of [source,kind,note])control.addEventListener('input',()=>{createKey=requestKey();});
  const inspect=async(id:string)=>{
    try{
      const row=await api('/admin/corrections/'+id);const actionNote=textarea(),impactResult=el('div');
      const impact=button('Inspect potential dependents',async()=>{try{const r=await api('/admin/corrections/'+id+'/impact');impactResult.replaceChildren(notice(r.notice),el('p',{},r.total+' potential dependents; graph '+(r.graph_complete?'complete within report bounds':'incomplete')),el('p',{},r.affected_source_ids.join(', ')||'No dependents recorded.'));}catch(e){impactResult.replaceChildren(notice((e as Error).message,'error'));}},'quiet');
      const action=(name:string,label:string)=>{
        const b=button(label,async()=>{busy(b,true);try{
          await api('/admin/corrections/'+id+'/actions','POST',{action:name,expected_version:row.version,note:actionNote.value});
          await load();await inspect(id);
        }catch(e){message.replaceChildren(notice((e as Error).message,'error'));}finally{busy(b,false);}},name==='disable'?'danger':'secondary');return b;
      };
      const actions:HTMLElement[]=[];
      if(row.status==='open')actions.push(action('triage','Mark triaged'));
      if(row.status==='triaged')actions.push(action('resolve','Resolve case'));
      if(['open','triaged'].includes(row.status)){actions.push(action('dismiss','Dismiss case'));if(row.source_enabled)actions.push(action('disable','Disable source now'));}
      else actions.push(action('reopen','Reopen case'));
      details.replaceChildren(el('h2',{},'Case '+row.id),el('p',{},row.status+' · source '+row.source_id),
        notice(row.source_enabled?'Source is enabled. Opening a case does not disable it.':'Source is disabled. Closing this case will not restore it.'),
        ...(row.source_changed?[notice('Source revision has changed since this case was opened. Review current evidence.','warning')]:[]),
        impact,impactResult,field('Action rationale (private administrative notes only)',actionNote),el('div',{class:'row-actions'},...actions),
        el('h3',{},'Latest 50 actions'),table(['Version','Action','Actor','Note'],row.events.map((e:Json)=>[e.version,e.action,e.actor_id||'Deleted account',e.note])));
    }catch(e){message.replaceChildren(notice((e as Error).message,'error'));}
  };
  const load=async()=>{
    const ticket=++sequence;const result=await api('/admin/corrections?offset='+offset+(status.value?'&status='+status.value:''));if(ticket!==sequence)return;
    const prev=button('Previous',()=>{offset-=50;void load();},'quiet');prev.disabled=offset===0;
    const next=button('Next',()=>{offset+=50;void load();},'quiet');next.disabled=offset+result.items.length>=result.total;
    list.replaceChildren(el('p',{},result.total+' cases'),table(['Source ID','Kind','Status','Open'],result.items.map((r:Json)=>[r.source_id,r.kind,r.status,button('Inspect',()=>inspect(r.id),'quiet')])),prev,next);
  };
  const submit=button('Open case',async()=>{busy(submit,true);try{
    const s=sources.find(s=>s.id===source.value);if(!s)throw new Error('Select a staged source.');
    const row=await api('/admin/corrections','POST',{source_id:s.id,kind:kind.value,note:note.value,expected_policy_version:s.policy_version,expected_review_revision:s.review_revision},createKey);
    createKey=requestKey();note.value='';await load();await inspect(row.id);
  }catch(e){message.replaceChildren(notice((e as Error).message,'error'));}finally{busy(submit,false);}});
  status.onchange=()=>{offset=0;void load();};
  app.content.replaceChildren(heading('Corrections and takedowns','Private administrative queue.',link(app,'Source administration','/admin')),
    notice('Do not paste restricted source text, legal advice, credentials or client documents here. Describe the issue and refer to the approved restricted record. Resolution records triage; it does not grant rights or professional approval. Downloaded copies cannot be recalled.'),
    field('Source (latest 500 staged records)',source),field('Case type',kind),field('Issue and restricted record reference',note),submit,message,
    field('Case status',status),list,details);
  app.cleanup=()=>{sequence++;};await load();
}
