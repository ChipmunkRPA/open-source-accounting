import {api,APIError} from '../api.js';
import {sourceNotices} from '../source-notices.js';
import {el,button,field,input,select,notice,card,link} from '../ui.js';
import type {App,Json} from '../types.js';

export function citationPicker(app:App,label:string,changed:()=>void){
  let disposed=false,busy=false,locked=false,ticket=0,revision:string|null=null;
  let rows:Json[]=[],selection:Json|null=null,starts=[0],page=0,next:number|null=null;
  const id=input(),choice=select([['','Load passage locations']]),message=el('div'),preview=el('div');
  const load=button('Load '+label.toLowerCase()+' passages',()=>fetchPage(0,true),'secondary');
  const previous=button('Previous '+label.toLowerCase()+' passages',()=>fetchPage(page-1),'quiet');
  const following=button('Next '+label.toLowerCase()+' passages',()=>fetchPage(page+1),'quiet');
  const inspect=button('Inspect '+label.toLowerCase()+' passage',()=>read(),'secondary');
  const state=el('p',{class:'muted'});
  const root=card(label,field(label+' source ID',id),link(app,'Find a source','/sources'),load,
    field(label+' passage',choice),el('div',{class:'actions'},previous,following,inspect),state,message,preview);
  function controls(){
    id.disabled=locked||busy;load.disabled=locked||busy;choice.disabled=locked||busy||!rows.length;
    previous.disabled=locked||busy||page===0;following.disabled=locked||busy||next===null;
    inspect.disabled=locked||busy||choice.value==='';
  }
  function reset(){selection=null;preview.replaceChildren();changed();}
  function invalidate(){ticket++;reset();rows=[];starts=[0];page=0;next=null;revision=null;state.textContent='';choice.replaceChildren(el('option',{value:''},'Load passage locations'));controls();}
  id.oninput=()=>{invalidate();message.replaceChildren();};
  choice.onchange=()=>{reset();controls();};
  function failure(e:unknown){invalidate();message.replaceChildren(notice((e as Error).message+' Reload the passage locations before continuing.','error'));}
  async function fetchPage(index:number,fresh=false){
    if(busy||locked)return;
    if(!id.value.trim()){message.replaceChildren(notice('Enter a source ID.','error'));return;}
    if(fresh)invalidate();
    const start=index<starts.length?starts[index]:next;if(start===null||index<0)return;
    busy=true;controls();reset();const current=++ticket,sid=id.value.trim();message.replaceChildren(notice('Loading exact locations…'));
    try{
      const result=await api('/sources/'+encodeURIComponent(sid)+`/passages?start=${start}&limit=10`);
      if(disposed||current!==ticket)return;
      const version=result.items[0]?.revision;
      if(!version||result.items.some((x:Json)=>x.revision!==version)||(revision&&revision!==version))throw new APIError('REVISION_CONFLICT','The source changed between pages.',409);
      revision=version;rows=result.items;page=index;starts[index]=start;next=result.next_start;
      choice.replaceChildren(el('option',{value:''},'Choose a passage'),...rows.map((x,i)=>el('option',{value:String(i)},`Characters ${x.character_start+1}–${x.character_end}: ${x.source_locator}`)));
      state.textContent=`Page ${page+1} · ${result.retained_characters.toLocaleString()} retained characters`;
      message.replaceChildren(sourceNotices(result.source_attributions));
    }catch(e){if(!disposed&&current===ticket)failure(e);}
    finally{busy=false;if(!disposed)controls();}
  }
  async function read(){
    const row=rows[Number(choice.value)];if(busy||locked||choice.value===''||!row)return;
    busy=true;controls();reset();const current=++ticket;
    try{
      const result=await api('/sources/'+encodeURIComponent(row.source_id)+'/passages/resolve','POST',{
        expected_revision:row.revision,locator:row.locator,character_start:row.character_start,character_end:row.character_end,passage_text_sha256:row.passage_text_sha256});
      if(disposed||current!==ticket)return;
      selection=Object.fromEntries(['source_id','revision','locator','character_start','character_end','passage_text_sha256'].map(k=>[k,result.citation[k]]));
      preview.replaceChildren(el('p',{class:'review-hash'},result.citation.locator),el('pre',{class:'source-passage-text'},result.text),
        el('p',{class:'review-hash'},'Passage SHA-256: '+result.citation.passage_text_sha256),sourceNotices(result.source_attributions));changed();
    }catch(e){if(!disposed&&current===ticket)failure(e);}
    finally{busy=false;if(!disposed)controls();}
  }
  controls();
  return {root,get:()=>selection,clear:invalidate,lock:(value:boolean)=>{locked=value;controls();},dispose:()=>{disposed=true;ticket++;}};
}
