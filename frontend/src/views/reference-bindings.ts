import {el,button,field,notice,select,checkbox} from '../ui.js';
import {sourceNotices} from '../source-notices.js';
import type {Json} from '../types.js';

type Binding={reference_id:string;source_id:string;review_revision:string;policy_version:number;locator:string};
type Row={node:HTMLElement;reference:string;choice:HTMLSelectElement;confirmed:HTMLInputElement};
const locator=(s:Json):string=>s.policy?.intake_locator||s.source_provenance?.locator||s.url||'';

export function referenceBindings(source:Json,sources:Json[]){
  const refs:string[]=source.policy.content_reference_ids||[];
  const candidates=sources.filter(s=>s.id!==source.id&&s.text&&locator(s));
  const rows:Row[]=[];
  const element=el('section',{'aria-label':'Exact source dependencies'},el('h3',{},'Exact source dependencies'),
    notice('Select staged evidence for each reference and inspect its exact text. A matching title or URL does not establish the citation relationship. All references need bindings before an original article can serve as Agent evidence.'),
    notice('No prior bindings are transferred automatically. Rights, technical review, historical applicability and inherited output limits remain separate gates.'));
  if(!refs.length)element.append(el('p',{},'This source has no listed editorial references.'));
  if(refs.length&&!candidates.length)element.append(notice('No other staged source with readable text and an exact locator is available. Record missing evidence as a change request; do not substitute a source link.','warning'));
  for(const ref of refs){
    const group=el('fieldset',{},el('legend',{},'Reference: '+ref));
    const slots=el('div');
    const add=()=>{
      if(rows.length>=200)throw new Error('At most 200 source bindings can be reviewed in one decision.');
      const choice=select([['','Choose exact staged evidence'],...candidates.map((s:Json):[string,string]=>[s.id,s.title+' · '+s.version+' · '+s.id.slice(0,8)])]);
      const confirmed=checkbox('I verified that this exact passage supports reference '+ref+'.');
      const details=el('div');
      const node=el('section',{class:'card'},field('Evidence for '+ref,choice),details,confirmed.element);
      const row={node,reference:ref,choice,confirmed:confirmed.input};rows.push(row);
      choice.addEventListener('change',()=>{
        confirmed.input.checked=false;
        const target=candidates.find(s=>s.id===choice.value);
        details.replaceChildren();
        if(target)details.append(el('p',{},'Edition: '+target.version+' · Locator: '+locator(target)),
          el('p',{class:'review-hash'},'Exact revision: '+target.review_revision),
          notice(target.technical_review_current?'Current technical approval; other admission gates still apply.':'No current technical approval; this binding alone cannot admit evidence.'),
          el('pre',{class:'review-text'},target.text),sourceNotices(target.source_attributions));
      });
      node.append(button('Remove evidence selection',()=>{rows.splice(rows.indexOf(row),1);node.remove();},'quiet'));
      slots.append(node);
    };
    const addStatus=el('div');
    group.append(slots,button('Add evidence for '+ref,()=>{try{add();addStatus.replaceChildren();}catch(e){addStatus.replaceChildren(notice((e as Error).message,'error'));}},'quiet'),addStatus);
    element.append(group);add();
  }
  return {element,collect():Binding[]{
    const selected=rows.filter(r=>r.choice.value);
    if(!selected.length)return []; // Technical-only decisions do not manufacture evidence admission.
    if(refs.some(ref=>!selected.some(r=>r.reference===ref)))throw new Error('Select evidence for every reference, or clear all selections to record technical review without evidence bindings.');
    const unique=new Set<string>();
    return selected.map(row=>{
      if(!row.confirmed.checked)throw new Error('Confirm each selected reference relationship after inspecting its exact passage.');
      const target=candidates.find(s=>s.id===row.choice.value);
      if(!target)throw new Error('Reload the staged source list.');
      const key=row.reference+'\n'+target.id;
      if(unique.has(key))throw new Error('Remove duplicate evidence selections for the same reference.');
      unique.add(key);
      return {reference_id:row.reference,source_id:target.id,review_revision:target.review_revision,policy_version:target.policy_version,locator:locator(target)};
    });
  }};
}
