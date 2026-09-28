import {api,requestKey} from '../api.js';
import {el,button,heading,notice,table,link,field,input,card,dateText} from '../ui.js';
import type {App,Json} from '../types.js';

export async function searchIndexView(app:App,initialSource=''){
  if(!app.me||!['admin','rights_approver'].includes(app.me.role)){
    app.content.replaceChildren(heading('Administrator access required','Search index maintenance is restricted to scoped administrators.'));
    return;
  }
  let disposed=false,sourceBusy=false,sweepBusy=false,sourceState:Json|null=null,sweep:Json|null=null;
  let sourceTicket=0,sweepTicket=0,historyTicket=0,createKey=requestKey();
  let historyBefore:string|null=null,receiptAfter:number|null=null;
  const sourceId=input('text',initialSource,'index-source-id'),sweepId=input('text',new URLSearchParams(location.search).get('sweep')||'','index-sweep-id');
  const sourceInfo=el('div',{'aria-live':'polite'}),sourceMessage=el('div'),sweepInfo=el('div',{'aria-live':'polite'}),sweepMessage=el('div');
  const history=el('div'),receipts=el('div'),inventory=el('div');
  const path=(id:string)=>'/admin/sources/'+encodeURIComponent(id)+'/search-index';
  const sweepPath=(id:string)=>'/admin/search-index/sweeps/'+encodeURIComponent(id);
  app.cleanup=()=>{disposed=true;sourceTicket++;sweepTicket++;historyTicket++;};
  const error=(host:HTMLElement,e:unknown)=>{if(!disposed)host.replaceChildren(notice((e as Error).message,'error'));};

  function sourceControls(){
    sourceId.disabled=sourceBusy;loadSource.disabled=sourceBusy;
    build.disabled=sourceBusy||!sourceState?.global_index_allowed;
    remove.disabled=sourceBusy||!sourceState?.stored;
  }
  function showSource(){
    if(!sourceState){sourceInfo.replaceChildren(notice('Load a source ID to inspect its current index state.'));return;}
    sourceInfo.replaceChildren(el('p',{},'Source: '+sourceState.source_id),
      table(['Stored entry','Current at check','Build permitted'],[[sourceState.stored?'Yes':'No',sourceState.current?'Yes':'No',sourceState.global_index_allowed?'Yes':'No']]),
      el('p',{},'Index version: '+(sourceState.index_version||'No stored index')),
      el('p',{class:'review-hash'},'Source revision: '+sourceState.expected_revision),
      notice(sourceState.global_index_allowed?'Indexing permission is present. Model use, applicability and output rights are still checked separately.':'Required indexing permissions or reviews are missing. Resolve those through the existing review process.','warning'));
  }
  async function sourceWork(action:'load'|'build'|'remove'){
    if(sourceBusy)return;
    const id=sourceId.value.trim(),snapshot=sourceState,ticket=++sourceTicket;
    if(!id){error(sourceMessage,new Error('Enter a source ID.'));return;}
    if(action!=='load'&&snapshot?.source_id!==id){error(sourceMessage,new Error('Load the selected source before changing its index.'));return;}
    sourceBusy=true;sourceControls();sourceMessage.replaceChildren();
    try{
      if(action==='build')await api(path(id),'POST',{expected_revision:snapshot!.expected_revision});
      if(action==='remove')await api(path(id),'DELETE');
      const result=await api(path(id));if(disposed||ticket!==sourceTicket)return;
      sourceState=result;showSource();
      if(action!=='load'){sourceMessage.replaceChildren(notice(action==='build'?'Index build completed for this revision.':'Derived index removed. The original source is retained.'));await loadInventory();}
    }catch(e){if(ticket===sourceTicket){sourceState=null;showSource();error(sourceMessage,e);}}
    finally{sourceBusy=false;if(!disposed)sourceControls();}
  }
  const loadSource=button('Load index status',()=>sourceWork('load'),'secondary');
  const build=button('Build or refresh index',()=>sourceWork('build'));
  const remove=button('Remove derived index',()=>sourceWork('remove'),'quiet danger-text');
  sourceId.oninput=()=>{sourceTicket++;sourceState=null;showSource();sourceControls();};
  const sourceForm=el('form',{},field('Source ID',sourceId),loadSource);sourceForm.onsubmit=e=>{e.preventDefault();void sourceWork('load');};

  async function loadInventory(){try{const value=await api('/admin/search-index/inventory');if(!disposed)inventory.replaceChildren(el('p',{},'Stored body-index entries: '+value.stored_entries),notice(value.notice));}catch(e){error(inventory,e);}}
  function sweepControls(){
    start.disabled=sweepBusy;loadSweep.disabled=sweepBusy;sweepId.disabled=sweepBusy;
    advance.disabled=sweepBusy||!sweep||sweep.state==='completed';
    loadReceipts.disabled=sweepBusy||!sweep;
    moreReceipts.disabled=sweepBusy||receiptAfter===null;
  }
  function showSweep(){
    if(!sweep){sweepInfo.replaceChildren(notice('Start a sweep or load a saved sweep to inspect progress.'));return;}
    sweepInfo.replaceChildren(el('p',{},'Sweep '+sweep.id+' · '+sweep.state+' · sequence '+sweep.sequence),
      el('p',{},'Started '+dateText(sweep.started_at)+' · completed '+dateText(sweep.completed_at)),
      el('p',{},'Cleanup version: '+sweep.cleanup_version),
      table(['Stored at start','Observed','Retained at check','Removed','Vanished before check'],[[sweep.initial_stored,sweep.scanned,sweep.retained,sweep.removed,sweep.vanished]]),
      notice(sweep.coverage_note),notice('Original sources remain. Removal from backups, replicas and storage media has not been verified.','warning'),
      el('p',{class:'review-hash'},'Cursor: '+(sweep.cursor||'Not advanced')+' · upper ID: '+(sweep.upper_id||'Empty range')));
  }
  async function sweepWork(action:'start'|'load'|'advance',selectedId?:string){
    if(sweepBusy)return;
    const id=selectedId||sweepId.value.trim(),snapshot=sweep,ticket=++sweepTicket;
    if(action!=='start'&&!id){error(sweepMessage,new Error('Enter or select a sweep ID.'));return;}
    if(action==='advance'&&snapshot?.id!==id){error(sweepMessage,new Error('Load the selected sweep before advancing it.'));return;}
    sweepBusy=true;sweepControls();sweepMessage.replaceChildren();
    try{
      let result:Json;
      if(action==='start'){result=await api('/admin/search-index/sweeps','POST',undefined,createKey);createKey=requestKey();}
      else if(action==='advance')result=await api(sweepPath(id)+'/advance','POST',{expected_sequence:snapshot!.sequence});
      else result=await api(sweepPath(id));
      if(disposed||ticket!==sweepTicket)return;
      sweep=result;sweepId.value=result.id;receipts.replaceChildren();receiptAfter=null;showSweep();
      if(action!=='load'){await Promise.all([loadInventory(),loadHistory()]);sweepMessage.replaceChildren(notice(action==='start'?'Sweep saved. Use the next-batch button to perform cleanup.':'Batch committed. Inspect the receipts or continue with the next batch.'));}
    }catch(e){if(ticket===sweepTicket){sweep=null;receipts.replaceChildren();receiptAfter=null;showSweep();error(sweepMessage,e);}}
    finally{sweepBusy=false;if(!disposed)sweepControls();}
  }
  const start=button('Start cleanup sweep',()=>sweepWork('start'));
  const loadSweep=button('Load saved sweep',()=>sweepWork('load'),'secondary');
  const advance=button('Check next 100 entries',()=>sweepWork('advance'));
  const loadReceipts=button('Load batch receipts',()=>readReceipts(false),'secondary');
  const moreReceipts=button('Load more receipts',()=>readReceipts(true),'quiet');
  sweepId.oninput=()=>{sweepTicket++;sweep=null;receipts.replaceChildren();receiptAfter=null;showSweep();sweepControls();};
  const sweepForm=el('form',{},field('Saved sweep ID',sweepId),loadSweep);sweepForm.onsubmit=e=>{e.preventDefault();void sweepWork('load');};

  async function readReceipts(more:boolean){
    if(sweepBusy||!sweep)return;
    const id=sweep.id,ticket=sweepTicket,after=more?receiptAfter:0;
    if(after===null)return;
    sweepBusy=true;sweepControls();sweepMessage.replaceChildren();
    try{
      const page=await api(sweepPath(id)+'/receipts?after='+after);if(disposed||ticket!==sweepTicket)return;
      if(!more)receipts.replaceChildren();
      if(!page.items.length&&!more)receipts.append(notice('No batch receipts yet. Starting an empty sweep does not create a batch.'));
      for(const item of page.items){
        const r=item.receipt,body=el('div'),details=el('details',{},el('summary',{},`Batch ${r.sequence} · ${r.observations.length} observations · ${r.state}`),body);
        details.ontoggle=()=>{if(details.open&&!body.childNodes.length)body.append(
          el('p',{class:'review-hash'},'Receipt SHA-256: '+item.receipt_sha256),
          table(['Source ID','Outcome','Index version','Index revision','Indexed-text SHA-256'],r.observations.map((o:Json)=>[o.source_id,o.outcome.replaceAll('_',' '),o.index_version||'Unavailable',o.index_revision||'Unavailable',o.indexed_text_sha256||'Unavailable'])));};
        receipts.append(details);
      }
      receiptAfter=page.next_after;
    }catch(e){error(sweepMessage,e);}
    finally{sweepBusy=false;if(!disposed)sweepControls();}
  }
  async function loadHistory(more=false){
    const ticket=++historyTicket;historyMore.disabled=true;
    try{
      const page=await api('/admin/search-index/sweeps'+(more&&historyBefore?'?before='+encodeURIComponent(historyBefore):''));
      if(disposed||ticket!==historyTicket)return;
      if(!more)history.replaceChildren();
      if(!page.items.length&&!more)history.append(notice('No saved cleanup sweeps.'));
      else history.append(table(['Sweep','Started','State','Observed / removed','Open'],page.items.map((s:Json)=>[
        s.id,dateText(s.started_at),s.state,s.scanned+' / '+s.removed,button('Load '+s.id,()=>sweepWork('load',s.id),'quiet')])));
      historyBefore=page.next_before;
    }catch(e){error(sweepMessage,e);}
    finally{if(!disposed&&ticket===historyTicket)historyMore.disabled=!historyBefore;}
  }
  const historyMore=button('Older sweeps',()=>loadHistory(true),'quiet');
  const historyRefresh=button('Refresh saved sweeps',()=>loadHistory(),'secondary');
  app.content.replaceChildren(heading('Search index administration','Inspect derived indexes and reconcile stale entries.',link(app,'Source administration','/admin')),
    inventory,card('Source index',sourceForm,sourceInfo,el('div',{class:'row-actions'},build,remove),sourceMessage),
    card('Cleanup',notice('Cleanup checks existing derived indexes. It does not acquire content, grant review approval, or start a recurring schedule.'),start,sweepForm,sweepInfo,
      el('div',{class:'row-actions'},advance,loadReceipts),sweepMessage,receipts,moreReceipts),
    card('Saved cleanup sweeps',historyRefresh,history,historyMore));
  showSource();sourceControls();showSweep();sweepControls();
  await Promise.all([loadInventory(),loadHistory(),...(initialSource?[sourceWork('load')]:[]),...(sweepId.value?[sweepWork('load')]:[])]);
}
