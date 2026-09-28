import {api} from '../api.js';
import {el,button,heading,notice,badge,field,input,select,busy} from '../ui.js';
import type {App} from '../types.js';

type ASU={id:string;subject:string;topic:string;issued:string;date_precision:string;official_url:string;boundary_uncertain:boolean;reference_links:number};
type Refresh={state:string;completed_at:number|null;eligible_passages:number;overdue:boolean};
type Register={items:ASU[];window_start:string;window_end:string;topics:string[];catalog_checked_on:string;catalog_age_days:number;notice:string;refresh:Refresh;coverage:{reference_links:number;companies:number}};
type Filing={company:string;cik:string;accession:string;form:string|null;filed_on:string|null;period_end:string|null;url:string;locator:string;status:string;observation:string;checked_on:string;kind:string;raw_sha256:string|null;parser_version?:string};
type Materials={items:Filing[];total:number;next_offset:number|null;notice:string};
const label=(s:string)=>s.replaceAll('_',' ');
const external=(url:string,text:string)=>el('a',{href:url,target:'_blank',rel:'noopener noreferrer'},text);

export async function asuTrackingView(app:App){
 let alive=true, request=0, materialRequest=0, selected:ASU|undefined, offset=0;
 app.cleanup=()=>{alive=false;request++;materialRequest++;};
 const q=input('search');q.placeholder='ASU number, subject, or topic';
 const topic=select([['','All topics']]);
 const company=input('search');company.placeholder='Company name or CIK';
 const status=select([['','All disclosure statuses'],['early_adopted','Early adopted'],['adopted','Adopted'],['not_yet_adopted','Not yet adopted'],['mentioned','Mentioned · adoption unverified']]);
 const summary=el('div'), register=el('div',{class:'asu-register'}), detail=el('section',{class:'asu-detail','aria-label':'Selected ASU filings'}), results=el('div',{'aria-live':'polite'});
 const freshness=el('div');
 function showRefresh(s:Refresh){
  freshness.replaceChildren(el('p',{class:'muted'},`Filing corpus refresh: ${s.state.replace('_',' ')} · Last completed: ${s.completed_at?new Date(s.completed_at*1000).toLocaleString():'never'} · ${s.eligible_passages} eligible passages in latest sweep${s.overdue?' · overdue':''}. Daily refresh requires the worker to be running.`));
 }
 async function filings(reset=true){
  if(!selected)return;
  if(reset)offset=0;
  const id=selected.id,n=++materialRequest;
  results.replaceChildren(el('p',{},'Loading filing references…'));
  try{
   const data=await api<Materials>(`/asu-tracking/${id}/filings?company=${encodeURIComponent(company.value)}&status=${encodeURIComponent(status.value)}&offset=${offset}`.replace('&status=&','&'));
   if(!alive||n!==materialRequest)return;
   results.replaceChildren(el('p',{},`${data.total} matching materials`),notice(data.notice),
    ...data.items.map(f=>el('article',{class:'card'},el('h3',{},f.company),badge(label(f.status)),badge(f.kind==='reference_only'?'Reference link · no retained artifact':'Detected mention · unreviewed'),
      el('p',{},f.observation),el('p',{class:'muted'},`${f.form||'Form unverified'} · Period ${f.period_end||'unverified'} · Filed ${f.filed_on||'unverified'} · CIK ${f.cik}`),
      el('p',{},f.locator),el('p',{class:'muted'},`Accession ${f.accession} · Reference checked ${f.checked_on}`),
      f.raw_sha256?el('details',{},el('summary',{},'Artifact provenance'),el('p',{class:'sec-hash'},`SHA-256 ${f.raw_sha256}`),el('p',{},`Parser ${f.parser_version}`)):null,
      external(f.url,'Read SEC filing disclosure'))));
   if(!data.items.length)results.append(notice('No filing materials match this selection. This is a coverage gap, not evidence that companies have not adopted the ASU.'));
   const paging=el('div',{class:'actions'});
   if(offset)paging.append(button('Previous materials',()=>{offset=Math.max(0,offset-25);void filings(false);},'secondary'));
   if(data.next_offset!==null)paging.append(button('Next materials',()=>{offset=data.next_offset!;void filings(false);},'secondary'));
   results.append(paging);
  }catch(e){if(alive&&n===materialRequest){results.replaceChildren(notice('Filing materials could not be loaded. Try again.','error'));app.showError(e);}}
 }
 function choose(a:ASU){
  selected=a;company.value='';status.value='';
  detail.replaceChildren(el('h2',{},`ASU ${a.id} · ${a.subject}`),el('p',{},`Topic ${a.topic} · Issued ${a.issued} (${a.date_precision} precision)`),
    ...(a.boundary_uncertain?[notice('The issuance interval overlaps the edge of the two-year window; the exact date is not established.','warning')]:[]),
    external(a.official_url,'Open official FASB reference'),
    notice('Reference-only. Read the applicable codified guidance and entity-specific transition provisions before drawing conclusions.'),
    el('div',{class:'asu-filters'},field('Company or CIK',company),field('Disclosure status',status),button('Filter filings',()=>filings())),results);
  void filings();
 }
 async function search(){
  const n=++request;busy(searchButton,true,'Loading ASUs…');
  try{
   const data=await api<Register>(`/asu-tracking?q=${encodeURIComponent(q.value)}&topic=${encodeURIComponent(topic.value)}`);
   if(!alive||n!==request)return;
   if(topic.options.length===1)for(const t of data.topics)topic.append(el('option',{value:t},`Topic ${t}`));
   summary.replaceChildren(el('p',{},`${data.items.length} ASUs in the rolling window · ${data.window_start} to ${data.window_end}`),
    el('p',{class:'muted'},`Catalog checked ${data.catalog_checked_on} (${data.catalog_age_days} days ago) · ${data.coverage.reference_links} starter filing links across ${data.coverage.companies} companies.`),notice(data.notice,'warning'));
   showRefresh(data.refresh);
   register.replaceChildren(...data.items.map(a=>el('article',{class:'card'},el('h2',{},`ASU ${a.id}`),
    el('p',{},a.subject),badge(`Topic ${a.topic}`),el('p',{class:'muted'},`Issued ${a.issued} · ${a.reference_links} starter filing links`),
    button('View filings for '+a.id,()=>choose(a),'secondary'))));
   if(!data.items.length){register.append(notice('No ASUs match. Try another topic or search term.'));selected=undefined;materialRequest++;detail.replaceChildren();}
   else if(!selected||!data.items.some(a=>a.id===selected!.id))choose(data.items[0]);
  }catch(e){if(alive&&n===request)app.showError(e);}finally{if(alive&&n===request)busy(searchButton,false);}
 }
 const searchButton=button('Search ASUs',search);
 const refreshButton=button('Refresh authorized filing corpus',async()=>{
  busy(refreshButton,true,'Refreshing…');
  try{const s=await api<Refresh>('/admin/asu-tracking/refresh','POST');if(alive){showRefresh(s);await filings();}}
  catch(e){if(alive)app.showError(e);}finally{if(alive)busy(refreshButton,false);}
 },'secondary');
 q.onkeydown=e=>{if(e.key==='Enter')void search();};
 company.onkeydown=e=>{if(e.key==='Enter')void filings();};
 topic.onchange=()=>void search();status.onchange=()=>void filings();
 app.content.replaceChildren(heading('ASU tracking','Recent accounting updates and how public companies discuss them in SEC filings.'),
  notice('FREE PUBLIC MODULE · Company practice is separate from authoritative accounting requirements.'),summary,freshness,
  app.me?.role==='admin'?refreshButton:el('span'),
  el('div',{class:'asu-filters'},field('Search recent ASUs',q),field('ASC topic',topic),searchButton),
  el('div',{class:'asu-layout'},register,detail));
 await search();
}
