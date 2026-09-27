import {sourceNotices} from '../source-notices.js';
import {api,requestKey,download} from '../api.js';
import {el,button,link,heading,badge,textarea,field,busy,notice,card,select,input,table,modal,dateText,empty} from '../ui.js';
import type {App,Json} from '../types.js';
import {uploadInto} from './research.js';

export async function workspacesView(app:App){
  const rows=(await api('/runs')).items;
  const create=button('New workspace',()=>{
    const name=input('text','','workspace-name');
    const save=button('Create workspace',async()=>{try{await api('/workspaces','POST',{name:name.value});await app.refreshAccount();dialog.close();await workspacesView(app);}catch(e){app.showError(e);}});
    const dialog=modal('Create a workspace',field('Workspace name',name),save);
  },'secondary');
  async function collaborators(workspace:Json){
    const list=(await api(`/workspaces/${workspace.id}/members`)).items;
    const email=input('email','','collaborator-email'),role=select([['reviewer','Reviewer'],['editor','Editor'],['viewer','Viewer']]);
    const dialog=modal(workspace.name+' · collaborators',table(['Name','Email','Role'],list.map((x:Json)=>[x.name,x.email,x.role])));
    if(workspace.role==='owner'){
      const add=button('Add registered account',async()=>{try{await api(`/workspaces/${workspace.id}/members`,'POST',{email:email.value,role:role.value});dialog.close();await collaborators(workspace);}catch(e){app.showError(e);}});
      dialog.append(field('Account email',email),field('Role',role),notice('The collaborator must already have an account. This action does not send an email invitation.'),add);
    }
  }
  app.content.replaceChildren(heading('Your research, organized.','Private workspaces keep facts, evidence, and deliverables together.',create),
    el('div',{class:'grid three'},...app.workspaces.map(w=>card(w.name,badge(w.role),button('Collaborators',()=>collaborators(w),'quiet')))),
    card('Saved research',rows.length?table(['Question','Workflow','Status','Created',''],rows.map((r:Json)=>[r.question,r.workflow.replaceAll('_',' '),r.state,dateText(r.created_at),link(app,'Open',`/runs/${r.id}`)])):
      empty('No research tasks yet','Start with a scoped question in Agent studio.',link(app,'Explore tasks','/agents','button primary'))));
}

export async function documentsView(app:App){
  const workspace=select(app.workspaces.map(w=>[w.id,w.name]));const list=el('div');
  async function refresh(){
    if(!workspace.value){list.replaceChildren(empty('No workspace','Create a workspace before uploading.'));return;}
    const rows=(await api(`/workspaces/${workspace.value}/documents`)).items;
    const view=async(id:string)=>{try{const d=await api('/documents/'+id);modal(d.name,notice(`${d.scan_status}. Text extraction may omit visual structure.`),el('div',{class:'document-preview'},...d.chunks.slice(0,100).map((c:Json)=>el('section',{},badge(c.locator),el('p',{},c.text)))));}catch(e){app.showError(e);}};
    const remove=(d:Json)=>{
      const confirm=button('Delete document and derived content',async()=>{try{await api('/documents/'+d.id,'DELETE');dialog.close();await refresh();}catch(e){app.showError(e);}},'danger');
      const dialog=modal('Delete '+d.name+'?',notice('This deletes its original object and searchable text and clears dependent generated results and memo content. Downloaded exports cannot be recalled. Cancel active dependent tasks first.','warning'),confirm);
    };
    list.replaceChildren(rows.length?table(['Document','State','Size','Scanning','Actions'],rows.map((d:Json)=>[
      d.name,d.status,`${Math.ceil(d.size/1024)} KB`,d.scan_status,
      el('div',{class:'row-actions'},button('Inspect text',()=>view(d.id),'quiet'),button('Delete',()=>remove(d),'quiet danger-text'))])):
      empty('No documents in this workspace','Add your own contracts, policies, and memos after activating Agent.'));
  }
  workspace.onchange=()=>void refresh();
  app.content.replaceChildren(heading('Private documents','Existing content remains available after subscription expiry, subject to source permissions and retention.',
    button('Upload document · Agent',()=>uploadInto(app,workspace.value,refresh),'primary')),
    field('Workspace',workspace),list);await refresh();
}

export async function memoView(app:App,id?:string){
  if(!id){
    const items=(await api('/memos')).items;
    const blank=button('New blank memo',()=>{
      const name=input('text','Untitled memo','memo-new-title'),workspace=select(app.workspaces.map(w=>[w.id,w.name]));
      const create=button('Create blank memo',async()=>{try{const m=await api('/memos','POST',{workspace_id:workspace.value,title:name.value,body:''});dialog.close();app.navigate('/memos/'+m.id);}catch(e){app.showError(e);}});
      const dialog=modal('Create a manual memo',notice('Manual editing is free. AI-generated memo writing is an Agent task.'),field('Title',name),field('Workspace',workspace),create);
    },'secondary');
    app.content.replaceChildren(heading('Memo library','Versioned drafts with evidence and review history.',blank),items.length?
      table(['Memo','Revision','Updated',''],items.map((m:Json)=>[m.title,m.revision,dateText(m.updated_at),link(app,'Open memo','/memos/'+m.id)])):
      empty('No memos yet','Create a blank memo or generate a draft with Agent.',link(app,'Write with Agent','/agents/memo','button primary')));
    return;
  }
  let memo=await api('/memos/'+id);let dirty=false,saving=false,disposed=false,conflict=false;let timeout:ReturnType<typeof setTimeout>|undefined;
  const title=input('text',memo.title,'memo-title'),editor=textarea(memo.body,'memo-body',26);
  const status=el('span',{class:'muted',role:'status'},`Saved · revision ${memo.revision}`);
  const reviewBadge=badge(memo.review_state.replaceAll('_',' '),memo.review_state==='draft'?'warning':'neutral');
  const save=button('Save changes',async()=>saveNow(),'secondary');
  async function saveNow(){
    if(!dirty||saving||disposed||conflict)return;
    saving=true;save.disabled=true;status.textContent='Saving…';
    const bodyAtStart=editor.value,titleAtStart=title.value;
    try{
      memo=await api('/memos/'+id,'PUT',{expected_revision:memo.revision,title:titleAtStart,body:bodyAtStart});
      dirty=editor.value!==bodyAtStart||title.value!==titleAtStart;
      reviewBadge.textContent='draft';status.textContent=`Saved · revision ${memo.revision}`;
      if(dirty)timeout=setTimeout(()=>void saveNow(),1200);
    }catch(e){status.textContent='Not saved';if((e as any).status===409)conflict=true;app.showError(e);}
    finally{saving=false;save.disabled=false;}
  }
  function onEdit(){dirty=true;reviewBadge.textContent='draft · edited';status.textContent='Unsaved changes';clearTimeout(timeout);timeout=setTimeout(()=>void saveNow(),1200);}
  title.oninput=onEdit;editor.oninput=onEdit;
  const beforeUnload=(e:BeforeUnloadEvent)=>{if(dirty){e.preventDefault();e.returnValue='';}};
  window.addEventListener('beforeunload',beforeUnload);
  app.canLeave=()=>!dirty||confirm('Discard unsaved memo changes and leave?');
  app.cleanup=()=>{disposed=true;clearTimeout(timeout);window.removeEventListener('beforeunload',beforeUnload);};
  const review=button('Record human review',async()=>{
    await saveNow();if(dirty||conflict){app.showError(new Error('Save and resolve conflicts before recording review.'));return;}
    const note=textarea('','review-note',3);
    const submit=button('Record review of this revision',async()=>{try{memo=await api(`/memos/${id}/reviews`,'POST',{expected_revision:memo.revision,note:note.value});reviewBadge.textContent=memo.review_state.replaceAll('_',' ');dialog.close();}catch(e){app.showError(e);}},'primary');
    const dialog=modal('Review revision '+memo.revision,notice('Your identity and the exact revision are recorded. Reviewing a memo you authored or edited is labeled self-review, not independent review.'),field('Review scope and notes',note),submit);
  },'secondary');
  const exportSelect=select([['md','Markdown'],['docx','Word DOCX'],['pdf','PDF'],['html','HTML']],'md','export-format');exportSelect.setAttribute('aria-label','Export format');
  const exportButton=button('Download',async()=>{try{await saveNow();if(dirty)throw new Error('Save your changes before export.');await download(`/memos/${id}/export?format=${exportSelect.value}`,`accounting-memo.${exportSelect.value}`);}catch(e){app.showError(e);}},'secondary');
  const history=button('Revision history',async()=>{try{const revisions=(await api(`/memos/${id}/revisions`)).items;modal('Memo revision history',...revisions.map((r:Json)=>el('details',{},el('summary',{},`Revision ${r.revision} · ${dateText(r.created_at)}`),el('pre',{class:'source-text'},r.body),sourceNotices(r.source_attributions))));}catch(e){app.showError(e);}},'quiet');
  const critique=button('Challenge this memo · Agent',async()=>{
    if(!app.me?.access.agent_allowed){app.upgrade('AI memo critique');return;}
    await saveNow();if(dirty)return;
    try{const run=await api('/runs','POST',{workspace_id:memo.workspace_id,workflow:'memo_review',
      question:'Review this saved accounting memo for unsupported claims, inconsistent facts, missing alternatives, and authority gaps.',
      inputs:{memo_id:id},context:{framework:'US_GAAP'},facts:[],document_ids:[]},requestKey());app.navigate('/runs/'+run.id);}catch(e){app.showError(e);}
  });
  app.content.replaceChildren(heading('Memo editor','Manual editing and downloading existing work do not require an active subscription.',reviewBadge),
    el('div',{class:'editor-toolbar'},save,review,history,exportSelect,exportButton,critique),
    notice('AI-assisted research draft — verify sources and obtain appropriate professional review. Exports use the saved revision.'),
    sourceNotices(memo.source_attributions),field('Memo title',title),field('Memo content (Markdown)',editor),el('div',{class:'editor-status'},status,
      button('Reload saved revision',()=>{if(!dirty||confirm('Discard unsaved changes and reload?'))app.navigate('/memos/'+id);},'quiet')));
}
