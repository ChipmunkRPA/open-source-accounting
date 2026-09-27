import {api} from '../api.js';
import {el,button,heading,notice,badge,field,input,select,table,modal,busy} from '../ui.js';
import type {App} from '../types.js';

type Passage={id:string;locator:string;text:string;url:string;source_id:string;authority_type:string;retrieved_at:string;source_as_of:string|null;context_note:string;sha256:string;snapshot_id:string;verification_locator:string;professional_review:string};
type Source={id:string;title:string;family:string;url:string;acquisition_status:string};
type Inventory={sources_inventoried:number;sources_with_excerpts:number;selected_excerpts:number;agent_approved:number;notice:string;sources:Source[];families:{family:string;inventoried:number;excerpted:number;excerpts:number}[]};

export async function secCoreView(app:App){
 const stats=await api<Inventory>('/sec-core');
 const q=input('search','', 'sec-query');q.placeholder='Try equal prominence, 100.04, materiality, or furnished';
 const family=select([['','All collections'],...stats.families.map(f=>[f.family,f.family.toUpperCase().replace('_',' ')] as [string,string])]);
 const results=el('div',{'aria-live':'polite'});
 const list=el('div');let alive=true;let request=0;
 app.cleanup=()=>{alive=false;request++;};
 function detail(item:Passage){
  const a=el('a',{href:item.url,target:'_blank',rel:'noopener noreferrer'},'Open official source');
  modal(item.locator,badge(item.authority_type.replaceAll('_',' ')),notice('Selected official-source excerpt. Independent professional review is pending; not admitted as Agent evidence.'),
   el('p',{},item.context_note),el('pre',{class:'sec-text'},item.text),
   el('dl',{},el('dt',{},'Source checked / transcription recorded'),el('dd',{},item.retrieved_at),
      el('dt',{},'Source as-of, not effective date'),el('dd',{},item.source_as_of||'Not established'),
      el('dt',{},'Verification locator'),el('dd',{},item.verification_locator),
      el('dt',{},'Text SHA-256'),el('dd',{class:'sec-hash'},item.sha256)),a);
 }
 async function search(){
  const n=++request;busy(searchButton,true,'Searching source excerpts…');
  try{
   const r=await api<{items:Passage[]}>(`/sec-core/search?q=${encodeURIComponent(q.value)}&limit=40${family.value?'&family='+encodeURIComponent(family.value):''}`);
   if(!alive||n!==request)return;
   results.replaceChildren(el('p',{},`${r.items.length} matching excerpts · Source-reading preview, not a research conclusion`),
     ...r.items.map(x=>el('article',{class:'card'},el('h2',{},x.locator),badge(x.authority_type.replaceAll('_',' ')),
      el('p',{},x.text.slice(0,250)+(x.text.length>250?'…':'')),button('Inspect exact excerpt',()=>detail(x),'secondary'))));
   if(!r.items.length)results.append(notice('No excerpt in this starter pack matches. This does not mean the SEC has no relevant guidance.'));
  }catch(e){if(alive&&n===request)app.showError(e);}finally{if(alive&&n===request)busy(searchButton,false);}
 }
 const searchButton=button('Search excerpts',search);
 q.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();void search();}};
 function filterInventory(){
  const rows=stats.sources.filter(s=>!family.value||s.family===family.value);
  list.replaceChildren(table(['Source target','Collection','Actual coverage'],rows.map(s=>[
   button(s.title,async()=>{try{
    const d=await api<{source:Source;document:{passages:Omit<Passage,'url'|'source_id'|'authority_type'|'retrieved_at'|'source_as_of'|'snapshot_id'>[]}|null}>(`/sec-core/sources/${s.id}`);
    if(!alive)return;
    modal(s.title,notice(d.document?`${d.document.passages.length} selected excerpts. Full document not bundled.`:'Inventoried only. Source text has not been included.'),
     el('p',{},'A registry link is not evidence of acquisition, review, or Agent approval.'),
     el('a',{href:s.url,target:'_blank',rel:'noopener noreferrer'},'Open official publisher'));
   }catch(e){app.showError(e);}},'quiet'),s.family,s.acquisition_status==='selected_web_excerpts_only'?'Selected excerpts · review pending':'Inventoried only'
  ])));
 }
 family.onchange=()=>{filterInventory();if(q.value)void search();};
 app.content.replaceChildren(heading('SEC Core','Official-source text, exact locators, and an honest coverage inventory.'),
  notice('FREE SOURCE READING · No subscription or sign-in is required. General chat stays free; new Agent work remains $89.99/year.'),
  notice(stats.notice,'warning'),
  el('div',{class:'sec-stats'},...[[stats.sources_inventoried,'source targets'],[stats.sources_with_excerpts,'sources excerpted'],[stats.selected_excerpts,'selected excerpts'],[0,'approved for Agent']].map(([n,t])=>el('div',{class:'card'},el('strong',{},String(n)),el('p',{},String(t))))),
  el('div',{class:'sec-search'},field('Search official excerpts',q),field('Collection',family),searchButton),
  results,el('h2',{},'Collection targets and gaps'),list,
  notice('Next in the build queue: SEC Practice (#2), then SEC Audit & Enforcement (#3). Queued development does not mean a background crawler is running.'));
 filterInventory();
}
