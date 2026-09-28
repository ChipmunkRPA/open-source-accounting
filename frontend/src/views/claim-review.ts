import {api,download} from '../api.js';
import {sourceNotices} from '../source-notices.js';
import {el,button,heading,link,notice,card,input,textarea,select,field,checkbox,dateText} from '../ui.js';
import type {App,Json} from '../types.js';

export async function claimReviewView(app:App,runId='',claimId=''){
  let disposed=false,pending=false,ticket=0,status:Json|null=null,packet:Json|null=null,next:number|null=null;
  let assessments:{id:string;choice:HTMLSelectElement;reason:HTMLTextAreaElement;read:HTMLInputElement}[]=[];
  const run=input('text',runId),claim=input('text',claimId);
  run.maxLength=36;claim.maxLength=80;
  const message=el('div',{'aria-live':'polite'}),state=el('div'),history=el('div'),evidence=el('div');
  const decision=select([['','Choose a decision'],['supported','Supported'],['contradicted','Contradicted'],['unresolved','Unresolved'],['revoked','Revoke the latest decision']]);
  const note=textarea('', '',4),competence=textarea('', '',3),ref=input(),hash=input(),expiry=input('datetime-local');
  note.maxLength=4000;competence.maxLength=2000;ref.maxLength=123;hash.maxLength=64;
  const actual=checkbox('I performed this actual human review or revocation and retained its supporting records.');
  const independent=checkbox('I have the competence for this scope and am independent of the run and cited input authors.');
  const load=button('Load claim status',()=>loadStatus(),'secondary');
  const inspect=button('Inspect exact claim and passages',()=>inspectPacket(),'secondary');
  const exportPacket=button('Download exact review packet · JSON',()=>exportCurrent(),'secondary');
  const more=button('Earlier review records',()=>loadHistory(),'secondary');
  const save=button('Record human decision',()=>submit());
  const controls=[decision,note,competence,ref,hash,expiry,actual.input,independent.input];
  app.cleanup=()=>{disposed=true;ticket++;packet=null;assessments=[];evidence.replaceChildren();};
  const base=()=>'/runs/'+encodeURIComponent(run.value.trim())+'/claims/'+encodeURIComponent(claim.value.trim());
  const resetAttestations=()=>{actual.input.checked=false;independent.input.checked=false;};
  function update(){
    const eligible=app.me?.role==='technical_reviewer'&&status!==null;
    run.disabled=claim.disabled=load.disabled=pending;
    inspect.disabled=pending||!status;exportPacket.disabled=pending||!packet;more.disabled=pending||next===null;
    for(const c of controls)c.disabled=pending||!eligible;
    expiry.disabled=pending||!eligible||decision.value==='revoked';
    for(const a of assessments)for(const c of [a.choice,a.reason,a.read])c.disabled=pending||!eligible||decision.value==='revoked';
    save.disabled=pending||!eligible||!decision.value||!actual.input.checked||!independent.input.checked||
      (decision.value==='revoked'?!status?.record_revision:!packet||assessments.some(a=>!a.read.checked||!a.choice.value));
  }
  function clearPacket(){packet=null;assessments=[];evidence.replaceChildren();resetAttestations();}
  function invalidate(){ticket++;status=null;next=null;clearPacket();state.replaceChildren();history.replaceChildren();decision.value='';note.value=competence.value=ref.value=hash.value=expiry.value='';update();}
  for(const i of [run,claim])i.oninput=()=>{invalidate();message.replaceChildren();};
  for(const c of [decision,note,competence,ref,hash,expiry])c.addEventListener('input',()=>{resetAttestations();update();});
  actual.input.onchange=independent.input.onchange=update;
  const error=(e:unknown)=>message.replaceChildren(notice(e instanceof Error?e.message:'Claim review unavailable.','error'));
  function showStatus(){
    if(!status)return;
    state.replaceChildren(card('Current review status',el('p',{},`Decision: ${status.decision.replaceAll('_',' ')} · Sequence ${status.sequence}`),
      notice(status.current?'This assessment is current for its bound claim and evidence. It does not approve the whole deliverable.':'No current human assessment applies to the available claim and evidence.','warning'),
      el('p',{},status.reviewer_id?'Recorded reviewer: '+status.reviewer_id:'No valid reviewer record'),
      el('p',{class:'review-hash'},'Current revision: '+(status.revision||'Unavailable')),
      el('p',{class:'review-hash'},'Last reviewed revision: '+(status.record_revision||'None')),
      link(app,'Return to saved result','/runs/'+encodeURIComponent(run.value.trim()))));
  }
  function historyRows(items:Json[]){
    for(const r of items)history.append(el('article',{class:'claim'},el('p',{},`Sequence ${r.sequence} · ${dateText(r.created_at)}`),
      el('p',{},r.integrity_valid?'Record integrity and assigned reviewer scope checks pass; this is not a current-support judgment.':'Record integrity or reviewer scope no longer passes.'),
      el('p',{class:'review-hash'},'Bound revision: '+r.revision)));
  }
  async function loadStatus(){
    if(pending||!run.value.trim()||!claim.value.trim())return;
    invalidate();pending=true;update();const id=++ticket;
    message.replaceChildren(notice('Checking workspace access and review status…'));
    try{
      const result=await api(base()+'/reviews');if(disposed||id!==ticket)return;
      status=result.status;next=result.next_before;showStatus();historyRows(result.items);
      if(!result.items.length)history.append(el('p',{},'No human decisions recorded for this claim.'));
      message.replaceChildren(notice('Inspect the exact packet before a new assessment. Metadata-only revocation remains available when a packet cannot be read.'));
    }catch(e){if(!disposed&&id===ticket)error(e);}
    finally{pending=false;if(!disposed)update();}
  }
  async function loadHistory(){
    if(pending||next===null)return;pending=true;update();const id=++ticket;
    try{
      const result=await api(base()+'/reviews?before='+next);if(disposed||id!==ticket)return;
      if(result.status.sequence!==status?.sequence){invalidate();throw new Error('The review sequence changed. Reload status before continuing.');}
      next=result.next_before;historyRows(result.items);
    }catch(e){if(!disposed)error(e);}
    finally{pending=false;if(!disposed)update();}
  }
  async function inspectPacket(){
    if(pending||!status)return;clearPacket();pending=true;update();const id=++ticket;
    message.replaceChildren(notice('Checking permissions and loading the exact claim packet…'));
    try{
      const result=await api(base()+'/review-packet');if(disposed||id!==ticket)return;
      if(result.status.sequence!==status.sequence){invalidate();throw new Error('The review changed. Reload status and inspect again.');}
      packet=result;status=result.status;showStatus();
      evidence.append(card('Exact claim',el('p',{},result.binding.claim.text),el('p',{},'Basis: '+result.binding.claim.basis),
        notice(result.notice),el('p',{class:'review-hash'},'Packet revision: '+result.revision)));
      assessments=result.binding.passages.map((p:Json,index:number)=>{
        const choice=select([['','Choose support relationship'],['supports','Supports'],['contradicts','Contradicts'],['context_only','Context only'],['unresolved','Unresolved']]);
        const reason=textarea('','',3);reason.maxLength=2000;
        const read=checkbox('I reviewed this exact passage and its applicability to the claim.');
        for(const c of [choice,reason,read.input])c.addEventListener('input',()=>{resetAttestations();update();});
        evidence.append(card(`Passage ${index+1}: ${p.title}`,el('p',{},`${p.source_kind} · ${p.access}`),
          el('p',{class:'review-hash'},p.locator),el('pre',{class:'source-passage-text'},p.text),
          el('details',{},el('summary',{},'Exact passage version and provenance'),
            el('p',{class:'review-hash'},'Evidence ID: '+p.evidence_id),el('p',{},'Source version: '+(p.source_version||'Private document')),
            el('p',{class:'review-hash'},'Passage SHA-256: '+p.text_sha256),
            el('p',{class:'review-hash'},'Source revision: '+(p.source_revision||p.document_checksum)),
            el('pre',{class:'source-passage-text'},JSON.stringify(p.extraction_context,null,2))),
          read.element,field(`Passage ${index+1} relationship`,choice),field(`Passage ${index+1} rationale`,reason)));
        return {id:p.evidence_id,choice,reason,read:read.input};
      });
      if(!assessments.length)evidence.append(notice('No cited passages. A supported or contradicted decision cannot be recorded without supporting or contradictory evidence.','warning'));
      evidence.append(el('details',{},el('summary',{},'Bound run and relationship versions'),
        el('p',{},`Model ${result.binding.model_id} · Prompt ${result.binding.prompt_version||'Not recorded'}`),
        el('p',{class:'review-hash'},'Result SHA-256: '+result.binding.result_sha256),
        el('p',{class:'review-hash'},'Facts and context SHA-256: '+result.binding.context_sha256),
        el('pre',{class:'source-passage-text'},JSON.stringify(result.binding.relationship_snapshots,null,2))),sourceNotices(result.source_attributions));
      if(result.review)evidence.append(card('Current recorded human assessment',el('p',{},result.review.review_note),
        el('p',{},result.review.competence_scope),el('p',{},'Expires '+dateText(result.review.expires_at)),
        ...result.review.passages.map((p:Json)=>el('p',{class:'review-hash'},`${p.evidence_id} · ${p.relationship}: ${p.rationale}`))));
      message.replaceChildren();
    }catch(e){if(!disposed){clearPacket();if(status){status={...status,current:false,revision:null};showStatus();}error(e);}}
    finally{pending=false;if(!disposed)update();}
  }
  async function exportCurrent(){
    if(pending||!packet)return;pending=true;update();const id=++ticket;
    const params=new URLSearchParams({expected_revision:packet.revision,expected_sequence:String(packet.status.sequence)});
    try{
      await download(base()+'/review-packet/export?'+params,'claim-review.json');
      if(!disposed&&id===ticket)message.replaceChildren(notice('Review packet download started after fresh export-permission checks. Recheck the live record before relying on a saved copy.'));
    }catch(e){if(!disposed&&id===ticket){invalidate();error(new Error((e as Error).message+' Reload and inspect the packet before trying again.'));}}
    finally{pending=false;if(!disposed)update();}
  }
  async function submit(){
    if(pending||save.disabled||!status)return;
    const revoked=decision.value==='revoked';
    const expires=revoked?1:Math.floor(new Date(expiry.value).getTime()/1000);
    const passages=revoked?[]:assessments.map(a=>({evidence_id:a.id,relationship:a.choice.value,rationale:a.reason.value.trim()}));
    if(note.value.trim().length<20||competence.value.trim().length<20||!/^ev_[A-Za-z0-9_-]{1,120}$/.test(ref.value)||!(/^[a-f0-9]{64}$/.test(hash.value))||
       (!revoked&&(!Number.isFinite(expires)||expires<=Date.now()/1000||passages.some(p=>p.rationale.length<20)))){
      error(new Error('Complete the review note and competence scope (at least 20 characters), secure ev_ record reference, 64-character SHA-256, passage rationales and future expiry.'));return;
    }
    const relationships=passages.map(p=>p.relationship);
    if((decision.value==='supported'&&(!relationships.includes('supports')||relationships.includes('contradicts')||relationships.includes('unresolved')))||
       (decision.value==='contradicted'&&!relationships.includes('contradicts'))){
      error(new Error('A supported decision requires supporting evidence with no unresolved or contradictory assessments. A contradicted decision requires a contradictory passage.'));return;
    }
    const payload={expected_revision:revoked?status.record_revision:packet!.revision,expected_sequence:status.sequence,
      decision:decision.value,passages,review_note:note.value.trim(),competence_scope:competence.value.trim(),
      evidence_ref:ref.value,evidence_sha256:hash.value,expires_at:expires,
      confirm_actual_review_performed:true,confirm_competence_and_independence:true};
    pending=true;update();const id=++ticket;
    try{
      const result=await api(base()+'/reviews','POST',payload);if(disposed||id!==ticket)return;
      clearPacket();status=result;showStatus();history.replaceChildren();next=null;decision.value='';
      note.value=competence.value=ref.value=hash.value=expiry.value='';
      message.replaceChildren(notice('Human decision recorded. Reload status and inspect a fresh packet before another assessment.'));
    }catch(e){if(!disposed&&id===ticket){invalidate();error(new Error((e as Error).message+' Reload status and inspect again before submitting.'));}}
    finally{pending=false;if(!disposed)update();}
  }
  app.content.replaceChildren(heading('Claim review','Human judgments bound to exact saved evidence. Retained review does not require an Agent subscription.'),
    notice('Individual claim assessments do not certify the deliverable or grant source rights. Reviewer competence is attested, not independently verified by this application.'),
    card('Find a saved claim',field('Run ID',run),field('Claim ID',claim),el('div',{class:'actions'},load,inspect,exportPacket)),message,state,evidence,
    card('Record a human decision',app.me?.role==='technical_reviewer'?notice('Workspace review permission and independence are checked by the server.'):notice('An assigned technical reviewer with workspace review permission must record decisions.','warning'),
      field('Decision',decision),field('Review note',note),field('Competence and review scope',competence),
      field('Secure supporting-record reference',ref,'Use an approved ev_ record handle. Do not paste secrets or private advice into public issues.'),
      field('Supporting-record SHA-256',hash),field('Review expiry (local time)',expiry),actual.element,independent.element,save),
    card('Review history',el('p',{},'Metadata only; stale historical findings and source text are withheld.'),history,more));
  update();if(runId&&claimId)await loadStatus();
}
