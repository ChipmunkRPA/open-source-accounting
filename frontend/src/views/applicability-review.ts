import {api} from '../api.js';
import {el,button,field,notice,select,input,textarea,checkbox,modal,card} from '../ui.js';
import {sourceNotices} from '../source-notices.js';
import type {App,Json} from '../types.js';

export function applicabilityReview(app:App,source:Json,reload:()=>Promise<void>){
  const decision=select([['changes_requested','Request changes'],['approved','Approve applicability'],['rejected','Reject'],['revoked','Revoke prior review']]);
  const issued=input('date'),available=input('date'),start=input('date'),end=input('date'),expiry=input('datetime-local');
  const openEnded=checkbox('I verified that the effective interval has no known end date.');
  const frameworks=['US_GAAP','IFRS'].map(v=>({value:v,...checkbox(v.replaceAll('_',' '))}));
  const entities=['public','private','nonprofit'].map(v=>({value:v,...checkbox(v)}));
  const regimes=['PCAOB','AICPA','GAGAS','NONE'].map(v=>({value:v,...checkbox(v)}));
  const group=(label:string,items:typeof frameworks)=>el('fieldset',{},el('legend',{},label),...items.map(v=>v.element));
  const scope=textarea('', '',3),notes=textarea('', '',4),conditions=textarea('', '',3),evidence=input(),hash=input();
  const attestation=checkbox('I actually reviewed these dates, scope and conditions against the exact source revision.');
  const status=el('div'),history=el('div');
  const dialog=modal('Historical applicability · '+source.title,
    notice('Rights, parser review and technical approval are separate prerequisites. Recording dates does not grant Agent admission.'),
    el('p',{class:'review-hash'},'Source revision: '+source.review_revision),
    el('pre',{class:'review-text'},source.text??'Full source display is not currently permitted.'),sourceNotices(source.source_attributions),
    field('Decision',decision),
    el('div',{class:'grid two'},field('Issued date',issued),field('Publicly available date',available),field('Effective from',start),field('Effective through (inclusive)',end)),
    openEnded.element,group('Reviewed accounting frameworks',frameworks),group('Reviewed entity types',entities),group('Reviewed audit regimes (required for audit sources)',regimes),
    field('Unresolved conditions (one per line)',conditions,'Any condition withholds automated evidence until a case-specific review is available. Free-text early-adoption claims cannot override this gate.'),
    field('Review scope',scope),field('Private findings',notes),field('Private supporting-record reference',evidence,'Use the approved evidence reference, beginning ev_. Do not paste credentials or supporting documents.'),
    field('Supporting-record SHA-256',hash),field('Review expires at (your local time)',expiry),attestation.element,status);
  let saved=false;
  const submit=button('Record applicability decision',async()=>{
    if(saved)return;
    submit.disabled=true;
    try{
      if(!attestation.input.checked)throw new Error('Confirm actual applicability review before submitting.');
      const expires=new Date(expiry.value).getTime();
      if(!expiry.value||!Number.isFinite(expires)||expires<=Date.now())throw new Error('Choose a future review expiry.');
      const checked=(items:typeof frameworks)=>items.filter(v=>v.input.checked).map(v=>v.value);
      const result:Json=await api('/editorial/sources/'+encodeURIComponent(source.id)+'/applicability','POST',{
        expected_policy_version:source.policy_version,expected_review_revision:source.review_revision,
        decision:decision.value,issued_at:issued.value||null,publicly_available_at:available.value||null,
        effective_from:start.value||null,effective_to:end.value||null,confirm_open_ended:openEnded.input.checked,
        frameworks:checked(frameworks),entity_types:checked(entities),audit_regimes:checked(regimes),
        conditions:conditions.value.split('\n').map(v=>v.trim()).filter(Boolean),review_scope:scope.value,review_note:notes.value,
        evidence_ref:evidence.value.trim(),evidence_sha256:hash.value.trim(),expires_at:Math.floor(expires/1000),confirm_actual_applicability_review:true});
      saved=true;
      if(!dialog.isConnected)return;
      dialog.querySelectorAll('input,textarea,select').forEach(n=>(n as HTMLInputElement).disabled=true);
      status.replaceChildren(notice('Decision saved. '+(result.requires_case_review?'Unresolved conditions withhold automated evidence. ':'')+'No Agent admission was granted.'),
        button('Reload content review',async()=>{dialog.close();try{await reload();}catch(e){app.showError(e);}},'secondary'));
    }catch(e){if(dialog.isConnected)status.replaceChildren(notice((e as Error).message,'error'));}
    finally{submit.disabled=saved;}
  },'secondary');
  const historyButton=button('Load applicability history',async()=>{
    historyButton.disabled=true;
    try{
      const data:Json=await api('/editorial/sources/'+encodeURIComponent(source.id)+'/applicability');
      if(!dialog.isConnected)return;
      history.replaceChildren(notice(data.current?'A current applicability record exists; case scope and other gates still apply.':'No current applicability approval.'),
        ...data.items.map((r:Json)=>card(r.payload.decision+' · '+new Date(r.created_at*1000).toLocaleString(),
          el('p',{},r.payload.review_scope),el('pre',{class:'review-text'},JSON.stringify(r.payload,null,2)),el('p',{class:'review-hash'},'Record SHA-256: '+r.payload_sha256))));
    }catch(e){if(dialog.isConnected)history.replaceChildren(notice((e as Error).message,'error'));}
    finally{historyButton.disabled=false;}
  },'quiet');
  dialog.append(submit,historyButton,history);
}
