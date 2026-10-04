import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {renderDirectory} from '../scripts/build-systems.mjs';

const root=resolve(fileURLToPath(new URL('../..',import.meta.url)));
const read=path=>readFile(resolve(root,path),'utf8');
const brand='Ray Sang’s Annotation';

test('brand sidecar binds all originals without changing credits, hashes or existing CC BY',async()=>{
  const manifest=JSON.parse(await read('content/manifest.json'));
  const policy=JSON.parse(await read('content/annotation-policy.json'));
  assert.equal(policy.annotation_brand,brand);
  assert.equal(policy.professional_review_implied,false);
  assert.equal(policy.source_text_is_annotation,false);
  assert.equal(policy.preserve_prior_licenses,true);
  const baselineIds=new Set(policy.existing_library_items.map(item=>item.id));
  assert.equal(baselineIds.size,78);
  assert.deepEqual(policy.existing_library_items,manifest.items.filter(item=>baselineIds.has(item.id)).map(({id,sha256,license,author})=>({id,sha256,license,author})));
  for(const item of manifest.items.filter(item=>baselineIds.has(item.id))){
    assert.equal(createHash('sha256').update(await read('content/'+item.path)).digest('hex'),item.sha256);
    assert.equal(item.license,'CC-BY-4.0');
  }
});

test('every system card and detail labels our prose without relicensing vendor marks',async()=>{
  const data=JSON.parse(await read('content/systems/catalog.json'));
  const files=renderDirectory(data);
  const cards=files.get('index.html').split('data-system=').slice(1);
  assert.equal(cards.length,data.systems.length);
  for(const html of cards)assert.ok(html.includes(brand));
  for(const item of data.systems){
    const html=files.get(item.id+'.html');
    assert.ok(html.includes(brand));
    assert.ok(html.includes('not personal professional review'));
    assert.ok(html.includes('excluded from that license'));
    assert.ok(html.includes('CC BY 4.0'));
    assert.ok(html.includes('content-terms.txt'));
  }
});

test('original article pages and list prominently label annotations and retain creator credit',async()=>{
  const source=await read('frontend/scripts/build-library.mjs');
  assert.ok(source.includes(`<strong>${brand}</strong>`));
  assert.ok(source.includes('Original credit: ${escape(item.author)}'));
  assert.ok(source.includes('Existing CC BY 4.0 rights and creator credits preserved'));
});

test('publisher notices and exact source passages are not turned into annotations',async()=>{
  assert.ok(!(await read('frontend/src/source-notices.ts')).includes('annotationNotice'));
  assert.ok(!(await read('frontend/src/views/source-reader.ts')).includes('annotationNotice'));
  const sec=await read('frontend/src/views/sec-core.ts');
  assert.ok(sec.includes("annotationNotice('Our context note, separate from the official excerpt')"));
  assert.ok(sec.includes("el('pre',{class:'sec-text'},item.text)"));
});

test('runtime original summaries and case interpretations carry annotation labels',async()=>{
  for(const file of ['open-library','library','sec-comments','asu-tracking']){
    const source=await read(`frontend/src/views/${file}.ts`);
    assert.ok(source.includes('annotationNotice('),file);
  }
  const helper=await read('frontend/src/annotation.ts');
  assert.ok(helper.includes(brand));
  assert.ok(helper.includes('personally wrote or professionally reviewed'));
});

test('terms preserve prior licenses, public domain, exceptions and GitHub grants',async()=>{
  const terms=await read('CONTENT-TERMS.md');
  for(const phrase of ['expressly','Previously issued MIT, CC BY 4.0','Unmarked material is not silently relicensed','17 U.S.C. §105','laws, regulations, judicial decisions','Fair use, fair dealing','GitHub, its affiliates','not an OSI-approved','not reliable technical','not proof of infringement'])assert.ok(terms.includes(phrase),phrase);
  assert.equal(await read('frontend/public/content-terms.txt'),terms);
});

test('robots advisory is rooted in both build output and local server routing',async()=>{
  const robots=await read('robots.txt');
  assert.equal(await read('frontend/public/robots.txt'),robots);
  assert.ok(robots.includes('User-agent: *\nDisallow: /'));
  assert.ok(robots.includes('preserves existing licenses'));
  assert.ok((await read('frontend/scripts/copy-assets.mjs')).includes("'robots.txt','content-terms.txt'"));
  assert.ok((await read('scripts/serve_public.py')).includes("{'/robots.txt', '/content-terms.txt'}"));
});


test('new original annotations have explicit custom terms and preserve authority gates',async()=>{
  const manifest=JSON.parse(await read('content/manifest.json'));
  const policy=JSON.parse(await read('content/annotation-policy.json'));
  const baselineIds=new Set(policy.existing_library_items.map(item=>item.id));
  const additions=manifest.items.filter(item=>!baselineIds.has(item.id));
  assert.ok(additions.length>=12);
  for(const item of additions){
    const body=await read('content/'+item.path);
    assert.equal(item.license,policy.new_explicit_license);
    assert.ok(body.includes(item.license));
    assert.ok(body.includes(brand));
    assert.equal(item.agent_eligible_by_default,false);
    assert.equal(item.technical_review.status,'unreviewed');
    assert.equal(createHash('sha256').update(body).digest('hex'),item.sha256);
  }
  const schema=JSON.parse(await read('content/manifest.schema.json'));
  assert.deepEqual(schema.$defs.Item.properties.license.enum,['CC-BY-4.0',policy.new_explicit_license]);
  assert.ok((await read('frontend/src/views/open-library.ts')).includes("item.license==='CC-BY-4.0'"));
});
