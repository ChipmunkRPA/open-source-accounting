import {annotationNotice} from '../annotation.js';
import {api} from '../api.js';
import {el,button,heading,notice,badge,field,input,select,busy} from '../ui.js';
import type {App} from '../types.js';

type Letter={company:string;cik:string;accession:string;form:string;url:string;letter_date:string;filed_on:string|null;publicly_available_on:string|null;checked_on:string;reviewed_filing:string;related_accessions:string[];locator:string;topics:string[];staff_concern:string;company_response:string;analysis:string;follow_up:string;kind:string;analysis_partial:boolean;archive_artifacts:{raw_sha256:string;normalized_sha256:string;parser_version:string;acquired_at:number}[];findings:{topic:string;locator:string;analysis_version:string;hits:{term:string;start:number;end:number}[]}[]};
type Results={items:Letter[];total:number;next_offset:number|null;topics:string[];topic_counts:Record<string,number>;coverage:{archived_records:number;reference_records:number;scan_truncated:boolean};notice:string;refresh:string;catalog_checked_on:string};
export async function secCommentsView(app:App){
 let alive=true,request=0,offset=0;
 app.cleanup=()=>{alive=false;request++;};
 const q=input('search');q.placeholder='Company, CIK, accession, filing or topic';
 const topic=select([['','All topics']]);
 const form=select([['','Staff letters and company responses'],['UPLOAD','SEC staff letters'],['CORRESP','Company responses']]);
 const period=select([['true','Recent two years · letter date'],['false','All archive dates']]);
 const results=el('div',{'aria-live':'polite'});
 function card(r:Letter){
  return el('article',{class:'card'},el('h2',{},r.company),badge(r.form==='UPLOAD'?'SEC staff letter':'Company response'),badge(r.kind==='reference_only'?'Reference · original not retained':'Authorized retained artifact'),
   el('p',{},r.topics.join(' · ')),el('p',{class:'muted'},`Letter ${r.letter_date} · Filed ${r.filed_on||'unverified'} · Public release ${r.publicly_available_on||'unverified'}`),
   el('p',{},r.reviewed_filing),el('p',{class:'muted'},`CIK ${r.cik} · Accession ${r.accession} · Checked ${r.checked_on}`),el('p',{},r.locator),
   el('a',{href:r.url,target:'_blank',rel:'noopener noreferrer'},'Read official SEC record'),
   el('details',{},el('summary',{},'Analysis and correspondence context'),
    annotationNotice('Our correspondence summaries, analysis and follow-up questions'),
    notice('Draft analysis · Independent review pending · Outcome not established'),
    r.analysis_partial?notice('Analysis display limit reached; review the complete artifact.','warning'):null,
    el('h3',{},'Staff concern'),el('p',{},r.staff_concern),el('h3',{},'Company response'),el('p',{},r.company_response),
    el('h3',{},'Analysis'),el('p',{},r.analysis),el('h3',{},'Follow-up'),el('p',{},r.follow_up),
    el('p',{},r.related_accessions.length?'Explicitly linked accessions: '+r.related_accessions.join(', '):'No verified correspondence chain linked. Nearby dates alone do not establish a connection.'),
    ...r.findings.map(f=>el('p',{},`${f.topic} · ${f.locator} · Lexical mentions: ${f.hits.map(h=>`${h.term} [${h.start}–${h.end}]`).join(', ')} · ${f.analysis_version}`))),
   ...r.archive_artifacts.map(a=>el('details',{},el('summary',{},'Retained artifact provenance'),el('p',{class:'sec-hash'},`Raw SHA-256 ${a.raw_sha256}`),el('p',{class:'sec-hash'},`Normalized SHA-256 ${a.normalized_sha256}`),el('p',{},`Parser ${a.parser_version} · Acquired ${new Date(a.acquired_at*1000).toLocaleString()}`))));
 }
 async function search(reset=true){
  if(reset)offset=0;const n=++request;busy(searchButton,true,'Loading…');
  try{
   const params=new URLSearchParams({q:q.value,topic:topic.value,recent:period.value,offset:String(offset)});
   if(form.value)params.set('form',form.value);
   const data=await api<Results>('/sec-comments?'+params);
   if(!alive||n!==request)return;
   if(topic.options.length===1)for(const t of data.topics)topic.append(el('option',{value:t},t));
   results.replaceChildren(el('p',{},`${data.total} matching records · ${data.coverage.archived_records} with retained artifacts · ${data.coverage.reference_records} reference-only`),notice(data.notice),
    el('p',{class:'muted'},`Catalog checked ${data.catalog_checked_on}. ${data.refresh}`),
    el('p',{},'Topic counts within this selection: '+(Object.entries(data.topic_counts).map(([k,v])=>`${k}: ${v}`).join(' · ')||'none')),
    ...(data.coverage.scan_truncated?[notice('Corpus scan limit reached. Coverage and counts are partial.','warning')]:[]),...data.items.map(card));
   if(!data.items.length)results.append(notice('No matching records. This does not establish that no correspondence exists.'));
   const pages=el('div',{class:'actions'});
   if(offset)pages.append(button('Previous',()=>{offset=Math.max(0,offset-25);void search(false);},'secondary'));
   if(data.next_offset!==null)pages.append(button('Next',()=>{offset=data.next_offset!;void search(false);},'secondary'));
   results.append(pages);
  }catch(e){if(alive&&n===request)app.showError(e);}finally{if(alive&&n===request)busy(searchButton,false);}
 }
 const searchButton=button('Search correspondence',()=>search());
 q.onkeydown=e=>{if(e.key==='Enter')void search();};
 form.onchange=topic.onchange=period.onchange=()=>void search();
 app.content.replaceChildren(heading('SEC recent comments','Public staff letters, company responses, and source-grounded analysis.'),
  notice('FREE PUBLIC MODULE · Filing-review correspondence; rulemaking comments are separate.'),
  el('a',{href:'https://www.sec.gov/search-filings/edgar-search-assistance/how-search-edgar-correspondence',target:'_blank',rel:'noopener noreferrer'},'Find more correspondence in official EDGAR search'),
  el('div',{class:'asu-filters'},field('Search',q),field('Topic',topic),field('Correspondence type',form),field('Date window',period),searchButton),results);
 await search();
}
