import {api} from '../api.js';
import {el,button,heading,notice,table,link,busy,input,textarea,select,field,checkbox} from '../ui.js';
import type {App,Json} from '../types.js';

type PartEditor={node:HTMLElement;value:()=>Json;ready:()=>boolean;refresh:()=>void;dispose:()=>void};
export async function editionsView(app:App){
  let disposed=false,dirty=false,offset=0,workOffset:number|null=0,request=0,expected=0,locked=false,saving=false,historyRequest=0;
  app.cleanup=()=>{disposed=true;request++;};
  const works=new Map<string,Json>();
  const families=(await api('/admin/intake/families')).items.filter((f:Json)=>f.id!=='PRIVATE_UPLOADS');
  if(disposed)return;
  const family=select(families.map((f:Json)=>[f.id,f.id+' · '+f.title])),collection=input(),edition=input(),coverage=textarea('', '',2),note=textarea('', '',3);
  const status=el('div'),history=el('div'),details=el('div'),partsBox=el('div'),combinedBox=el('div');
  const fields=el('fieldset'),form=el('form',{},fields);
  const parts:PartEditor[]=[];let combined:PartEditor|null=null;
  app.canLeave=()=>!dirty||window.confirm('Discard unsaved inventory changes?');
  app.cleanup=()=>{disposed=true;request++;for(const p of [...parts,...(combined?[combined]:[])])p.dispose();};
  form.addEventListener('input',()=>{dirty=true;});form.addEventListener('change',()=>{dirty=true;});form.onsubmit=e=>e.preventDefault();
  const error=(e:unknown)=>{if(!disposed){status.replaceChildren(notice((e as Error).message,'error'));app.showError(e);}};
  const partEditor=(initial:Json,isCombined=false):PartEditor=>{
    let dead=false,ticket=0,ready=true,binding:Json|null=null;
    const key=input('text',initial.key||''),label=input('text',initial.label||''),required=checkbox('Required component',initial.required!==false);
    key.required=label.required=true;key.pattern='[A-Za-z0-9][A-Za-z0-9_.-]{0,79}';key.maxLength=80;label.maxLength=300;
    const work=select([['','Unbound: still to be registered']]),artifact=select([['','Hash not selected']]),hash=input('text',initial.expected_raw_sha256||''),feedback=el('div');
    hash.pattern='[a-f0-9]{64}';hash.maxLength=64;hash.disabled=!initial.intake_work_id;
    let selected=initial.intake_work_id||'',selectedHash=initial.expected_raw_sha256||'';
    const refresh=()=>{const options:[string,string][]=[['','Unbound: still to be registered']];
      for(const [id,w] of works)if(w.manifest.family_id===family.value)options.push([id,w.manifest.work_id+' · '+w.manifest.edition]);
      if(selected&&!options.some(([id])=>id===selected))options.push([selected,'Bound work '+selected]);
      work.replaceChildren(...options.map(([v,t])=>el('option',{value:v},t)));work.value=selected;};
    const inspect=async()=>{const current=++ticket;selected=work.value;binding=null;ready=!selected;artifact.disabled=!!selected;
      hash.value=selectedHash;hash.disabled=!!selected;artifact.replaceChildren(el('option',{value:''},'Hash not selected'));feedback.replaceChildren();
      if(!selected){hash.disabled=true;return;}
      feedback.append(notice('Loading exact work and artifact identities…'));
      try{const w=await api('/admin/intake/works/'+selected);if(dead||disposed||current!==ticket)return;
        if(w.manifest.family_id!==family.value)throw new Error('This work belongs to another family. Select a matching work.');
        if(initial.intake_work_id===selected&&initial.manifest_sha256&&initial.manifest_sha256!==w.manifest_sha256)throw new Error('Bound manifest changed. Select a different registered work; this binding cannot be refreshed silently.');
        binding=w;works.set(w.id,w);refresh();
        const hashes=new Set<string>();for(const a of w.artifacts){hashes.add(a.raw_sha256);artifact.append(el('option',{value:a.raw_sha256},a.raw_sha256+' · '+a.byte_count+' bytes'));}
        if(selectedHash&&!hashes.has(selectedHash))artifact.append(el('option',{value:selectedHash},selectedHash+' · expected, not acquired'));
        artifact.value=selectedHash;artifact.disabled=false;hash.disabled=false;ready=true;
        feedback.replaceChildren(el('p',{class:'review-hash'},'Work manifest SHA-256: '+w.manifest_sha256),notice('Artifact selection records identity only. Rights and reviews remain separate.'));
      }catch(e){if(!dead&&!disposed&&current===ticket)feedback.replaceChildren(notice((e as Error).message,'error'));}};
    work.onchange=()=>{selectedHash='';void inspect();};artifact.onchange=()=>{selectedHash=artifact.value;hash.value=selectedHash;};hash.oninput=()=>{selectedHash=hash.value.trim();artifact.value='';};
    const node=el('section',{class:'card'},el('h3',{},isCombined?'Combined representation (excluded from component counts)':'Component'),field('Component key',key),field('Component label',label),
      ...(!isCombined?[required.element]:[]),field('Registered work and edition',work),field('Expected raw artifact',artifact,'Select an acquired hash, preserve a prior expected hash, or leave unknown.'),field('Expected SHA-256 (optional)',hash,'For a known future delivery, enter the exact expected hash. No artifact is counted until it arrives.'),feedback);
    const result:PartEditor={node,value:()=>({key:key.value.trim(),label:label.value.trim(),required:isCombined?true:required.input.checked,intake_work_id:binding?.id||null,manifest_sha256:binding?.manifest_sha256||null,expected_raw_sha256:selectedHash||null}),ready:()=>ready,refresh,dispose:()=>{dead=true;ticket++;}};
    node.append(button(isCombined?'Remove combined representation':'Remove component',()=>{result.dispose();node.remove();if(isCombined)combined=null;else parts.splice(parts.indexOf(result),1);dirty=true;},'quiet'));
    refresh();if(selected)void inspect();return result;
  };
  const add=(initial:Json={})=>{if(parts.length>=250){status.replaceChildren(notice('An inventory supports at most 250 components.','error'));return;}const p=partEditor(initial);parts.push(p);partsBox.append(p.node);};
  const reset=(manifest?:Json)=>{
    for(const p of [...parts,...(combined?[combined]:[])])p.dispose();parts.length=0;combined=null;partsBox.replaceChildren();combinedBox.replaceChildren();
    locked=!!manifest;expected=manifest?.revision||0;family.disabled=collection.disabled=edition.disabled=locked;
    if(manifest)family.value=manifest.family_id;
    collection.value=manifest?.collection_key||'';edition.value=manifest?.edition||'';coverage.value=manifest?.coverage_unit||'';note.value=manifest?.inventory_note||'';
    for(const p of manifest?.parts||[{key:'part-1'}])add(p);
    if(manifest?.combined){combined=partEditor(manifest.combined,true);combinedBox.append(combined.node);}
    dirty=false;save.textContent=locked?'Save new inventory revision':'Create inventory';
  };
  const inspect=async(id:string)=>{const current=++request;
    try{const r=await api('/admin/intake/editions/'+id);if(disposed||current!==request)return;
      const unit=(p:Json)=>el('section',{class:'card'},el('h3',{},p.label+' · '+p.key),el('p',{},p.receipt_state.replaceAll('_',' ')+' · '+(p.component_edition||'unbound')),
        el('p',{class:'review-hash'},'Expected raw SHA-256: '+(p.expected_raw_sha256||'Not declared')),
        p.unreconciled_raw_sha256.length?notice('New unselected deliveries: '+p.unreconciled_raw_sha256.join(', '),'error'):null,
        el('p',{},'Currently permitted operations: '+(Object.entries(p.rights_operations).filter(([,v])=>v).map(([k])=>k).join(', ')||'None reported')),
        table(['Extraction','Parser version','Passages','Parser decision'],p.extractions.map((e:Json)=>[e.id,e.parser_version,e.passage_count,e.parser_review])),
        p.extractions_truncated?notice('Only the first 10 extractions are displayed.'):null,
        notice('Current bytes, technical/applicability approval and indexing are not verified by this report.'));
      const revise=button('Prepare next revision',()=>{if(saving||(dirty&&!window.confirm('Replace unsaved inventory changes?')))return;reset(r.manifest);form.scrollIntoView({block:'start'});});revise.disabled=!r.current_revision;
      details.replaceChildren(el('h2',{},r.manifest.collection_key+' · '+r.manifest.edition+' · revision '+r.revision),
        notice(r.current_revision?'Current inventory revision':'Historical inventory — cannot claim current receipt completeness'),
        el('p',{},r.required_matching_receipts+' / '+r.required_parts+' required receipts match; '+r.optional_matching_receipts+' / '+r.optional_parts+' optional receipts match.'),
        notice(r.required_receipts_complete?'All declared required receipts match. This does not establish a complete or approved publication.':'Required receipt inventory is incomplete or superseded.'),
        notice(r.notice),el('p',{class:'review-hash'},'Inventory SHA-256: '+r.manifest_sha256),revise,
        ...(!r.current_revision?[button('Open current revision',()=>inspect(r.latest_id),'secondary')]:[]),...r.items.map(unit),
        ...(r.combined_receipt?[el('h2',{},'Separate combined representation'),unit(r.combined_receipt)]:[]));
    }catch(e){if(current===request)error(e);}};
  const load=async()=>{const current=++historyRequest;try{const r=await api('/admin/intake/editions?offset='+offset);if(disposed||current!==historyRequest)return;
    const prev=button('Previous inventories',()=>{offset=Math.max(0,offset-100);void load();},'quiet');prev.disabled=offset===0;
    const next=button('Next inventories',()=>{offset=r.next_offset;void load();},'quiet');next.disabled=r.next_offset===null;
    history.replaceChildren(el('h2',{},'Inventory history'),table(['Family','Collection / edition','Revision','Inspect'],r.items.map((r:Json)=>[r.family_id,r.collection_key+' / '+r.edition,r.revision,button('Inspect inventory',()=>inspect(r.id),'secondary')])),
      ...(!r.items.length?[notice('No inventories declared. No acquisition or approval is implied.')]:[]),prev,next);
  }catch(e){if(current===historyRequest)error(e);}};
  const more=button('Load more registered works',async()=>{if(workOffset===null)return;busy(more,true);try{
    const r=await api('/admin/intake/works?offset='+workOffset);if(disposed)return;for(const w of r.items)works.set(w.id,w);workOffset=r.next_offset;
    for(const p of [...parts,...(combined?[combined]:[])])p.refresh();
  }catch(e){error(e);}finally{busy(more,false);more.disabled=workOffset===null;}},'secondary');
  const save=button('Create inventory',async()=>{
    if(!form.reportValidity())return;
    const all=[...parts,...(combined?[combined]:[])];if(all.some(p=>!p.ready())){status.replaceChildren(notice('Resolve pending or failed work lookups before saving.','error'));return;}
    saving=true;busy(save,true);fields.disabled=true;status.replaceChildren();
    try{const r=await api('/admin/intake/editions','POST',{family_id:family.value,collection_key:collection.value.trim(),edition:edition.value.trim(),expected_revision:expected,coverage_unit:coverage.value.trim(),inventory_note:note.value.trim(),parts:parts.map(p=>p.value()),combined:combined?.value()||null});
      if(disposed)return;dirty=false;reset(r.manifest);status.replaceChildren(notice('Inventory revision '+r.revision+' saved. No acquisition or approval was performed.'));offset=0;await load();await inspect(r.id);
    }catch(e){error(e);}finally{saving=false;fields.disabled=false;busy(save,false);save.textContent=locked?'Save new inventory revision':'Create inventory';}});
  collection.required=edition.required=coverage.required=note.required=true;collection.pattern='[A-Za-z0-9][A-Za-z0-9_.-]{0,159}';collection.maxLength=160;edition.maxLength=80;coverage.minLength=5;coverage.maxLength=500;note.minLength=10;note.maxLength=2000;
  family.onchange=()=>{reset();dirty=true;};
  fields.append(field('Source family',family),field('Collection key',collection),field('Publisher edition',edition),field('Declared coverage',coverage),field('Inventory basis and limitations',note),more,partsBox,
    button('Add component',()=>{add();dirty=true;},'secondary'),combinedBox,button('Add combined representation',()=>{if(!combined){combined=partEditor({key:'combined'},true);combinedBox.append(combined.node);dirty=true;}},'secondary'),save);
  app.content.replaceChildren(heading('Multipart inventories','Track exact parts and receipt gaps without granting source approval.',link(app,'Source administration','/admin')),
    notice('Inventories describe the scope you declare. They do not establish publisher completeness, verify stored bytes, or approve accounting evidence.'),status,
    button('Start a new inventory',()=>{if(!saving&&(!dirty||window.confirm('Discard unsaved inventory changes?')))reset();},'secondary'),form,history,details);
  reset();more.click();await load();
}
