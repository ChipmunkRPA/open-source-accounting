import {applicabilityReview} from './applicability-review.js';
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
          link(app,'Explore Agent tasks →','/agents'),link(app,'General AI chat · Free','/chat')))));
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
export async function editorialView(app:App){
  const result:Json=await api('/editorial/sources');const rows=el('div',{class:'grid two'});
  for(const s of result.items){
    const inspect=button('Review exact revision',()=>{
      const note=textarea('','technical-review-note',5),checked=checkbox('I actually performed this technical review and addressed every listed source and limitation.');
      const decision=select([['changes_requested','Request changes'],['approved','Approve technical content'],['rejected','Reject'],['revoked','Revoke prior review']]);const status=el('div');
      const scope=textarea('','review-scope',3),evidence=input('text','','review-evidence'),evidenceHash=input('text','','review-evidence-hash'),expiry=input('datetime-local');
      const dialog=modal(s.title,badge('Rights: '+(s.rights_reviewed?'approved':'pending')),badge('Technical: '+s.editorial_status),
        notice('A source link is not proof of primary-text access. Record exactly what you checked. This action never labels original commentary authoritative.','warning'),
        markdown(s.text||'').element,sourceNotices(s.source_attributions),el('pre',{},JSON.stringify(s.policy.content_reference_ids,null,2)),field('Decision',decision),field('Review scope',scope),field('Findings and authority limitations',note),field('Private supporting-record reference',evidence),field('Supporting-record SHA-256',evidenceHash),field('Review expires at (your local time)',expiry),checked.element,status);
      dialog.append(button('Record review',async()=>{try{
        if(!checked.input.checked)throw new Error('Confirm actual review before submitting.');
        if(!expiry.value || !Number.isFinite(new Date(expiry.value).getTime()))throw new Error('Choose an explicit review expiry.');
        await api('/editorial/sources/'+s.id+'/review','POST',{expected_policy_version:s.policy_version,content_sha256:s.content_sha256,
          expected_review_revision:s.review_revision,decision:decision.value,review_scope:scope.value,review_note:note.value,
          evidence_ref:evidence.value,evidence_sha256:evidenceHash.value,expires_at:Math.floor(new Date(expiry.value).getTime()/1000),
          checked_reference_ids:s.policy.content_reference_ids||[],confirm_actual_review_performed:true});
        dialog.close();await editorialView(app);
      }catch(e){status.replaceChildren(notice((e as Error).message,'error'));}},'secondary'));
    },'secondary');
    const compare=button('Compare versions',()=>{
      const versions=select([['','Choose a staged version'],...result.items.filter((other:Json)=>other.id!==s.id).map((other:Json):[string,string]=>[other.id,other.title+' · '+other.version+' · '+other.id.slice(0,8)])]);
      const output=el('div');
      const dialog=modal('Compare exact versions',notice('Select a baseline for this version. Only the same explicit item or work/passage identity can be compared; permissions are checked for both.'),
        el('p',{},'Comparison target: '+s.title+' · '+s.version),field('Comparison baseline',versions),output);
      const run=button('Show changes',async()=>{
        run.disabled=true;output.replaceChildren();
        try{
          const before=result.items.find((other:Json)=>other.id===versions.value);
          if(!before)throw new Error('Choose a baseline version.');
          const data:Json=await api('/editorial/compare','POST',{before_source_id:before.id,after_source_id:s.id,
            before_revision:before.review_revision,after_revision:s.review_revision,
            before_policy_version:before.policy_version,after_policy_version:s.policy_version});
          if(!dialog.isConnected)return;
          const c=data.comparison;
          output.replaceChildren(notice(c.notice),sourceNotices(c.source_attributions),
            el('h3',{},c.body_changed?'Text changes':'Text is identical'),
            ...c.line_changes.map((change:Json)=>el('div',{class:'grid two'},
              card('Before · line '+change.before_start_line,el('pre',{class:'review-text'},change.before_lines.join('')||'(no lines)')),
              card('After · line '+change.after_start_line,el('pre',{class:'review-text'},change.after_lines.join('')||'(no lines)')))),
            el('h3',{},'Metadata changes'),
            ...c.metadata_changes.map((change:Json)=>card(change.field.replaceAll('_',' '),
              el('div',{class:'grid two'},el('div',{},el('h4',{},'Before'),el('pre',{class:'review-text'},JSON.stringify(change.before,null,2))),
                el('div',{},el('h4',{},'After'),el('pre',{class:'review-text'},JSON.stringify(change.after,null,2)))))),
            ...(c.metadata_changes.length?[]:[el('p',{},'No compared metadata fields changed.')]),
            el('p',{class:'muted review-hash'},'Before body SHA-256 '+c.before.body_sha256),
            el('p',{class:'muted review-hash'},'After body SHA-256 '+c.after.body_sha256),
            notice('No approval was transferred. Inspect missing source context and applicability separately.'));
        }catch(e){if(dialog.isConnected)output.replaceChildren(notice((e as Error).message,'error'));}finally{run.disabled=false;}
      },'secondary');dialog.append(run);
    },'quiet');
    const packet=button('Download review packet',async()=>{try{
      const data:Json=await api('/editorial/sources/'+s.id+'/packet?expected_review_revision='+encodeURIComponent(s.review_revision)+'&expected_policy_version='+s.policy_version);
      saveBlob(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),'review-packet.json');
      }catch(e){app.showError(e);}},'quiet');
    const history=button('Review history',async()=>{try{const data:Json=await api('/editorial/sources/'+s.id+'/reviews');
      modal('Technical review history',notice('Private review records; do not copy confidential advice into public content.'),el('pre',{},JSON.stringify(data,null,2)));
      }catch(e){app.showError(e);}},'quiet');
    rows.append(card(s.title,badge(s.editorial_status+(s.technical_review_current?' · current':' · no current approval'),'warning'),el('p',{class:'muted'},'Version '+s.version+' · rights '+(s.rights_reviewed?'approved':'pending')),inspect,compare,history,packet,
      s.policy.sec_core?notice('Bundled SEC excerpts use the separate SEC applicability workflow.'):button('Review applicability',()=>applicabilityReview(app,s,()=>editorialView(app)),'secondary')));
  }
  app.content.replaceChildren(heading('Technical content review','Reviews are recorded against the exact source hash and policy revision.'),
    notice('Importing a content pack does not approve it. Source rights approval and a separate technical-review action are both required.'),
    result.items.length?rows:empty('No staged library content','An operator can stage the pack with python -m app.content import --author ADMIN_USER_ID.'));
}
