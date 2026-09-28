import {api,APIError} from '../api.js';
import {sourceNotices} from '../source-notices.js';
import {el,button,link,heading,notice,badge,card,textarea,field,dateText} from '../ui.js';
import type {App,Json} from '../types.js';

export async function sourceReaderView(app:App,id:string){
  let disposed=false,busy=false,ticket=0,revision:string|null=null,next:number|null=null;
  let starts:number[]=[0],pageIndex=0,hasReading=false,edgeAfter:string|null=null;
  const relationships=el('div');
  const base='/sources/'+encodeURIComponent(id),info=el('div'),message=el('div',{'aria-live':'polite'});
  const passages=el('div'),reading=el('div'),pageLabel=el('p',{class:'muted'});
  const previous=button('Previous passages',()=>loadPage(pageIndex-1),'secondary');
  const following=button('Next passages',()=>loadPage(pageIndex+1),'secondary');
  const reload=button('Reload source',()=>initialize(),'secondary');
  const loadRelationships=button('Load reviewed relationships',()=>loadLinks(),'secondary');
  app.cleanup=()=>{disposed=true;ticket++;};
  function controls(){
    loadRelationships.disabled=busy||!hasReading;
    previous.disabled=busy||pageIndex===0;following.disabled=busy||next===null;reload.disabled=busy;
    for(const b of passages.querySelectorAll('button'))b.disabled=busy;
  }
  function clear(){passages.replaceChildren();reading.replaceChildren();relationships.replaceChildren();edgeAfter=null;loadRelationships.textContent='Load reviewed relationships';next=null;pageLabel.textContent='';}
  function failed(e:unknown){
    clear();info.replaceChildren();hasReading=false;revision=null;starts=[0];pageIndex=0;
    const changed=e instanceof APIError&&e.status===409;
    message.replaceChildren(notice((e as Error).message+(changed?' Reload the source to inspect its current revision.':''),'error'));
  }
  function details(c:Json){
    return el('details',{},el('summary',{},'Citation details'),
      el('p',{},`Version: ${c.source_version||'Not recorded'} · ${c.source_kind}`),
      el('p',{},c.locator_kind==='retained_locator'?'Retained source locator':'Source record only; no page or section locator is recorded.'),
      el('p',{class:'review-hash'},'Locator: '+c.locator),
      el('p',{class:'muted'},'Character ranges refer to retained text, not original file bytes or printed-page positions.'),
      el('p',{class:'review-hash'},'Source revision: '+c.revision),
      el('p',{class:'review-hash'},'Source text SHA-256: '+c.source_text_sha256),
      el('p',{class:'review-hash'},'Passage SHA-256: '+c.passage_text_sha256));
  }
  async function read(c:Json){
    if(busy)return;busy=true;controls();const request=++ticket;
    reading.replaceChildren();message.replaceChildren(notice('Loading the exact passage…'));
    try{
      const result=await api(base+'/passages/resolve','POST',{expected_revision:c.revision,locator:c.locator,
        character_start:c.character_start,character_end:c.character_end,passage_text_sha256:c.passage_text_sha256});
      if(disposed||request!==ticket)return;
      const citation=textarea(`${result.citation.source_version||'Version not recorded'}\n${result.citation.locator}\nSource: ${id}\nRevision: ${result.citation.revision}\nPassage SHA-256: ${result.citation.passage_text_sha256}`,'selected-source-citation',5);
      citation.readOnly=true;
      const title=el('h2',{tabindex:-1},'Selected passage');
      reading.replaceChildren(el('section',{class:'card'},title,
        el('p',{class:'review-hash'},result.citation.locator),
        el('pre',{class:'source-passage-text'},result.text),sourceNotices(result.source_attributions),
        details(result.citation),field('Exact citation',citation),
        button('Select citation',()=>{citation.focus();citation.select();},'secondary')));
      message.replaceChildren();title.focus();
    }catch(e){if(!disposed&&request===ticket)failed(e);}
    finally{busy=false;if(!disposed)controls();}
  }
  async function loadPage(index:number,initial=false){
    if(busy&&!initial)return;
    const start=index<starts.length?starts[index]:next;
    if(start===null||index<0)return;
    busy=true;controls();const request=++ticket;
    reading.replaceChildren();passages.replaceChildren();message.replaceChildren(notice('Loading passage locations…'));
    try{
      const result=await api(base+`/passages?start=${start}&limit=10`);
      if(disposed||request!==ticket)return;
      const version=result.items[0]?.revision;
      if(!version||result.items.some((c:Json)=>c.revision!==version)||(revision!==null&&revision!==version))
        throw new APIError('REVISION_CONFLICT','The source changed between passage pages.',409);
      revision=version;starts[index]=start;pageIndex=index;next=result.next_start;
      pageLabel.textContent=`Page ${pageIndex+1} · ${result.retained_characters.toLocaleString()} retained characters`;
      passages.replaceChildren(...result.items.map((c:Json)=>card(`Characters ${c.character_start+1}–${c.character_end}`,
        el('p',{class:'review-hash'},c.source_locator),button(`Read characters ${c.character_start+1}–${c.character_end}`,()=>read(c),'secondary'),details(c))),sourceNotices(result.source_attributions));
      message.replaceChildren();
    }catch(e){if(!disposed&&request===ticket)failed(e);}
    finally{busy=false;if(!disposed)controls();}
  }
  async function loadLinks(){
    if(busy||!hasReading)return;busy=true;controls();const request=++ticket;
    relationships.replaceChildren();message.replaceChildren(notice('Checking reviewed relationships…'));
    try{
      const result=await api(base+'/relationships?limit=20&after='+encodeURIComponent(edgeAfter||''));
      if(disposed||request!==ticket)return;
      if(result.source_revision!==revision)throw new APIError('REVISION_CONFLICT','The source changed before relationship navigation.',409);
      relationships.replaceChildren(card('Reviewed relationships',
        notice('These links describe exact reviewed passage relationships. They do not transfer source authority, permissions or reporting-period applicability.'),
        ...result.items.map((edge:Json)=>{
          const target=edge.direction==='outgoing'?edge.target:edge.source;
          const labels:Record<string,[string,string]>={cites:['Cites another source','Cited by another source'],amends:['Amends another source','Amended by another source'],supersedes:['Supersedes another source','Superseded by another source'],defines:['Defines a term in another source','Term defined by another source'],illustrates:['Illustrates another source','Illustrated by another source'],compares:['Compares with another source','Compared by another source']};
          return el('article',{class:'source-row'},el('div',{},el('h3',{},labels[edge.relation]?.[edge.direction==='outgoing'?0:1]||edge.relation),
            el('p',{},`${edge.source_kind.replaceAll('_',' ')} → ${edge.target_kind.replaceAll('_',' ')}`),el('p',{},edge.scope),
            el('p',{class:'review-hash'},target.locator),
            el('p',{class:'muted'},'Relationship review expires '+dateText(edge.review_expires_at)),
            link(app,'Inspect linked source','/sources/'+encodeURIComponent(target.source_id),'button secondary')));
        }),result.items.length?null:el('p',{},'No current permitted reviewed links in this batch.'),
        el('p',{class:'muted'},`${result.observed} relationship ${result.observed===1?'record':'records'} checked. This is not a complete authority graph.`),sourceNotices(result.source_attributions)));
      edgeAfter=result.next_after;
      loadRelationships.textContent=edgeAfter?'Next relationship batch':'Reload reviewed relationships';message.replaceChildren();
    }catch(e){if(!disposed&&request===ticket)failed(e);}
    finally{busy=false;if(!disposed)controls();}
  }
  async function initialize(){
    if(busy)return;busy=true;controls();clear();info.replaceChildren();hasReading=false;revision=null;starts=[0];pageIndex=0;
    const request=++ticket;message.replaceChildren(notice('Loading source information…'));
    try{
      const s=await api(base+'/metadata');if(disposed||request!==ticket)return;
      info.replaceChildren(card(s.title,badge(s.access==='text_available'?'Reading permitted':'Reference only'),
        el('p',{},`${s.publisher} · ${s.version||'Version not recorded'} · ${s.kind}`),
        el('p',{},`Framework: ${s.framework} · Effective dates recorded: ${s.effective_from||'unknown'} to ${s.effective_to||'unknown'}`),
        s.attribution?el('p',{},s.attribution):null,
        typeof s.url==='string'&&/^https?:\/\//.test(s.url)?el('a',{href:s.url,target:'_blank',rel:'noopener noreferrer'},'Open publisher source ↗'):null));
      if(s.access!=='text_available'){
        message.replaceChildren(notice('Reference metadata only. Current rights do not permit reading retained text.','warning'));return;
      }
      hasReading=true;await loadPage(0,true);
    }catch(e){if(!disposed&&request===ticket)failed(e);}
    finally{busy=false;if(!disposed)controls();}
  }
  app.content.replaceChildren(heading('Read an exact source passage.','Public reading is free. Source rights and accounting support are separate.'),
    link(app,'← Source directory','/sources'),
    notice('A matching citation confirms passage identity. It does not establish support for a claim, complete source coverage, reporting-period applicability or Agent admission.'),
    info,el('div',{class:'actions'},reload,previous,following,loadRelationships),pageLabel,message,relationships,reading,passages);
  await initialize();
}
