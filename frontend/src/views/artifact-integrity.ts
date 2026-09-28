import {api} from '../api.js';
import {el,button,heading,notice,table,link,busy,textarea,field,checkbox} from '../ui.js';
import type {App,Json} from '../types.js';

export async function artifactIntegrityView(app:App){
  let offset=0,disposed=false,sequence=0;
  const list=el('div'),artifacts=el('div'),result=el('div'),status=el('div');
  app.cleanup=()=>{disposed=true;sequence++;};
  const verify=async(id:string,b:HTMLButtonElement)=>{
    busy(b,true);result.replaceChildren();status.replaceChildren();
    try{
      const r=await api('/admin/intake/artifacts/'+id+'/verify','POST');if(disposed)return;
      result.replaceChildren(el('h2',{},'Observed integrity'),notice(r.notice),
        el('p',{},'Artifact '+r.artifact_id+' · observed '+new Date(r.observed_at*1000).toLocaleString()),
        table(['Unit','Status','Expected SHA-256','Observed SHA-256'],[
          ['Raw bytes',r.raw.status,r.raw.expected_sha256,r.raw.observed_sha256||'Not available'],
          ...r.extractions.map((e:Json)=>['Extraction '+e.extraction_id+' · '+e.passage_count+' passages',e.status,e.expected_sha256,e.observed_sha256||'Not available'])]),
        el('p',{},'Raw bytes expected: '+r.raw.expected_bytes+' · observed: '+(r.raw.observed_bytes??'Not available')),
        el('p',{class:'review-hash'},'Observation SHA-256: '+r.observation_sha256),
        notice(r.work_on_hold?'This work is on hold: dependent output and model use are blocked. A successful check alone never releases a hold.':'No integrity hold is recorded for this work. Other review gates still apply.'));
      if(!r.work_on_hold&&r.raw.status==='verified'){
        for(const ex of r.extractions.filter((x:Json)=>x.status==='verified')){
          const confirm=checkbox('Create new unapproved passage versions for extraction '+ex.extraction_id+'. Keep prior evidence and reviews unchanged.');
          const restage=button('Create recovery passage revisions',async()=>{busy(restage,true);status.replaceChildren();try{
            if(!confirm.input.checked)throw new Error('Acknowledge that fresh reviews are required.');
            const state=await api('/admin/intake/extractions/'+ex.extraction_id+'/restage','POST',{
              expected_parent_policy_version:r.policy_version,expected_normalized_sha256:ex.expected_sha256,confirm_fresh_reviews_required:true});
            if(disposed)return;result.replaceChildren(notice(state.created+' new passage revisions created. No approvals or old evidence were restored.'),
              table(['New source','Prior source'],state.source_ids.map((sid:string,i:number)=>[sid,state.predecessor_source_ids[i]])));
          }catch(e){if(!disposed)status.replaceChildren(notice((e as Error).message,'error'));}finally{busy(restage,false);}},'secondary');
          result.append(confirm.element,restage);
        }
      }
      if(r.integrity_hold&&app.me?.role==='rights_approver'){
        const note=textarea(),confirm=checkbox('Reverify these files and release this artifact hold. Older evidence remains invalid and must be reviewed again.');
        const release=button('Reverify and release hold',async()=>{busy(release,true);status.replaceChildren();try{
          if(!confirm.input.checked)throw new Error('Confirm the recheck and stale-evidence condition.');
          const state=await api('/admin/intake/artifacts/'+id+'/release-hold','POST',{expected_policy_version:r.policy_version,note:note.value,confirm_reverification_and_stale_evidence:true});
          if(disposed)return;result.replaceChildren(notice('This artifact hold was released after rechecking. '+(state.work_on_hold?'Other holds still block this work.':'Old evidence was not restored; separate approvals and revised source bindings remain required.')));
        }catch(e){if(!disposed)status.replaceChildren(notice((e as Error).message,'error'));}finally{busy(release,false);}},'secondary');
        result.append(field('Operational restoration rationale',note),confirm.element,release);
      }
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
    notice('Verification reads the configured object store only when you select Verify stored bytes. A failure puts the entire work on hold for output and model use. It does not fetch publisher content, repair files, grant approval or verify accounting accuracy. GCS reads use the operator-configured project and bucket.'),status,list,artifacts,result);
  await load();
}
