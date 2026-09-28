import {api} from '../api.js';
import {el,button,field,heading,notice,input,table,link} from '../ui.js';
import type {App,Json} from '../types.js';

export async function dependencyReportView(app:App){
  const sourceId=input(),status=el('div'),body=el('div');let offset=0,filter='',sequence=0;
  const load=async()=>{
    const ticket=++sequence;status.replaceChildren(notice('Reading staged coverage…'));
    try{
      const params=new URLSearchParams({offset:String(offset),limit:'50'});if(filter)params.set('affected_by',filter);
      const data:Json=await api('/editorial/dependency-report?'+params);
      if(ticket!==sequence)return;
      status.replaceChildren();
      const flag=(value:boolean|null)=>value===null?'Not tracked here':value?'Current record':'No current record';
      const impact=(id:string)=>button('Show dependents',()=>{sourceId.value=id;filter=id;offset=0;void load();},'quiet');
      const previous=button('Previous',()=>{offset=Math.max(0,offset-50);void load();},'quiet');previous.disabled=offset===0;
      const next=button('Next',()=>{offset+=50;void load();},'quiet');next.disabled=offset+data.items.length>=data.total;
      body.replaceChildren(notice(data.notice),
        ...(data.graph_complete?[]:[notice('The dependency graph is incomplete. The affected list may omit items; resolve integrity/history errors before relying on it.','warning')]),
        el('p',{},`${data.staged_source_count} staged sources · ${data.total} matching rows · observed ${new Date(data.generated_at*1000).toLocaleString()}`),
        el('details',{},el('summary',{},'All source-family database counts'),
          table(['Family','Staged sources','Artifact records','Extraction records','Current technical records','Current applicability records','Originals missing bindings'],
            data.families.map((f:Json)=>[f.family_id,f.staged_sources||0,f.artifact_records||0,f.extraction_records||0,f.current_technical_records||0,f.current_applicability_records||0,f.original_sources_missing_bindings||0]))),
        filter?notice('Potential dependents of '+filter+'. Includes historical bindings and intake-parent relationships; this is not a determination of accounting impact.'):notice('Select Show dependents on a source, or enter its exact staged ID, to inspect potential impact.'),
        table(['Staged source','Family / edition','Recorded review states','Dependency issues','Impact'],data.items.map((s:Json)=>[
          el('div',{},el('strong',{},s.title),el('p',{class:'review-hash'},s.source_id),el('p',{},s.enabled?'Enabled':'Disabled')),
          s.family_id+' / '+s.edition,
          el('div',{},el('p',{},'Rights revision: '+flag(s.rights_revision_current)),el('p',{},'Technical: '+flag(s.technical_record_current)),el('p',{},'Applicability: '+flag(s.applicability_record_current)),el('p',{},'Parser: '+flag(s.parser_record_current))),
          el('div',{},el('p',{},s.binding_count+' bindings / '+s.reference_count+' references'),
            el('p',{},s.issues.length?s.issues.map((x:string)=>x.replaceAll('_',' ')).join('; '):'No listed metadata issue. Runtime gates still apply.'),
            ...(s.missing_reference_ids.length?[el('p',{},'Missing: '+s.missing_reference_ids.join(', '))]:[]),
            ...s.stale_bindings.map((b:Json)=>el('p',{},b.reference_id+': '+b.reason.replaceAll('_',' ')))),impact(s.source_id)])),
        el('div',{},previous,next),el('p',{class:'muted review-hash'},'Report SHA-256: '+data.report_sha256));
    }catch(e){if(ticket===sequence)status.replaceChildren(notice((e as Error).message,'error'));}
  };
  app.content.replaceChildren(heading('Dependency coverage','Recorded evidence states and potential source-change impact.',link(app,'Content review','/editorial')),
    field('Changed source ID',sourceId),button('Show source impact',()=>{filter=sourceId.value.trim();offset=0;void load();},'secondary'),
    button('Show all staged sources',()=>{sourceId.value='';filter='';offset=0;void load();},'quiet'),status,body);
  app.cleanup=()=>{sequence++;};
  await load();
}
