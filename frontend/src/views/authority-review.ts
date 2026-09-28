import {api} from '../api.js';
import {sourceNotices} from '../source-notices.js';
import {el,button,link,heading,notice,card,input,textarea,select,field,checkbox,table,dateText} from '../ui.js';
import {citationPicker} from './citation-picker.js';
import type {App,Json} from '../types.js';

export async function authorityReviewView(app:App,initialId=''){
  if(!app.me||!['admin','rights_approver','technical_reviewer'].includes(app.me.role)){
    app.content.replaceChildren(heading('Relationship review access required','Only source administrators and technical reviewers can manage these records.'));return;
  }
  let disposed=false,proposalBusy=false,reviewBusy=false,historyBusy=false,reviewTicket=0,historyTicket=0;
  let status:Json|null=null,packet:Json|null=null,after:string|null=null,inspected=[false,false];
  const proposalMessage=el('div'),reviewMessage=el('div',{'aria-live':'polite'}),historyMessage=el('div');
  const queue=el('div'),record=el('div'),packetView=el('div'),bodies=el('div');
  const relationshipId=input('text',initialId),relation=select([['','Choose a relationship'],['cites','Cites'],['amends','Amends'],['supersedes','Supersedes'],['defines','Defines'],['illustrates','Illustrates'],['compares','Compares']]);
  const scope=textarea('', 'relationship-scope',4),proposalRef=input(),proposalHash=input();
  const decision=select([['','Choose a decision'],['approved','Approve'],['rejected','Reject'],['revoked','Revoke']]);
  const note=textarea('','relationship-review-note',4),reviewRef=input(),reviewHash=input(),expiry=input('datetime-local');
  const confirm=checkbox('I performed the actual independent review and retained supporting evidence.');
  const source=citationPicker(app,'From',()=>proposalControls()),target=citationPicker(app,'To',()=>proposalControls());
  const submit=button('Submit relationship proposal',()=>propose());
  const load=button('Load relationship',()=>loadRecord(),'secondary');
  const inspect=button('Inspect both bound passages',()=>inspectRecord(),'secondary');
  const save=button('Record independent decision',()=>review());
  const refresh=button('Refresh relationship list',()=>loadHistory(true),'secondary');
  const more=button('Next relationship records',()=>loadHistory(false),'secondary');
  app.cleanup=()=>{disposed=true;reviewTicket++;historyTicket++;source.dispose();target.dispose();};
  const message=(host:HTMLElement,e:unknown)=>host.replaceChildren(notice((e as Error).message,'error'));
  const hash=(value:string)=>/^[a-f0-9]{64}$/.test(value);
  const ref=(value:string)=>/^ev_[A-Za-z0-9_-]{1,120}$/.test(value);
  function proposalControls(){submit.disabled=proposalBusy||reviewBusy||!source.get()||!target.get();
    source.lock(proposalBusy||reviewBusy);target.lock(proposalBusy||reviewBusy);
    for(const element of [relation,scope,proposalRef,proposalHash])element.disabled=proposalBusy;
  }
  function reviewControls(){
    const busy=reviewBusy||proposalBusy;
    relationshipId.disabled=busy;load.disabled=busy;inspect.disabled=busy||!packet;
    for(const b of queue.querySelectorAll('button'))b.disabled=busy;
    proposalControls();
    const eligible=app.me?.role==='technical_reviewer'&&status&&status.created_by!==app.me.id;
    for(const element of [decision,note,reviewRef,reviewHash,expiry,confirm.input])element.disabled=busy||!eligible;
    save.disabled=busy||!eligible||!decision.value||!confirm.input.checked||(decision.value==='approved'&&(!packet||!inspected.every(Boolean)));
  }
  function invalidate(){reviewTicket++;status=null;packet=null;inspected=[false,false];record.replaceChildren();packetView.replaceChildren();bodies.replaceChildren();confirm.input.checked=false;reviewControls();}
  relationshipId.oninput=()=>{invalidate();reviewMessage.replaceChildren();};
  decision.onchange=reviewControls;confirm.input.onchange=reviewControls;
  function showStatus(){
    if(!status)return;
    record.replaceChildren(card('Relationship status',el('p',{class:'review-hash'},status.id),
      el('p',{},`${status.relation} · Decision: ${status.decision} · Sequence ${status.sequence}`),
      notice(status.current?'The relationship review is current. This does not approve Agent use or claim support.':'The relationship is not currently eligible for public navigation.','warning'),
      el('p',{class:'review-hash'},`${status.source_id} → ${status.target_id}`),
      status.created_by===app.me?.id?notice('You proposed this relationship. Another technical reviewer must record its decision.','warning'):null));
  }
  async function loadRecord(allowProposal=false){
    if(reviewBusy||(proposalBusy&&!allowProposal))return;const id=relationshipId.value.trim();if(!id){message(reviewMessage,new Error('Enter a relationship ID.'));return;}
    invalidate();reviewBusy=true;reviewControls();const current=++reviewTicket;reviewMessage.replaceChildren(notice('Loading relationship status and review packet…'));
    try{
      const result=await api('/editorial/relationships/'+encodeURIComponent(id)+'/status');if(disposed||current!==reviewTicket)return;
      status=result;showStatus();
      try{
        const result=await api('/editorial/relationships/'+encodeURIComponent(id));if(disposed||current!==reviewTicket)return;
        if(result.revision!==status!.revision||result.sequence!==status!.sequence)throw new Error('The relationship changed while loading. Reload before deciding.');
        packet=result;
        packetView.replaceChildren(card('Bound proposal',el('p',{},result.proposal.scope),
          el('p',{class:'review-hash'},'Proposal evidence reference: '+result.proposal.evidence_ref),
          el('p',{class:'review-hash'},'Proposal evidence SHA-256: '+result.proposal.evidence_sha256),
          ...['source','target'].map(key=>el('div',{},el('h3',{},key==='source'?'From passage':'To passage'),el('p',{class:'review-hash'},result.proposal[key].locator),el('p',{class:'review-hash'},'Passage SHA-256: '+result.proposal[key].passage_text_sha256))),
          sourceNotices(result.source_attributions)),card('Decision history',...result.reviews.map((r:Json)=>el('details',{},el('summary',{},`${r.payload.decision} · ${r.payload.reviewer_id} · expires ${dateText(r.payload.expires_at)}`),el('p',{},r.payload.review_note),el('p',{class:'review-hash'},r.payload.evidence_ref),el('p',{class:'review-hash'},'Record SHA-256: '+r.payload_sha256))),result.reviews.length?null:el('p',{},'No decisions recorded.')));
        reviewMessage.replaceChildren();
      }catch(e){if(!disposed&&current===reviewTicket){packet=null;message(reviewMessage,new Error('The text review packet is unavailable. '+(e as Error).message+' Metadata remains available for rejection or revocation.'));}}
    }catch(e){if(!disposed&&current===reviewTicket){invalidate();message(reviewMessage,e);}}
    finally{reviewBusy=false;if(!disposed)reviewControls();}
  }
  async function inspectRecord(){
    if(reviewBusy||proposalBusy||!packet)return;reviewBusy=true;reviewControls();const current=++reviewTicket,snapshot=packet;
    inspected=[false,false];bodies.replaceChildren();reviewMessage.replaceChildren(notice('Resolving both exact passages…'));
    try{
      const results=[];
      for(const key of ['source','target']){
        const c=snapshot.proposal[key];results.push(await api('/sources/'+encodeURIComponent(c.source_id)+'/passages/resolve','POST',{
          expected_revision:c.revision,locator:c.locator,character_start:c.character_start,character_end:c.character_end,passage_text_sha256:c.passage_text_sha256}));
      }
      if(disposed||current!==reviewTicket)return;
      bodies.replaceChildren(...results.map((r,i)=>card(i===0?'From passage text':'To passage text',el('p',{class:'review-hash'},r.citation.locator),el('pre',{class:'source-passage-text'},r.text),sourceNotices(r.source_attributions))));
      inspected=[true,true];reviewMessage.replaceChildren(notice('Both exact passages loaded. Reading them does not perform an independent professional review.'));
    }catch(e){if(!disposed&&current===reviewTicket){packet=null;packetView.replaceChildren();message(reviewMessage,e);}}
    finally{reviewBusy=false;if(!disposed)reviewControls();}
  }
  async function propose(){
    if(proposalBusy||reviewBusy)return;const a=source.get(),b=target.get();
    if(!a||!b||!relation.value||a.source_id===b.source_id||scope.value.trim().length<20||!ref(proposalRef.value)||!hash(proposalHash.value)){
      message(proposalMessage,new Error('Inspect two different source passages, choose a relationship, and provide a scope of at least 20 characters plus a valid evidence reference and SHA-256.'));return;
    }
    proposalBusy=true;reviewControls();
    try{
      const result=await api('/editorial/relationships','POST',{source:a,target:b,relation:relation.value,scope:scope.value,evidence_ref:proposalRef.value,evidence_sha256:proposalHash.value});
      if(disposed)return;proposalMessage.replaceChildren(notice('Proposal saved. It has not been independently approved.'),link(app,'Open saved relationship','/authority-review/'+result.id));
      relationshipId.value=result.id;await loadRecord(true);await loadHistory(true);
    }catch(e){if(!disposed){source.clear();target.clear();message(proposalMessage,e);}}
    finally{proposalBusy=false;if(!disposed){reviewControls();}}
  }
  async function review(){
    if(reviewBusy||!status||save.disabled)return;
    const expires=Math.floor(new Date(expiry.value).getTime()/1000);
    if(!Number.isFinite(expires)||expires<=0||!ref(reviewRef.value)||!hash(reviewHash.value)||note.value.trim().length<20){message(reviewMessage,new Error('Provide a review note of at least 20 characters, an evidence reference, SHA-256 and explicit expiry.'));return;}
    reviewBusy=true;reviewControls();const current=++reviewTicket,snapshot=status;
    try{
      await api('/editorial/relationships/'+encodeURIComponent(snapshot.id)+'/review','POST',{
        expected_revision:snapshot.revision,expected_sequence:snapshot.sequence,decision:decision.value,review_note:note.value,
        evidence_ref:reviewRef.value,evidence_sha256:reviewHash.value,expires_at:expires,confirm_actual_review_performed:confirm.input.checked});
      if(disposed||current!==reviewTicket)return;
      invalidate();reviewMessage.replaceChildren(notice('Decision recorded. Reload the relationship to inspect its new sequence and history.'));await loadHistory(true);
    }catch(e){if(!disposed&&current===reviewTicket){invalidate();message(reviewMessage,new Error((e as Error).message+' Reload the relationship before another decision.'));}}
    finally{reviewBusy=false;if(!disposed)reviewControls();}
  }
  async function loadHistory(reset=false){
    if(historyBusy)return;historyBusy=true;refresh.disabled=true;more.disabled=true;const current=++historyTicket;
    if(reset)after=null;historyMessage.replaceChildren();
    try{
      const result=await api('/editorial/relationships?after='+encodeURIComponent(after||''));if(disposed||current!==historyTicket)return;
      after=result.next_after;queue.replaceChildren(table(['Relationship','Direction','Decision','Sequence','Open'],result.items.map((r:Json)=>[
        r.relation,el('span',{class:'review-hash'},`${r.source_id} → ${r.target_id}`),r.decision,r.sequence,
        button('Inspect '+r.id,()=>{if(reviewBusy||proposalBusy)return;relationshipId.value=r.id;void loadRecord();},'secondary')])));
      if(!result.items.length)queue.replaceChildren(notice('No relationship records in this page.'));
    }catch(e){if(!disposed&&current===historyTicket)message(historyMessage,e);}
    finally{historyBusy=false;if(!disposed){refresh.disabled=false;more.disabled=after===null;reviewControls();}}
  }
  app.content.replaceChildren(heading('Authority relationship review','Bind exact passages, explain the relationship, and retain an independent decision.'),
    notice('No source rights, accounting applicability or Agent admission is granted by this screen. Evidence references point to your approved restricted records; do not paste credentials or private legal advice.'),
    el('details',{class:'card',open:!initialId},el('summary',{},'Propose a relationship'),el('div',{class:'grid two'},source.root,target.root),field('Relationship direction: From → To',relation),field('Scope and qualifications',scope),
      field('Proposal evidence reference',proposalRef,'Use an approved ev_ reference.'),field('Proposal evidence SHA-256',proposalHash),submit,proposalMessage),
    card('Inspect and decide',field('Relationship ID',relationshipId),load,reviewMessage,record,packetView,inspect,bodies,
      app.me.role==='technical_reviewer'?null:notice('Only an independent technical reviewer can record a decision.'),
      field('Review decision',decision),field('Review note',note),field('Review evidence reference',reviewRef),field('Review evidence SHA-256',reviewHash),field('Review expiry (local time)',expiry),confirm.element,save),
    card('Relationship records',refresh,more,historyMessage,queue));
  proposalControls();reviewControls();await loadHistory(true);if(initialId)await loadRecord();
}
