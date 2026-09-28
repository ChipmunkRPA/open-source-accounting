import {runRelationships} from './run-relationships.js';
import {sourceNotices} from '../source-notices.js';
import {api,requestKey,saveBlob} from '../api.js';
import {el,button,link,heading,badge,textarea,field,busy,notice,card,select,input,checkbox,table,modal,textBlock,dateText,empty} from '../ui.js';
import type {App,Json} from '../types.js';

export async function studioView(app:App){
  const catalog=(await api('/agents')).items as Json[];
  const search=input('search','','agent-search');search.placeholder='Find a task: revenue, memo, controls…';
  const filter=select([['','All categories'],...Array.from(new Set(catalog.map(x=>x.category))).map(x=>[x,x] as [string,string])]);
  const grid=el('div',{class:'grid three'});
  function draw(){
    grid.replaceChildren(...catalog.filter(x=>(!filter.value||x.category===filter.value)&&
      `${x.title} ${x.description}`.toLowerCase().includes(search.value.toLowerCase())).map(x=>el('article',{class:'card agent-card'},
      el('div',{class:'card-meta'},badge(x.code),badge(x.enabled?'Agent':'Experimental',x.enabled?'paid':'neutral')),
      el('h2',{},x.title),el('p',{class:'muted'},x.description),el('small',{class:'muted'},x.outputs.slice(0,3).join(' · ')),
      link(app,x.id==='standards_watch'?'Configure watch →':'View task →',x.id==='standards_watch'?'/watches':`/agents/${x.id}`,'task-link'))));
  }
  search.oninput=draw;filter.onchange=draw;draw();
  app.content.replaceChildren(heading('Delegate the work.','Purpose-built workflows for research, documents, workpapers, and review.',
    badge(app.me?.access.agent_allowed?'Agent active':'$89.99 / year','paid')),
    notice('Every output is a draft. Agent access does not grant rights to unavailable standards. Experimental workflows require operator enablement.'),
    el('div',{class:'filters'},field('Find a task',search),field('Category',filter)),grid);
}

export async function uploadInto(app:App,workspace:string,refresh:()=>Promise<void>){
  if(!app.me?.access.agent_allowed){app.upgrade('Document processing');return;}
  const file=input('file','','upload-file');file.accept='.txt,.md,.pdf,.docx,.xlsx,.csv';
  const basis=select([['own_original','My original business document'],['licensed_for_this_service','Material licensed for processing with this service']]);
  const agree=checkbox('I am authorized to process this material here. It does not bypass a publisher restriction.');
  const message=el('div');
  const submit=button('Upload and process',async()=>{
    if(!file.files?.[0]||!agree.input.checked){message.replaceChildren(notice('Choose a file and confirm authorization.','error'));return;}
    busy(submit,true,'Scanning and parsing…');
    try{const form=new FormData();form.set('file',file.files[0]);form.set('authorization_basis',basis.value);
      await api(`/workspaces/${workspace}/documents`,'POST',form);await refresh();dialog.close();
    }catch(e){message.replaceChildren(notice((e as Error).message,'error'));}finally{busy(submit,false);}
  });
  const dialog=modal('Upload a private document',notice(`Text, Markdown, text-based PDF, DOCX, XLSX or UTF-8 comma-separated CSV. Spreadsheet formulas are not recalculated; caches and formatting remain unverified. Maximum ${app.config.max_upload_mb} MB. No OCR. Local demos do not scan files unless a scanner is configured.`),
    field('Document',file),field('Authorization basis',basis),agree.element,message,submit);
}

export async function taskView(app:App,workflow:string){
  const task=(await api('/agents')).items.find((x:Json)=>x.id===workflow);
  if(!task){app.content.replaceChildren(empty('Unknown task','Return to Agent studio.'));return;}
  const workspace=select(app.workspaces.map(w=>[w.id,w.name]));
  const question=textarea('','research-question',5);question.minLength=10;question.maxLength=8000;
  question.placeholder=task.id==='memo'?'Describe the issue, audience, and intended memo conclusion to investigate.':'Describe the issue and what you need the Agent to investigate.';
  const framework=select([['US_GAAP','U.S. GAAP'],['IFRS','IFRS'],['BOTH','U.S. GAAP and IFRS'],['UNKNOWN','Not yet known']],task.id==='framework_compare'?'BOTH':(app.me?.preferences.default_framework||'US_GAAP'),'framework');
  const entity=select([['unknown','Not specified'],['private','Private company'],['public','Public company'],['nonprofit','Nonprofit']],'unknown');
  const start=input('date','','period-start'),end=input('date','','period-end');
  const facts=textarea('','facts-input',4);facts.placeholder='One confirmed fact per line. Do not include assumptions as facts.';
  const docs=el('div',{class:'document-list'});let selected=new Set<string>();
  async function refreshDocs(){
    const rows=(await api(`/workspaces/${workspace.value}/documents`)).items;
    docs.replaceChildren(...rows.map((d:Json)=>{const c=checkbox(`${d.name} · ${d.chunk_count} text segments`,selected.has(d.id));c.input.onchange=()=>c.input.checked?selected.add(d.id):selected.delete(d.id);return c.element;}));
    if(!rows.length)docs.append(el('p',{class:'muted'},'No documents yet. Source-only research can proceed without documents.'));
  }
  workspace.onchange=()=>{selected.clear();void refreshDocs();};
  const extras=el('div',{class:'task-extras'});let collectInputs:()=>Json=()=>({});
  if(workflow==='revenue_workpaper'){
    const price=input('number','','transaction-price');price.min='0';price.step='.01';
    const lines=textarea('Subscription, 100000\nImplementation, 20000','ssp-items',3);
    extras.append(card('Optional allocation scenario',field('Transaction price',price),field('Item, standalone selling price — one per line',lines),
      notice('Arithmetic only. These inputs do not establish distinct performance obligations or the applicability of allocation exceptions.')));
    collectInputs=()=>price.value?{allocation:{transaction_price:price.value,items:lines.value.split('\n').filter(Boolean).map(line=>{const [name,ssp]=line.split(',');return {name:name.trim(),ssp:ssp?.trim()};})}}:{};
  }else if(workflow==='lease_workpaper'){
    const payment=input('number','','monthly-payment'),rate=input('number','','discount-rate'),months=input('number','12','lease-months'),first=input('date','','first-payment');
    rate.step='.0001';rate.min='0';rate.max='1';payment.step='.01';payment.min='0';months.min='1';months.max='600';
    extras.append(card('Optional fixed-payment schedule',el('div',{class:'grid two'},field('Monthly payment',payment),field('Annual nominal rate as a decimal (0.05 = 5%)',rate),field('Number of monthly payments',months),field('First payment date',first)),
      notice('Payments in arrears only. The application does not choose a discount rate or determine lease classification.')));
    collectInputs=()=>payment.value?{lease:{monthly_payment:payment.value,annual_discount_rate:rate.value,months:Number(months.value),first_payment_date:first.value,timing:'arrears'}}:{};
  }
  const error=el('div');
  const create=button('Review facts and scope →',async()=>{
    if(question.value.trim().length<10){error.replaceChildren(notice('Describe the question in at least ten characters.','error'));question.focus();return;}
    if(start.value&&end.value&&start.value>end.value){error.replaceChildren(notice('The reporting period start cannot follow the end.','error'));return;}
    busy(create,true,'Saving draft…');
    try{const run=await api('/runs','POST',{workspace_id:workspace.value,workflow,question:question.value,
      context:{framework:framework.value,entity_type:entity.value,period_start:start.value||null,period_end:end.value||null},
      facts:facts.value.split('\n').map(x=>x.trim()).filter(Boolean).map(text=>({text,status:'confirmed'})),
      document_ids:[...selected],inputs:collectInputs()},requestKey());app.navigate('/runs/'+run.id);
    }catch(e){error.replaceChildren(notice((e as Error).message,'error'));}finally{busy(create,false);}
  });
  create.disabled=!task.enabled;
  app.content.replaceChildren(heading(task.title,task.description,link(app,'← Agent studio','/agents','button quiet')),
    !task.enabled?notice('Experimental workflow. The operator has not enabled execution for this deployment.','warning'):notice(task.guardrail),
    el('div',{class:'intake-layout'},el('section',{class:'card'},badge('1 · DEFINE THE TASK'),field('Research question',question),
      el('div',{class:'grid two'},field('Workspace',workspace),field('Reporting framework',framework),field('Entity type',entity),field('Period begins',start),field('Period ends',end)),
      field('Confirmed facts',facts),extras,error,create),
      el('aside',{},card('2 · Select evidence',el('p',{class:'muted'},`This task requires ${task.min_documents} document(s). Uploaded material stays in this workspace.`),docs,
        button('Upload document · Agent',()=>uploadInto(app,workspace.value,refreshDocs),'secondary')),
        card('Your deliverable',el('ul',{},...task.outputs.map((x:string)=>el('li',{},x))),
          el('p',{class:'muted'},'Scope preview is free. Execution requires Agent and reserves one task.')))));
  if(workspace.value)await refreshDocs();
}

async function showEvidence(id:string){
  const e=await api('/evidence/'+id);
  const dialog=modal(e.title,badge(e.access,e.access==='reference_only'?'warning':'neutral'),
    el('p',{class:'muted'},`${e.locator} · ${e.source_kind}${e.version?' · version '+e.version:''}`),
    e.text?el('blockquote',{class:'source-text'},e.text):notice('Primary text was not accessed or is no longer available. This is not a verified quotation.','warning'));
  dialog.append(sourceNotices(e.source_attributions));
  if(e.url){const a=el('a',{href:e.url,target:'_blank',rel:'noopener noreferrer',class:'button secondary'},'Open publisher source ↗');dialog.append(a);}
}

export async function runView(app:App,id:string){
  if(!id){app.navigate('/agents');return;}
  let alive=true,pending=false;
  let disposeRelationships=()=>{};
  app.cleanup=()=>{alive=false;clearInterval(timer);disposeRelationships();};
  const body=el('div');app.content.replaceChildren(body);
  let lastState='';
  async function refresh(force=false){
    if(!alive||pending)return;pending=true;
    try{
      const run=await api('/runs/'+id);if(!alive)return;
      const key=`${run.state}:${run.revision}:${run.access_blocked}`;
      if(!force && key===lastState)return;lastState=key;disposeRelationships();disposeRelationships=()=>{};
      const top=heading(run.workflow.replaceAll('_',' '),run.question,link(app,'All work','/workspaces','button quiet'));
      if(['draft','planned','failed','cancelled','blocked'].includes(run.state)&&!run.result){
        const scope=await api(`/runs/${id}/scope`,'POST');
        const confirm=checkbox('I confirm these facts and authorize the described Agent task.');
        const msg=el('div');
        const start=button(run.state==='draft'?'Start Agent task':'Retry Agent task',async()=>{
          if(!app.me?.access.agent_allowed){app.upgrade(scope.workflow);return;}
          if(!confirm.input.checked){msg.replaceChildren(notice('Confirm the scope before starting.','error'));return;}
          busy(start,true,'Reserving task…');
          try{await api(`/runs/${id}/start`,'POST',{expected_revision:run.revision,confirm_scope:true},requestKey());await app.refreshAccount();lastState='';await refreshLater();}
          catch(e){app.showError(e);}finally{busy(start,false);}
        });
        const edit=button('Edit facts',()=>{
          const f=textarea(run.facts.map((x:Json)=>x.text).join('\n'));
          const save=button('Save facts',async()=>{try{await api(`/runs/${id}/facts`,'PUT',{expected_revision:run.revision,facts:f.value.split('\n').filter(Boolean).map(text=>({text,status:'confirmed'})),context:run.context});dialog.close();lastState='';void refresh();}catch(e){app.showError(e);}});
          const dialog=modal('Edit confirmed facts',field('One fact per line',f),save);
        },'secondary');
        body.replaceChildren(top,run.error_code?notice(`Previous attempt: ${run.error_code}. No completed-task allowance was consumed.`,'warning'):notice('Confirm the scope before the Agent starts. Your draft has been saved.'),
          el('div',{class:'grid two'},card('Facts and context',table(['Field','Value'],Object.entries(run.context).filter(([,v])=>v).map(([k,v])=>[k.replaceAll('_',' '),String(v)])),
            ...run.facts.map((f:Json)=>el('p',{},badge(f.status),f.text)),edit),
            card('Research scope',el('ul',{},...scope.sections.map((s:string)=>el('li',{},s))),notice(scope.guardrail),
              el('p',{},`${scope.documents_selected} selected documents. Required: ${scope.min_documents}.`),
              el('p',{class:'muted'},'One task is reserved on start; unsuccessful runs release that reservation. The model does not access unrestricted websites.'),confirm.element,msg,start)));
        return;
      }
      if(run.access_blocked){body.replaceChildren(top,notice('A supporting source changed or was removed. Output is withheld pending review. Payment cannot resolve source permissions.','warning'),link(app,'Review claim history or revoke a decision','/claim-review/'+encodeURIComponent(id),'button secondary'));return;}
      if(!run.result){
        const events=(await api(`/runs/${id}/events`)).items;
        body.replaceChildren(top,badge(run.state,'paid'),card('Research activity',
          el('ol',{class:'activity'},...events.map((x:Json)=>el('li',{},x.payload.state||x.kind))),
          el('p',{class:'muted'},'Activity records describe actions, not private internal reasoning. No percent-complete estimate is invented.'),
          button('Cancel task',async()=>{try{await api(`/runs/${id}/cancel`,'POST');lastState='';void refresh();}catch(e){app.showError(e);}},'secondary')),
          notice('Local development requires a separate worker process. Start it with python -m app.worker.'));
        return;
      }
      const result=run.result,evidence=(await api(`/runs/${id}/evidence`)).items;
      if(!alive)return;
      const main=el('section',{class:'analysis-panel'},badge('DRAFT · REVIEW REQUIRED','warning'),el('h2',{},result.title),textBlock(result.summary));
      for(const section of result.sections)main.append(el('section',{class:'analysis-section'},el('h3',{},section.heading),textBlock(section.body)));
      main.append(sourceNotices(result.source_attributions));
      if(result.claims?.length){main.append(el('h3',{},'Claims and supporting evidence'));
        for(const claim of result.claims)main.append(el('div',{class:'claim'},badge(claim.basis),textBlock(claim.text),
          el('div',{class:'citation-row'},...claim.evidence_ids.map((eid:string,i:number)=>button(`Evidence ${i+1}`,()=>showEvidence(eid),'citation'))),
          link(app,'Human review · '+claim.id,'/claim-review/'+encodeURIComponent(id)+'/'+encodeURIComponent(claim.id),'button secondary')));
      }
      const relationships=runRelationships(app,id);disposeRelationships=relationships.dispose;main.append(relationships.element);
      for(const t of result.tables||[])main.append(el('h3',{},t.title),table(t.columns,t.rows));
      const deterministic=result.deterministic||{};
      if(deterministic.comparison)main.append(el('h3',{},'Deterministic document comparison'),el('pre',{class:'diff'},deterministic.comparison.diff||'No text differences.'),notice(deterministic.comparison.warning));
      if(deterministic.allocation)main.append(el('h3',{},'Relative-SSP allocation'),table(['Item','SSP','Allocated amount'],deterministic.allocation.rows.map((x:Json)=>[x.name,x.ssp,x.allocated])),notice(deterministic.allocation.assumption));
      if(deterministic.lease)main.append(el('h3',{},`Illustrative lease liability · PV ${deterministic.lease.present_value}`),table(['Period','Payment date','Payment','Interest','Closing'],deterministic.lease.rows.slice(0,24).map((x:Json)=>[x.period,x.date,x.payment,x.interest,x.closing])),el('p',{class:'muted'},'Showing the first 24 periods. Download the full calculation data below.'));
      if(deterministic.lease||deterministic.allocation)main.append(button('Download calculation data',()=>saveBlob(new Blob([JSON.stringify(deterministic,null,2)],{type:'application/json'}),'calculation-data.json'),'secondary'));
      main.append(card('Limitations',el('ul',{},...result.limitations.map((s:string)=>el('li',{},s)))),card('Open questions',el('ul',{},...result.open_questions.map((s:string)=>el('li',{},s)))));
      const memo=button(run.memo_id?'Open memo':'Create memo from this result',async()=>{try{const m=run.memo_id?{id:run.memo_id}:await api(`/runs/${id}/memo`,'POST');app.navigate('/memos/'+m.id);}catch(e){app.showError(e);}});
      const follow=textarea('','follow-up',3);follow.placeholder='Ask a follow-up or describe revised facts. The previous result will be preserved.';
      const next=button('Prepare follow-up · Agent',async()=>{try{const child=await api(`/runs/${id}/follow-ups`,'POST',{question:follow.value},requestKey());app.navigate('/runs/'+child.id);}catch(e){app.showError(e);}},'secondary');
      body.replaceChildren(top,el('div',{class:'result-actions'},memo,badge(`${evidence.length} evidence records`)),
        el('div',{class:'research-grid'},el('aside',{class:'facts-panel'},el('h2',{},'Facts & scope'),el('p',{},run.context.framework),
          el('p',{class:'muted'},`${run.context.period_start||'Unknown start'} → ${run.context.period_end||'Unknown end'}`),
          ...run.facts.map((f:Json)=>el('div',{class:'fact'},badge(f.status),el('p',{},f.text)))),main,
          el('aside',{class:'evidence-panel'},el('h2',{},'Evidence'),...evidence.map((e:Json)=>el('article',{class:'evidence-card'},badge(e.access,e.access==='reference_only'?'warning':'neutral'),
            el('h3',{},e.title),el('p',{class:'muted'},e.locator),button('Inspect evidence',()=>showEvidence(e.id),'quiet'))))),
        card('Continue the research',field('Follow-up question',follow),next));
    }catch(e){if(alive)app.showError(e);}finally{pending=false;}
  }
  async function refreshLater(){setTimeout(()=>void refresh(true),0);}
  const timer=setInterval(()=>void refresh(),1500);
  await refresh(true);
}
