import {api,saveBlob} from '../api.js';
import {el,button,link,heading,badge,field,notice,card,select,input,empty,textarea,checkbox,busy,table,dateText} from '../ui.js';
import {sourceNotices} from '../source-notices.js';
import type {App,Json} from '../types.js';

export async function parserReviewView(app:App){
  let disposed=false,sequence=0,offset=0;
  app.cleanup=()=>{disposed=true;sequence++;};
  const body=el('div'),status=el('div');
  app.content.replaceChildren(heading('Parser and citation review','Compare original artifacts with extracted passages before recording a separate parser decision.',link(app,'Technical content review','/editorial')),
    notice('Parser review does not approve accounting conclusions, source permissions or historical applicability.'),status,body);
  async function list(){
    const ticket=++sequence;
    try{
      const data:Json=await api('/editorial/extractions?offset='+offset);
      if(disposed||ticket!==sequence)return;
      const rows=el('div',{class:'grid two'});
      for(const row of data.items){
        const inspect=button('Inspect extraction',()=>inspectExtraction(row),'secondary');
        inspect.disabled=!row.packet_permitted;
        rows.append(card(row.title,badge(row.family_id),el('p',{},'Edition '+row.edition+' · '+row.passage_count+' passages'),
          el('p',{class:'muted'},'Parser '+row.parser_version),
          el('p',{},row.last_decision?'Last decision: '+row.last_decision.replaceAll('_',' ')+' · record '+row.review_sequence+' · expires '+dateText(row.review_expires_at):'No parser decision recorded'),
          notice('Recorded decisions are checked again for revision, expiry and permissions at use.'),inspect,
          !row.packet_permitted?notice('Current artifact display and export permissions are required to open the review packet.','warning'):null));
      }
      const previous=button('Previous extractions',()=>{offset=Math.max(0,offset-30);void list();},'quiet');previous.disabled=offset===0;
      const next=button('Next extractions',()=>{offset=data.next_offset;void list();},'quiet');next.disabled=data.next_offset===null;
      body.replaceChildren(data.items.length?rows:empty('No parsed artifacts','An operator must acquire and parse an authorized source before review.'),el('div',{},previous,next));
    }catch(e){if(!disposed&&ticket===sequence)status.replaceChildren(notice((e as Error).message,'error'));}
  }
  async function inspectExtraction(row:Json){
    const ticket=++sequence;status.replaceChildren(notice('Loading the authorized artifact packet…'));
    try{
      const result:Json=await api('/editorial/extractions/'+encodeURIComponent(row.id)+'/packet');
      if(disposed||ticket!==sequence)return;
      status.replaceChildren();const packet=result.packet,checked=new Set<number>();let start=0;
      const passages=el('section',{'aria-label':'Extracted passages'}),count=el('p',{'aria-live':'polite'}),feedback=el('div'),history=el('div');
      function renderPassages(){
        const units=packet.passages.slice(start,start+25).map((p:Json,i:number)=>{
          const index=start+i,check=checkbox('I checked passage '+(index+1)+' and its locator against the original artifact.',checked.has(index));
          check.input.onchange=()=>{check.input.checked?checked.add(index):checked.delete(index);count.textContent=checked.size+' of '+packet.passages.length+' passages checked.';};
          return card('Passage '+(index+1)+' · '+p.locator,el('pre',{class:'review-text'},p.text),el('p',{class:'muted review-hash'},'SHA-256 '+p.sha256),check.element);
        });
        const prev=button('Previous passages',()=>{start=Math.max(0,start-25);renderPassages();},'quiet');prev.disabled=start===0;
        const next=button('Next passages',()=>{start+=25;renderPassages();},'quiet');next.disabled=start+25>=packet.passages.length;
        count.textContent=checked.size+' of '+packet.passages.length+' passages checked.';
        passages.replaceChildren(...units,el('div',{},prev,next));
      }
      const choice=select([['changes_requested','Request changes'],['approved','Approve parser and citations'],['rejected','Reject'],['revoked','Revoke prior parser review']]);
      const scope=textarea('','parser-scope',3),findings=textarea('','parser-findings',5),reference=input('text'),hash=input('text'),expiry=input('datetime-local');
      const attest=checkbox('I actually inspected the original artifact, extraction and citation locators for this scope.');
      const submit=button('Record parser decision',async()=>{
        busy(submit,true);feedback.replaceChildren();
        try{
          if(!attest.input.checked)throw new Error('Confirm actual inspection before submitting.');
          if(!expiry.value||!Number.isFinite(new Date(expiry.value).getTime()))throw new Error('Choose an explicit review expiry.');
          if(choice.value==='approved'&&checked.size!==packet.passages.length)throw new Error('Inspect and check every passage before approval.');
          const saved:Json=await api('/editorial/extractions/'+encodeURIComponent(row.id)+'/review','POST',{
            expected_revision:packet.review_revision,expected_sequence:packet.review_sequence,decision:choice.value,
            review_scope:scope.value,review_note:findings.value,evidence_ref:reference.value,evidence_sha256:hash.value,
            expires_at:Math.floor(new Date(expiry.value).getTime()/1000),checked_passage_indices:[...checked].sort((a,b)=>a-b),
            confirm_raw_and_citations_checked:true});
          if(disposed||ticket!==sequence)return;
          feedback.replaceChildren(notice('Parser decision recorded: '+saved.decision.replaceAll('_',' ')+' · record '+saved.sequence+'. Other review gates remain separate.'));
          submit.textContent='Decision recorded';submit.disabled=true;body.append(button('Reload this extraction',()=>inspectExtraction(row),'secondary'));
        }catch(e){if(!disposed&&ticket===sequence)feedback.replaceChildren(notice((e as Error).message,'error'));busy(submit,false);}
      },'secondary');
      async function exportPacket(raw=false){
        try{
          const latest:Json=await api('/editorial/extractions/'+encodeURIComponent(row.id)+'/packet');
          if(disposed||ticket!==sequence)return;
          if(latest.packet.review_revision!==packet.review_revision)throw new Error('The extraction changed. Reload it before downloading.');
          if(raw){const bytes=Uint8Array.from(atob(latest.packet.raw_base64),(c:string)=>c.charCodeAt(0));saveBlob(new Blob([bytes],{type:'application/octet-stream'}),'source-artifact.bin');}
          else saveBlob(new Blob([JSON.stringify(latest,null,2)],{type:'application/json'}),'parser-review-packet.json');
        }catch(e){if(!disposed&&ticket===sequence)feedback.replaceChildren(notice((e as Error).message,'error'));}
      }
      const downloads=el('div',{},button('Download review packet',()=>exportPacket(),'quiet'),
        button('Download original bytes',()=>exportPacket(true),'quiet'));
      const loadHistory=button('Show parser decision history',async()=>{
        busy(loadHistory,true);
        try{const data:Json=await api('/editorial/extractions/'+encodeURIComponent(row.id)+'/reviews');if(disposed||ticket!==sequence)return;
          history.replaceChildren(notice('Private review findings. Use an approved review channel when sharing.'),
            ...data.items.map((r:Json)=>card('Record '+r.sequence+' · '+r.payload.decision.replaceAll('_',' '),
              el('p',{},'Reviewer '+r.payload.reviewer_id+' · '+dateText(r.created_at)+' · expires '+dateText(r.payload.expires_at)),
              el('p',{},r.payload.review_scope),el('pre',{class:'review-text'},r.payload.review_note),
              el('p',{class:'review-hash'},'Supporting record '+r.payload.evidence_ref+' · SHA-256 '+r.payload.evidence_sha256))),
            ...(!data.items.length?[el('p',{},'No decisions recorded.')]:[]));
        }catch(e){if(!disposed&&ticket===sequence)history.replaceChildren(notice((e as Error).message,'error'));}finally{busy(loadHistory,false);}
      },'quiet');
      renderPassages();
      body.replaceChildren(button('Back to extractions',()=>list(),'quiet'),card(packet.source.title,
        el('p',{},packet.source.publisher+' · edition '+packet.source.edition),
        table(['Field','Value'],[['Original format',packet.raw_mime],['Raw SHA-256',packet.identity.raw_sha256],['Normalized SHA-256',packet.identity.normalized_sha256],['Parser',packet.identity.parser_version],['Decision sequence',packet.review_sequence]]),
        notice('Open original bytes in an isolated viewer. This page displays extracted plain text and does not execute the source file.'),
        el('ul',{},...packet.publication_metadata.notices.map((n:string)=>el('li',{},n))),sourceNotices(packet.source_attributions),downloads),
        count,passages,card('Record a parser decision',field('Decision',choice),field('Review scope',scope),field('Findings and limitations',findings),
          field('Private supporting-record reference',reference),field('Supporting-record SHA-256',hash),field('Review expires at (your local time)',expiry),attest.element,submit,feedback),loadHistory,history);
    }catch(e){if(!disposed&&ticket===sequence)status.replaceChildren(notice((e as Error).message,'error'));}
  }
  await list();
}
