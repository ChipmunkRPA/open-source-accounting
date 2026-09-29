import {api,saveBlob} from '../api.js';
import {el,button,link,heading,badge,field,notice,card,select,input,empty,textarea,checkbox,modal} from '../ui.js';
import {markdown} from '../markdown.js';
import {sourceNotices} from '../source-notices.js';
import type {App,Json} from '../types.js';
function saveMarkdown(name:string,text:string){const url=URL.createObjectURL(new Blob([text],{type:'text/markdown;charset=utf-8'}));
  const a=el('a',{href:url,download:name});document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
const labels:Record<string,string>={guide:'Guides',case:'Worked cases',template:'Templates',playbook:'Agent playbooks',qa_set:'Study questions'};
export async function openLibraryView(app:App,id?:string){
  if(id){
    const item:Json=await api('/library/'+encodeURIComponent(id));const body=markdown(item.body.replace(/^# [^\n]*\n+/,''));
    const toc=el('nav',{'aria-label':'Article sections',class:'library-toc'},el('h2',{},'In this article'),
      ...body.headings.map(h=>el('a',{href:'#'+h.id},h.text)));
    const sources=card('Source provenance',...item.sources.map((s:Json)=>el('div',{class:'library-reference'},
      el('a',{href:s.url,target:'_blank',rel:'noopener noreferrer'},s.title+' ↗'),
      el('p',{class:'muted'},s.review_scope),badge(s.verification==='publisher_page_examined'?'Publisher page examined':'Reference only','neutral'))));
    app.content.replaceChildren(link(app,'← Open library','/library'),
      heading(item.title,item.summary,button('Download original Markdown',()=>saveMarkdown(item.id+'.md',item.body),'secondary')),
      el('div',{class:'row-actions'},badge('FREE ORIGINAL CONTENT','free'),badge('AI-ASSISTED · UNREVIEWED','warning'),badge(item.license)),
      notice('This public editorial draft is not automatically available to research agents. Independent rights and technical approval are required before Agent use.','warning'),
      el('div',{class:'library-reading-layout'},el('div',{},body.element,sources),
        el('aside',{},toc,card('Use this material',el('p',{},'Read, download, and adapt the original content under CC BY 4.0. Preserve attribution and identify changes.'),
          el('p',{class:'muted'},'Third-party standards are linked, not licensed or reproduced by this pack.'),
          link(app,'General AI chat · Free','/chat')))));
    return;
  }
  const initial:Json=await api('/library?limit=24');const q=input('search','','library-search');q.placeholder='Search issues, examples, or a task';q.maxLength=200;
  const kind=select([['','All content'],...initial.facets.kinds.map((k:string)=>[k,labels[k]||k])]),
    topic=select([['','All topics'],...initial.facets.topics.map((t:string)=>[t,t.replaceAll('_',' ')])]);
  const grid=el('div',{class:'grid two library-grid'}),count=el('p',{class:'muted','aria-live':'polite'}),pager=el('div',{class:'row-actions'});
  let offset=0,sequence=0,timer:number;
  function draw(result:Json){
    count.textContent=`${result.total} matching items · all ${initial.total} starter items are editorial drafts`;
    grid.replaceChildren(...result.items.map((item:Json)=>card(item.title,
      el('div',{class:'row-actions'},badge(labels[item.kind]||item.kind),badge(item.topic),badge('DRAFT','warning')),
      el('p',{class:'muted'},item.summary),link(app,'Read '+(item.kind==='case'?'case':'article')+' →','/library/'+item.id))));
    if(!result.items.length)grid.append(empty('No matching articles','Try fewer words or remove a filter.'));
    const previous=button('Previous',()=>{offset=Math.max(0,offset-24);void refresh();},'secondary');previous.disabled=offset===0;
    const next=button('Next',()=>{offset+=24;void refresh();},'secondary');next.disabled=offset+24>=result.total;
    pager.replaceChildren(previous,el('span',{},result.total?`${offset+1}–${Math.min(offset+24,result.total)} of ${result.total}`:'0 results'),next);
  }
  async function refresh(){const request=++sequence;try{const result=await api(`/library?q=${encodeURIComponent(q.value)}&topic=${encodeURIComponent(topic.value)}&kind=${kind.value}&offset=${offset}&limit=24`);
    if(request===sequence)draw(result);}catch(e){app.showError(e);}}
  q.oninput=()=>{offset=0;clearTimeout(timer);timer=window.setTimeout(()=>void refresh(),200);};
  kind.onchange=topic.onchange=()=>{offset=0;void refresh();};app.cleanup=()=>{clearTimeout(timer);sequence++;};
  app.content.replaceChildren(heading('An open library. Built for careful research.','Original guides, worked examples, reusable templates, and Agent playbooks. Free to read and download.'),
    notice('Original guides, cases, templates and study questions. AI-assisted drafts, not professionally reviewed accounting guidance.','warning'),
    el('div',{class:'filters'},field('Search library',q),field('Content type',kind),field('Topic',topic)),count,grid,pager,
    card('What is—and is not—in this release',el('p',{},'The library contains original explanations and fictional cases. It does not include the ASC, DART, AICPA, IFRS, company filings, or a complete government-standards corpus.'),
      el('p',{},'The source directory and Agent evidence store have independent approval controls. Reading an article does not mean a research run used it.'),link(app,'Inspect the source directory →','/sources')));
  draw(initial);
}
