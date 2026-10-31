import {loadReaderEdition,readerSourceScope} from '../reader-edition.js';
import {annotationNotice} from '../annotation.js';
import {api,saveBlob} from '../api.js';
import {el,button,link,heading,badge,field,notice,card,select,input,empty,textarea,checkbox,modal} from '../ui.js';
import {markdown} from '../markdown.js';
import {sourceNotices} from '../source-notices.js';
import type {App,Json} from '../types.js';
function saveMarkdown(name:string,text:string){const url=URL.createObjectURL(new Blob([text],{type:'text/markdown;charset=utf-8'}));
  const a=el('a',{href:url,download:name});document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
const labels:Record<string,string>={guide:'Guides',case:'Worked cases',template:'Templates',playbook:'Agent playbooks',qa_set:'Study questions'};
type ListState={q:string;kind:string;topic:string;offset:number};
// History entries contain only an opaque token. Search text stays in memory for this app instance.
const listStates=new WeakMap<App,Map<string,ListState>>();
function savedState(app:App):ListState|undefined{
  const token=typeof history==='undefined'?undefined:history.state?.libraryListToken;
  return typeof token==='string'?listStates.get(app)?.get(token):undefined;
}
function newToken(app:App,state:ListState):string{
  let states=listStates.get(app);if(!states){states=new Map();listStates.set(app,states);}
  const token=crypto.randomUUID();states.set(token,{...state});return token;
}
function remember(app:App,state:ListState){
  let token=history.state?.libraryListToken;
  const states=listStates.get(app);
  if(typeof token!=='string'||!states?.has(token)){
    token=newToken(app,state);history.replaceState({...history.state,libraryListToken:token},'');
  }else states.set(token,{...state});
}
export async function openLibraryView(app:App,id?:string){
  if(id){
    let cancelled=false;app.cleanup=()=>{cancelled=true;};
    let item:Json;let reader;
    try{
      item=await api('/library/'+encodeURIComponent(id));if(cancelled)return;
      reader=await loadReaderEdition(item as {id:string;body:string;title:string;license:string;version?:string;sha256?:string});if(cancelled)return;
    }catch(error){if(cancelled)return;throw error;}
    const body=markdown(reader.body.replace(/^# [^\n]*\n+/,''));
    const toc=el('nav',{'aria-label':'Article sections',class:'library-toc'},el('h2',{},'In this article'),
      ...body.headings.map(h=>el('a',{href:'#'+h.id},h.text)));
    const sources=card('Source provenance',...item.sources.map((s:Json)=>el('div',{class:'library-reference'},
      el('a',{href:s.url,target:'_blank',rel:'noopener noreferrer'},s.title+' ↗'),
      el('p',{class:'muted'},readerSourceScope(s.review_scope)),badge(s.verification==='publisher_page_examined'?'Publisher page examined':'Reference only','neutral'))));
    const back=link(app,'← Open library','/library');
    const fromList=savedState(app);
    if(fromList)back.onclick=e=>{if(!e.ctrlKey&&!e.metaKey){e.preventDefault();app.navigate('/library',{libraryListToken:newToken(app,fromList)});}};
    app.content.replaceChildren(back,
      heading(item.title,item.summary,button('Download Markdown',()=>saveMarkdown(item.id+'.md',reader.body),'secondary')),
      annotationNotice(),
      el('div',{class:'row-actions'},badge('FREE ORIGINAL CONTENT','free'),badge('EDUCATIONAL DRAFT · UNREVIEWED','warning'),badge(item.license)),
      notice('This public editorial draft is not automatically available to research agents. Independent rights and technical approval are required before Agent use.','warning'),
      el('div',{class:'library-reading-layout'},el('div',{},body.element,sources),
        el('aside',{},toc,card('Use this material',el('p',{},item.license==='CC-BY-4.0'?'Read, download, and adapt this original content under CC BY 4.0. Preserve attribution and identify changes.':'This new annotation uses '+item.license+'. Read the linked content terms for permitted uses; prior CC BY grants remain unchanged.'),
          el('p',{class:'muted'},'Third-party standards are linked, not licensed or reproduced by this pack.'),
          link(app,'General AI chat · Free','/chat')))));
    return;
  }
  let cancelled=false,sequence=0,timer:number;
  app.cleanup=()=>{cancelled=true;clearTimeout(timer);sequence++;};
  let initial:Json;
  try{initial=await api('/library?limit=24');}catch(error){if(cancelled)return;throw error;}
  if(cancelled)return;
  const saved=savedState(app);
  const q=input('search',saved?.q||'','library-search');q.placeholder='Search issues, examples, or a task';q.maxLength=200;
  const kind=select([['','All content'],...initial.facets.kinds.map((k:string)=>[k,labels[k]||k])]),
    topic=select([['','All topics'],...initial.facets.topics.map((t:string)=>[t,t.replaceAll('_',' ')])]);
  if(saved&&initial.facets.kinds.includes(saved.kind))kind.value=saved.kind;
  if(saved&&initial.facets.topics.includes(saved.topic))topic.value=saved.topic;
  const grid=el('div',{class:'grid two library-grid'}),count=el('p',{class:'muted','aria-live':'polite'}),pager=el('div',{class:'row-actions'});
  let offset=saved?.offset||0;
  if(saved&&(kind.value!==saved.kind||topic.value!==saved.topic))offset=0;
  const state=():ListState=>({q:q.value,kind:kind.value,topic:topic.value,offset});
  function pending(){count.textContent='Loading results…';grid.replaceChildren();pager.replaceChildren();}
  function draw(result:Json){
    count.textContent=`${result.total} matching items · all ${initial.total} starter items are editorial drafts`;
    grid.replaceChildren(...result.items.map((item:Json)=>{const path='/library/'+encodeURIComponent(item.id);
      const read=link(app,'Read '+(item.kind==='case'?'case':'article')+' →',path);
      read.onclick=e=>{if(!e.ctrlKey&&!e.metaKey){e.preventDefault();app.navigate(path,{libraryListToken:newToken(app,state())});}};
      return card(item.title,
      annotationNotice(),
      el('div',{class:'row-actions'},badge(labels[item.kind]||item.kind),badge(item.topic),badge('DRAFT','warning')),
      el('p',{class:'muted'},item.summary),read);}));
    if(!result.items.length)grid.append(empty('No matching articles','Try fewer words or remove a filter.'));
    const previous=button('Previous',()=>{offset=Math.max(0,offset-24);remember(app,state());void refresh();},'secondary');previous.disabled=offset===0;
    const next=button('Next',()=>{offset+=24;remember(app,state());void refresh();},'secondary');next.disabled=offset+24>=result.total;
    pager.replaceChildren(previous,el('span',{},result.total?`${offset+1}–${Math.min(offset+24,result.total)} of ${result.total}`:'0 results'),next);
  }
  async function refresh(){const request=++sequence;pending();try{const result=await api(`/library?q=${encodeURIComponent(q.value)}&topic=${encodeURIComponent(topic.value)}&kind=${encodeURIComponent(kind.value)}&offset=${offset}&limit=24`);
    if(!cancelled&&request===sequence)draw(result);}catch(e){if(!cancelled&&request===sequence){count.textContent='Could not load results.';pager.replaceChildren(button('Try again',()=>void refresh(),'secondary'));app.showError(e);}}}
  q.oninput=()=>{offset=0;sequence++;clearTimeout(timer);remember(app,state());pending();timer=window.setTimeout(()=>void refresh(),200);};
  kind.onchange=topic.onchange=()=>{offset=0;clearTimeout(timer);remember(app,state());void refresh();};
  app.content.replaceChildren(heading('An open library. Built for careful research.','Original guides, worked examples, reusable templates, and Agent playbooks. Free to read and download.'),
    notice('Original guides, cases, templates and study questions. Educational drafts, not professionally reviewed accounting guidance.','warning'),
    el('div',{class:'filters'},field('Search library',q),field('Content type',kind),field('Topic',topic)),count,grid,pager,
    card('What is—and is not—in this release',el('p',{},'The library contains original explanations and fictional cases. It does not include the ASC, DART, AICPA, IFRS, company filings, or a complete government-standards corpus.'),
      el('p',{},'The source directory and Agent evidence store have independent approval controls. Reading an article does not mean a research run used it.'),link(app,'Inspect the source directory →','/sources')));
  remember(app,state());
  if(saved&&(q.value||kind.value||topic.value||offset))void refresh();else draw(initial);
}
