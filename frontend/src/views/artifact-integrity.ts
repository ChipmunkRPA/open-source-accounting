import {api} from '../api.js';
import {el,button,heading,notice,table,link,busy} from '../ui.js';
import type {App,Json} from '../types.js';

export async function artifactIntegrityView(app:App){
  let offset=0,disposed=false,sequence=0;
  const list=el('div'),artifacts=el('div'),result=el('div'),status=el('div');
  app.cleanup=()=>{disposed=true;sequence++;};
  const verify=async(id:string,b:HTMLButtonElement)=>{
    busy(b,true);result.replaceChildren();
    try{
      const r=await api('/admin/intake/artifacts/'+id+'/verify','POST');if(disposed)return;
      result.replaceChildren(el('h2',{},'Observed integrity'),notice(r.notice),
        el('p',{},'Artifact '+r.artifact_id+' · observed '+new Date(r.observed_at*1000).toLocaleString()),
        table(['Unit','Status','Expected SHA-256','Observed SHA-256'],[
          ['Raw bytes',r.raw.status,r.raw.expected_sha256,r.raw.observed_sha256||'Not available'],
          ...r.extractions.map((e:Json)=>['Extraction '+e.extraction_id+' · '+e.passage_count+' passages',e.status,e.expected_sha256,e.observed_sha256||'Not available'])]),
        el('p',{},'Raw bytes expected: '+r.raw.expected_bytes+' · observed: '+(r.raw.observed_bytes??'Not available')),
        el('p',{class:'review-hash'},'Observation SHA-256: '+r.observation_sha256));
    }catch(e){if(!disposed)result.replaceChildren(notice((e as Error).message,'error'));}finally{busy(b,false);}
  };
  const inspect=async(id:string)=>{
    const ticket=++sequence;result.replaceChildren();
    try{
      const r=await api('/admin/intake/works/'+id);if(disposed||ticket!==sequence)return;
      artifacts.replaceChildren(el('h2',{},r.manifest.work_id+' · '+r.manifest.edition),
        ...r.artifacts.map((a:Json)=>{const b=button('Verify stored bytes',()=>verify(a.id,b),'secondary');
          return el('section',{class:'card'},el('p',{},'Artifact '+a.id+' · '+a.byte_count+' recorded bytes'),el('p',{class:'review-hash'},a.raw_sha256),b);}),
        ...(!r.artifacts.length?[notice('No acquired artifact records for this work.')]:[]));
    }catch(e){if(!disposed)status.replaceChildren(notice((e as Error).message,'error'));}
  };
  const load=async()=>{
    const ticket=++sequence;
    try{
      const r=await api('/admin/intake/works?offset='+offset);if(disposed||ticket!==sequence)return;
      const prev=button('Previous works',()=>{offset=Math.max(0,offset-100);void load();},'quiet');prev.disabled=offset===0;
      const next=button('Next works',()=>{offset=r.next_offset;void load();},'quiet');next.disabled=r.next_offset===null;
      list.replaceChildren(table(['Family','Work / edition','Inspect'],r.items.map((w:Json)=>[
        w.manifest.family_id,w.manifest.work_id+' / '+w.manifest.edition,button('Inspect artifacts',()=>inspect(w.id),'quiet')])),prev,next,
        ...(!r.items.length?[notice('No intake works registered. No content has been verified by this view.')]:[]));
    }catch(e){if(!disposed)status.replaceChildren(notice((e as Error).message,'error'));}
  };
  app.content.replaceChildren(heading('Stored artifact integrity','Explicit checks of existing private source objects.',link(app,'Source administration','/admin')),
    notice('Verification reads the configured object store only when you select Verify stored bytes. It does not fetch publisher content, repair files, grant approval or verify accounting accuracy. GCS reads use the operator-configured project and bucket.'),status,list,artifacts,result);
  await load();
}
