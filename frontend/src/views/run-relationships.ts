import {api} from '../api.js';
import {sourceNotices} from '../source-notices.js';
import {el,button,card,notice,badge,dateText,link} from '../ui.js';
import type {App,Json} from '../types.js';

const labels:Record<string,string>={cites:'Cites',amends:'Amends',supersedes:'Supersedes',defines:'Defines',illustrates:'Illustrates',compares:'Compares'};

export function runRelationships(app:App,runId:string){
  let disposed=false,pending=false;
  const body=el('div',{'aria-live':'polite'});
  const load=button('Inspect saved relationships',async()=>{
    if(disposed||pending)return;
    pending=true;load.disabled=true;
    body.replaceChildren(notice('Checking current permissions and saved relationship versions…'));
    try{
      const result=await api('/runs/'+encodeURIComponent(runId)+'/relationships');
      if(disposed)return;
      const passages=(item:Json,name:'source'|'target')=>{
        const p=item.passages[name],c=p.citation;
        return el('details',{},el('summary',{},`${name==='source'?'From':'To'}: ${p.title}`),
          badge(p.source_kind.replaceAll('_',' ')),badge(p.access.replaceAll('_',' ')),
          el('p',{class:'review-hash'},c.locator),el('pre',{class:'source-passage-text'},p.text),
          el('details',{},el('summary',{},'Exact saved citation'),
            el('p',{},'Source version: '+p.source_version),el('p',{class:'review-hash'},'Evidence ID: '+p.evidence_id),
            el('p',{},c.offset_convention+`: ${c.character_start}–${c.character_end}`),
            el('p',{class:'review-hash'},'Source revision: '+c.revision),
            el('p',{class:'review-hash'},'Source SHA-256: '+c.source_text_sha256),
            el('p',{class:'review-hash'},'Passage SHA-256: '+c.passage_text_sha256)),
          link(app,'Open current source record','/sources/'+encodeURIComponent(c.source_id)));
      };
      body.replaceChildren(notice(result.coverage_note),
        ...result.items.map((item:Json)=>{const r=item.relationship;return el('article',{class:'relationship-inspection'},
          el('h3',{},labels[r.relation]||r.relation),el('p',{},r.scope),passages(item,'source'),passages(item,'target'),
          el('details',{},el('summary',{},'Relationship review version'),
            el('p',{},`Decision sequence ${r.review_sequence} · expires ${dateText(r.review_expires_at)}`),
            el('p',{class:'review-hash'},'Relationship ID: '+r.relationship_id),
            el('p',{class:'review-hash'},'Revision: '+r.revision),
            el('p',{class:'review-hash'},'Review ID: '+r.review_id),
            el('p',{class:'review-hash'},'Review SHA-256: '+r.review_sha256)));}),
        ...(result.items.length?[]:[el('p',{},'No relationship snapshots were saved for this run.')]),
        el('details',{},el('summary',{},'Selection limits and version'),el('p',{},
          `Up to ${result.selection_limits.lexical_seeds} lexical seeds, ${result.selection_limits.incident_edges_per_seed} incident edges per seed, ${result.selection_limits.relationships} saved relationships and ${result.selection_limits.metadata_bytes} metadata bytes.`),
          el('p',{},'Selection version: '+result.version)),sourceNotices(result.source_attributions));
      load.textContent='Recheck saved relationships';
    }catch(error){if(!disposed)body.replaceChildren(notice(error instanceof Error?error.message:'Saved relationship evidence is unavailable.','error'));}
    finally{pending=false;if(!disposed)load.disabled=false;}
  },'secondary');
  return {element:card('Saved source relationships',
    el('p',{},'Inspect the exact source pairs supplied to the Agent. A reviewed link does not establish claim support, automatic precedence or complete context.'),load,body),
    dispose:()=>{disposed=true;body.replaceChildren();}};
}
