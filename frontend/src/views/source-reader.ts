import {api,APIError} from '../api.js';
import {sourceNotices} from '../source-notices.js';
import {el,button,link,heading,notice,badge,card,textarea,field} from '../ui.js';
import type {App,Json} from '../types.js';

export async function sourceReaderView(app:App,id:string){
  let disposed=false,busy=false,ticket=0,revision:string|null=null,next:number|null=null;
  let starts:number[]=[0],pageIndex=0;
  const base='/sources/'+encodeURIComponent(id),info=el('div'),message=el('div',{'aria-live':'polite'});
  const passages=el('div'),reading=el('div'),pageLabel=el('p',{class:'muted'});
  const previous=button('Previous passages',()=>loadPage(pageIndex-1),'secondary');
  const following=button('Next passages',()=>loadPage(pageIndex+1),'secondary');
  const reload=button('Reload source',()=>initialize(),'secondary');
  app.cleanup=()=>{disposed=true;ticket++;};
  function controls(){
    previous.disabled=busy||pageIndex===0;following.disabled=busy||next===null;reload.disabled=busy;
    for(const b of passages.querySelectorAll('button'))b.disabled=busy;
  }
  function clear(){passages.replaceChildren();reading.replaceChildren();next=null;pageLabel.textContent='';}
  function failed(e:unknown){
    clear();info.replaceChildren();revision=null;starts=[0];pageIndex=0;
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
  async function initialize(){
    if(busy)return;busy=true;controls();clear();info.replaceChildren();revision=null;starts=[0];pageIndex=0;
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
      await loadPage(0,true);
    }catch(e){if(!disposed&&request===ticket)failed(e);}
    finally{busy=false;if(!disposed)controls();}
  }
  app.content.replaceChildren(heading('Read an exact source passage.','Public reading is free. Source rights and accounting support are separate.'),
    link(app,'← Source directory','/sources'),
    notice('A matching citation confirms passage identity. It does not establish support for a claim, complete source coverage, reporting-period applicability or Agent admission.'),
    info,el('div',{class:'actions'},reload,previous,following),pageLabel,message,reading,passages);
  await initialize();
}
