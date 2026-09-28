import {api} from '../api.js';
import {el,button,card,notice,table,link} from '../ui.js';
import type {App,Json} from '../types.js';

const labels:Record<string,string>={supported:'Supported',contradicted:'Contradicted',unresolved:'Unresolved',
  unreviewed:'Unreviewed',stale_revoked_or_invalid:'Stale, revoked or invalid'};

export function claimCoverage(app:App,runId:string){
  let disposed=false,pending=false;
  const body=el('div',{'aria-live':'polite'});
  const load=button('Check claim review coverage',async()=>{
    if(disposed||pending)return;
    pending=true;load.disabled=true;
    body.replaceChildren(notice('Checking current claim versions and reviewer access…'));
    try{
      const report=await api('/runs/'+encodeURIComponent(runId)+'/claim-review-coverage');
      if(disposed)return;
      body.replaceChildren(
        el('p',{},`${report.current_attested_decisions} of ${report.total_claims} claims have current reviewer attestations.`),
        notice('These counts are review coverage, not measured accuracy or professional approval. Reviewer credentials and review origin have not been independently verified.','warning'),
        table(['Current outcome','Claims'],Object.entries(labels).map(([key,label])=>[label,report.outcomes[key]])),
        el('p',{},'Verified professional adjudications: '+report.verified_professional_adjudications+'. Claim and numerical accuracy: not established.'),
        ...(report.items.length?[table(['Claim','Review status','Sequence'],report.items.map((item:Json)=>[
          link(app,item.claim_id,'/claim-review/'+encodeURIComponent(runId)+'/'+encodeURIComponent(item.claim_id)),
          labels[item.outcome]||item.outcome,item.sequence]))]:[el('p',{},'This retained result has no claims; review coverage has no denominator.')]),
        el('details',{},el('summary',{},'Report version and exact bindings'),
          el('p',{},'Report: '+report.version),el('p',{},'Model: '+(report.model_id||'Not recorded')),
          el('p',{},'Prompt: '+(report.prompt_version||'Not recorded')),
          el('p',{class:'review-hash'},'Result SHA-256: '+report.result_sha256),
          ...report.items.map((item:Json)=>el('div',{},el('h4',{},item.claim_id),
            el('p',{class:'review-hash'},'Current revision: '+(item.revision||'Unavailable')),
            el('p',{class:'review-hash'},'Reviewed revision: '+(item.record_revision||'No review')),
            el('p',{class:'review-hash'},'Record: '+(item.record_id||'No review'))))),
        el('p',{class:'muted'},'Snapshot checked '+new Date().toLocaleString()+'. Recheck after review or permission changes.'));
      load.textContent='Recheck claim review coverage';
    }catch(error){if(!disposed)body.replaceChildren(notice(error instanceof Error?error.message:'Claim review coverage is unavailable.','error'));}
    finally{pending=false;if(!disposed)load.disabled=false;}
  },'secondary');
  return {element:card('Claim review coverage',el('p',{},'Check current assessments and open the exact claim for review. This report contains no source passages or private review notes.'),load,body),
    dispose:()=>{disposed=true;body.replaceChildren();}};
}
