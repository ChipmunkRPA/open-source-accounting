import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {applyReaderLabels,loadReaderEditions} from '../scripts/read-reader-editions.mjs';
import {loadReaderEdition,readerSourceScope} from '../dist/reader-edition.js';

const root=resolve(fileURLToPath(new URL('../..',import.meta.url)));
const read=path=>readFile(resolve(root,path),'utf8');
const content=path=>readFile(resolve(root,'content',path));
const hash=value=>createHash('sha256').update(value).digest('hex');
const manifestBytes=await content('manifest.json');
const manifest=JSON.parse(manifestBytes);
const index=JSON.parse(await content('reader-editions/index.json'));
const rules=JSON.parse(await content('reader-editions/rules.json'));
const disclosures=/AI-assisted|AI editorial|\bastra\b|\bgpt-|model knowledge/i;
const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');

test('all canonical items have exact hash-bound reader editions; review and admission records are unchanged',async()=>{
  const readers=await loadReaderEditions(content,manifest,manifestBytes);
  assert.equal(readers.size,manifest.items.length);assert.equal(readers.size,124);
  const policy=JSON.parse(await content('annotation-policy.json'));
  const originals=new Map(manifest.items.map(item=>[item.id,item]));
  for(const old of policy.existing_library_items){const item=originals.get(old.id);assert.equal(item.sha256,old.sha256);assert.equal(item.author,old.author);assert.equal(item.license,old.license);}
  for(const item of manifest.items){assert.equal(item.technical_review.status,'unreviewed');assert.equal(item.agent_eligible_by_default,false);assert.ok(item.source_ids.length);}
  const reviews=JSON.parse(await content('ai_reviews/manifest.json'));
  for(const record of reviews.reviews){const item=originals.get(record.item_id);assert.equal(record.content_sha256,item.sha256);assert.equal(record.version,item.version);}
});

test('all 124 pages, downloads and runtime payloads use the same verified neutral reader bytes',async()=>{
  for(const item of manifest.items){
    const row=index.items.find(row=>row.item_id===item.id);
    const original=await read('content/'+item.path);const reader=await read('content/'+row.reader_path);
    const download=await read('frontend/dist/reader-editions/'+item.id+'.md');
    const payload=JSON.parse(await read('frontend/dist/reader-editions/'+item.id+'.json'));
    const html=await read('frontend/dist/library/'+item.id+'.html');
    assert.equal(reader,applyReaderLabels(original,rules));assert.equal(download,reader);assert.equal(payload.body,reader);
    assert.equal(hash(original),item.sha256);assert.equal(hash(reader),row.reader_sha256);
    assert.ok(html.includes(escape(reader)));assert.ok(html.includes(`href="../reader-editions/${item.id}.md" download`));
    assert.ok(!disclosures.test(reader),item.id);assert.ok(!disclosures.test(html),item.id);assert.ok(!disclosures.test(JSON.stringify(payload)),item.id);
    assert.ok(reader.includes('No new professional review or source verification is claimed.'));
    assert.ok(html.includes('Ray Sang Annotation'));assert.ok(html.includes('not') || html.includes('Not'));
    assert.equal(payload.creator_credit,item.author.replace(/ \(AI-assisted\)$/,''));assert.equal(payload.license,item.license);
    assert.deepEqual([...reader.matchAll(/https?:\/\/[^\s)]+/g)].map(x=>x[0]),[...original.replaceAll('../../CONTENT-TERMS.md','https://github.com/ChipmunkRPA/open-source-accounting/blob/4ffc83f154a152c453438eafe63e8b6b77f27a93/CONTENT-TERMS.md').matchAll(/https?:\/\/[^\s)]+/g)].map(x=>x[0]));
    const withoutNotice=reader.replace('\n'+rules.reader_notice+'\n','');
    assert.deepEqual(withoutNotice.replace(/https?:\/\/[^\s)]+/g,'').match(/\d[\d,.]*/g),original.replace(/https?:\/\/[^\s)]+/g,'').match(/\d[\d,.]*/g));
    const result=await loadReaderEdition({...item,body:original},async(url,options)=>{
      assert.equal(url,'/assets/reader-editions/'+item.id+'.json');assert.equal(options.credentials,'same-origin');
      return {ok:true,json:async()=>structuredClone(payload)};
    });
    assert.equal(result.body,reader);
  }
});

test('build refuses unknown source, reader, metadata and coverage changes',async()=>{
  const item=manifest.items[0];const row=index.items[0];
  await assert.rejects(loadReaderEditions(async path=>path===item.path?Buffer.from((await content(path)).toString()+' altered'):content(path),manifest,manifestBytes),/article hash mismatch/);
  await assert.rejects(loadReaderEditions(async path=>path===row.reader_path?Buffer.from('changed'):content(path),manifest,manifestBytes),/article hash mismatch/);
  const missing=structuredClone(index);missing.items.pop();
  await assert.rejects(loadReaderEditions(async path=>path==='reader-editions/index.json'?Buffer.from(JSON.stringify(missing)):content(path),manifest,manifestBytes),/incomplete article coverage|pinned article count/);
  const duplicate=structuredClone(index);duplicate.items[1]=duplicate.items[0];
  await assert.rejects(loadReaderEditions(async path=>path==='reader-editions/index.json'?Buffer.from(JSON.stringify(duplicate)):content(path),manifest,manifestBytes),/canonical item mismatch/);
  const changed=structuredClone(index);changed.items[0].reader_sha256=hash('invented accounting conclusion');
  await assert.rejects(loadReaderEditions(async path=>path==='reader-editions/index.json'?Buffer.from(JSON.stringify(changed)):path===row.reader_path?Buffer.from('invented accounting conclusion'):content(path),manifest,manifestBytes),/unapproved reader text change|pinned article revision/);
  const badPath=structuredClone(index);badPath.items[0].reader_path='../private.md';
  await assert.rejects(loadReaderEditions(async path=>path==='reader-editions/index.json'?Buffer.from(JSON.stringify(badPath)):content(path),manifest,manifestBytes),/invalid reader path/);
  await assert.rejects(loadReaderEditions(content,manifest,Buffer.from('different manifest')),/manifest or rule hash mismatch/);
});

test('runtime refuses stale or tampered articles and never falls back to canonical bodies',async()=>{
  const item=manifest.items[0];const original=await read('content/'+item.path);const base={...item,body:original};
  const payload=JSON.parse(await read('frontend/dist/reader-editions/'+item.id+'.json'));
  const fetcher=value=>async()=>({ok:true,json:async()=>value});
  await assert.rejects(loadReaderEdition({...base,body:original+'changed'},fetcher(payload)),/integrity/);
  await assert.rejects(loadReaderEdition(base,fetcher({...payload,body:payload.body+'changed'})),/integrity/);
  await assert.rejects(loadReaderEdition(base,fetcher({...payload,body:payload.body+'changed',reader_sha256:hash(payload.body+'changed')})),/unapproved article changes|pinned article revision/);
  await assert.rejects(loadReaderEdition({...base,version:'new'},fetcher(payload)),/does not match/);
  await assert.rejects(loadReaderEdition(base,fetcher({...payload,model_id:'fabricated'})),/Invalid reader/);
  await assert.rejects(loadReaderEdition(base,fetcher({...payload,creator_credit:'Different author'})),/does not match/);
  await assert.rejects(loadReaderEdition(base,async()=>({ok:false})),/not available/);
  let called=false;await assert.rejects(loadReaderEdition({...base,id:'../private'},async()=>{called=true;}),/Invalid article/);assert.equal(called,false);
});

test('cards, search snippets, shared labels and downloads are neutral while genuine chat and source-policy discussion remains',async()=>{
  for(const item of manifest.items)assert.ok(!disclosures.test(item.title+' '+item.summary),item.id);
  const library=await read('frontend/dist/library/index.html');assert.ok(!disclosures.test(library));
  const view=await read('frontend/src/views/open-library.ts');
  assert.ok(view.includes('markdown(reader.body.replace'));assert.ok(view.includes("saveMarkdown(item.id+'.md',reader.body)"));assert.ok(!view.includes("saveMarkdown(item.id+'.md',item.body)"));assert.ok(view.includes('if(cancelled)return'));
  for(const path of ['frontend/src/annotation.ts','frontend/src/views/open-library.ts'])assert.ok(!disclosures.test(await read(path)),path);
  for(const path of ['frontend/dist/systems/index.html','frontend/dist/systems/xero.html'])assert.ok(!disclosures.test(await read(path)),path);
  assert.ok((await read('frontend/src/views/chat.ts')).includes('General AI chat is free.'));
  assert.ok((await read('frontend/src/main.ts')).includes('General AI chat is free.'));
  assert.ok((await read('content/reader-editions/2026-10-05/electronic-audit-evidence.md')).includes('A source link is not permission to process the source with AI.'));
  assert.ok((await read('content/reader-editions/2026-10-05/software-cost-workbook.md')).includes('Cloud, AI, agile or implementation are labels, not accounting models.'));
});

test('leaving an article while reader loading discards both late success and late failure',async()=>{
  const {openLibraryView}=await import('../dist/views/open-library.js');
  const item=manifest.items[0];const original=await read('content/'+item.path);
  const payload=JSON.parse(await read('frontend/dist/reader-editions/'+item.id+'.json'));
  const savedFetch=globalThis.fetch;
  try{
    for(const fail of [false,true]){
      let release;let started;
      const requested=new Promise(resolve=>{started=resolve;});
      globalThis.fetch=async url=>{
        if(url.startsWith('/api/v1/library/'))return {ok:true,status:200,json:async()=>({...item,body:original,sources:[]})};
        started();return new Promise((resolve,reject)=>{release=()=>fail?reject(Error('late network failure')):resolve({ok:true,json:async()=>payload});});
      };
      let renders=0;const app={content:{replaceChildren(){renders++;}}};
      const pending=openLibraryView(app,item.id);await requested;app.cleanup();release();await pending;
      assert.equal(renders,0);
    }
  }finally{globalThis.fetch=savedFetch;}
});

test('GitHub entry indexes link all current neutral editions instead of historical canonical bodies',async()=>{
  const landing=await read('README.md');const contentIndex=await read('content/README.md');const readerIndex=await read('content/reader-editions/README.md');
  assert.ok(landing.includes('[current 124-item reader index](content/README.md)'));
  assert.ok(!disclosures.test(contentIndex));assert.ok(contentIndex.includes('not professionally reviewed'));
  for(const item of manifest.items){
    assert.ok(contentIndex.includes(`](reader-editions/2026-10-05/${item.id}.md)`));
    assert.ok(readerIndex.includes(`](2026-10-05/${item.id}.md)`));
    assert.ok(!contentIndex.includes(`](${item.path})`));
  }
  const history=await read('content/reader-editions/history/content-index-0.5.0.md');
  assert.ok(history.includes('Release 0.5.0'));assert.ok(history.includes('42 original library items'));
});

test('runtime rejects paired metadata forgery against the pinned registry even with minimal API data',async()=>{
  const item=manifest.items[0];const body=await read('content/'+item.path);
  const payload=JSON.parse(await read('frontend/dist/reader-editions/'+item.id+'.json'));
  const minimal={id:item.id,title:item.title,license:item.license,body};
  const fetcher=value=>async()=>({ok:true,json:async()=>value});
  assert.equal((await loadReaderEdition(minimal,fetcher(payload))).body,payload.body);
  for(const mutation of [
    {reader_edition:'9999-99-99.999'},
    {reader_edition:'2026-10-05.99'},
    {canonical_version:'999.0.0'},
    {creator_credit:payload.creator_credit==='Open Accounting contributors'?'Open Source Accounting contributors':'Open Accounting contributors'},
  ])await assert.rejects(loadReaderEdition(minimal,fetcher({...payload,...mutation})),/pinned article revision/);
  const changedBody=body+'\nUnknown new source revision.\n';
  const changedReader=payload.body+'\nUnknown new source revision.\n';
  await assert.rejects(loadReaderEdition({...minimal,body:changedBody},fetcher({...payload,canonical_version:'999.0.0',canonical_sha256:hash(changedBody),reader_sha256:hash(changedReader),body:changedReader})),/pinned article revision/);
  await assert.rejects(loadReaderEdition({...minimal,title:'Other title',license:'Other license'},fetcher({...payload,title:'Other title',license:'Other license'})),/pinned article revision/);
  await assert.rejects(loadReaderEdition({...minimal,id:'unknown-article'},fetcher({...payload,item_id:'unknown-article'})),/No pinned reader/);
});

test('build pins the exact supported edition and notice rather than an arbitrary dated version',async()=>{
  const altered=structuredClone(index);altered.reader_edition='2026-10-05.99';
  await assert.rejects(loadReaderEditions(async path=>path==='reader-editions/index.json'?Buffer.from(JSON.stringify(altered)):content(path),manifest,manifestBytes),/unapproved pinned edition/);
  const alteredRules=structuredClone(rules);alteredRules.reader_notice='A fabricated professional approval';
  const ruleBytes=Buffer.from(JSON.stringify(alteredRules));const pairedIndex=structuredClone(index);pairedIndex.rules_sha256=hash(ruleBytes);
  await assert.rejects(loadReaderEditions(async path=>path==='reader-editions/index.json'?Buffer.from(JSON.stringify(pairedIndex)):path==='reader-editions/rules.json'?ruleBytes:content(path),manifest,manifestBytes),/unapproved pinned edition/);
});

test('reader legal links resolve to the exact preserved terms document from repository and download contexts',async()=>{
  const terms='https://github.com/ChipmunkRPA/open-source-accounting/blob/4ffc83f154a152c453438eafe63e8b6b77f27a93/CONTENT-TERMS.md';
  let normalized=0;
  for(const row of index.items){
    const original=await read('content/'+row.canonical_path);const body=await read('content/'+row.reader_path);
    const links=[...body.matchAll(/\]\(([^)]+)\)/g)].map(match=>match[1]);
    for(const link of links)assert.ok(/^https?:\/\/|^#/.test(link),'Unresolved reader-relative link: '+link);
    if(original.includes('../../CONTENT-TERMS.md')){normalized++;assert.ok(body.includes('[CONTENT-TERMS.md]('+terms+')'));}
    assert.equal(await read('frontend/dist/reader-editions/'+row.item_id+'.md'),body);
  }
  assert.equal(normalized,46);
});

test('all active source cards remove only the four exact authoring labels while preserving source-use restrictions',async()=>{
  const references=JSON.parse(await content('references/sources.json')).sources;
  const activeIds=new Set(manifest.items.flatMap(item=>item.source_ids));let changed=0;
  for(const source of references.filter(source=>activeIds.has(source.id))){
    const original=source.review_scope;const shown=readerSourceScope(original);
    assert.ok(!disclosures.test(shown),source.id);
    if(shown!==original){changed++;assert.equal(shown,original.replace('AI-assisted locator check only','Locator check only').replace('AI-assisted selected checks only','Selected checks only'));}
    else assert.equal(shown,original);
  }
  assert.equal(changed,4);
  assert.equal(readerSourceScope('Publisher prohibits AI-assisted processing.'),'Publisher prohibits AI-assisted processing.');
  assert.ok((await read('frontend/src/views/open-library.ts')).includes("readerSourceScope(s.review_scope)"));
});
