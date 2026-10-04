import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
import {validateCatalog,validateSVG,renderDirectory,safeURL,escape} from '../scripts/build-systems.mjs';
import {normalize,matches,readFilters,filterQuery,mountDirectory} from '../public/systems.js';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const data=JSON.parse(await readFile(resolve(root,'content/systems/catalog.json'),'utf8'));
const clone=()=>structuredClone(data);
const mutate=fn=>{const d=clone();fn(d);return d;};
const record=s=>({search:[s.name,...s.aliases,s.introduction,...s.use_cases,...s.categories].join(' '),categories:s.categories,sizes:s.company_sizes});
test('33 real profiles cover every one of 13 workflows without changing the article corpus',()=>{
 assert.equal(validateCatalog(data),data);assert.equal(data.systems.length,33);assert.equal(data.categories.length,13);
 assert.ok(data.categories.every(c=>data.systems.some(s=>s.categories.includes(c.id))));
 assert.ok(data.systems.filter(s=>!s.categories.includes('erp')).length>=25);
});
for(const [name,fn]of [
 ['duplicate system',d=>d.systems.push(d.systems[0])],['duplicate category',d=>d.categories.push(d.categories[0])],
 ['unknown category',d=>d.systems[0].categories.push('invented')],['empty category',d=>d.categories.push({id:'empty',label:'Empty',description:'No profile'})],
 ['unknown company size',d=>d.systems[0].company_sizes.push('everyone')],['missing provenance',d=>d.systems[0].sources=[]],
 ['invented source role',d=>d.systems[0].sources[0].supports=['independent_test']],['missing product evidence',d=>d.systems[0].sources[0].supports=['identity']],
 ['duplicate source',d=>d.systems[0].sources.push(d.systems[0].sources[0])],['source date mismatch',d=>d.systems[0].sources[0].checked_on='2020-01-01'],
 ['future check date',d=>d.last_checked='2999-01-01'],['impossible date',d=>d.last_checked='2026-02-30'],
 ['unexpected metadata',d=>d.affiliate=true],['unexpected system field',d=>d.systems[0].tracking_url='https://example.com/'],
 ['unreviewed logo path',d=>d.systems[0].logo.path='logos/bill.svg'],['missing logo conditions',d=>d.systems.find(s=>s.logo.path).logo.usage_conditions=''],
 ['logo path traversal',d=>d.systems.find(s=>s.logo.path).logo.path='../private.svg'],['logo asset protocol',d=>d.systems.find(s=>s.logo.path).logo.asset_url='javascript:alert(1)'],
 ['nonhash logo',d=>d.systems.find(s=>s.logo.path).logo.sha256='z'.repeat(64)],['invalid slug',d=>d.systems[0].id='../outside'],
 ['empty use cases',d=>d.systems[0].use_cases=[]],['empty fit',d=>d.systems[0].company_fit=''],['missing integration context',d=>delete d.systems[0].integration_context]
])test(`validation rejects ${name}`,()=>assert.throws(()=>validateCatalog(mutate(fn)),/Systems catalog:/));
for(const url of ['javascript:alert(1)','data:text/html,hi','http://example.com','https://user:pass@example.com/','//example.com','https://example.com:8443/','https://example.com/hello world','https://example.com\\evil','file:///tmp/test'])test(`unsafe URL refused: ${url.split(':')[0]}`,()=>assert.equal(safeURL(url),false));
test('ordinary official HTTPS source is allowed',()=>assert.equal(safeURL('https://example.com/docs?q=finance&v=1'),true));
for(const fragment of ['<script>alert(1)</script>','<image href="https://example.com/a"/>','<foreignObject/>','<path onclick="x()"/>','<path style="fill:url(https://example.com/a)"/>','<!DOCTYPE svg>','<use href="#x"/>','<animate/>'])test(`SVG refuses active or unapproved markup ${fragment.split(' ')[0]}`,()=>assert.throws(()=>validateSVG(`<svg xmlns="http://www.w3.org/2000/svg">${fragment}</svg>`)));
test('official acquired SVGs remain exact and passive',async()=>{
 const logos=data.systems.filter(s=>s.logo.path);assert.equal(logos.length,2);
 assert.deepEqual((await readdir(resolve(root,'content/systems/logos'))).sort(),['chargebee.svg','ramp.svg']);
 for(const s of logos){const bytes=await readFile(resolve(root,'content/systems',s.logo.path));validateSVG(bytes.toString());assert.equal(createHash('sha256').update(bytes).digest('hex'),s.logo.sha256);}
});
test('HTML escapes source descriptions, names and attributes',()=>{
 const d=clone();d.systems[0].name='<img src=x onerror=alert(1)>';d.systems[0].introduction='" onmouseover="alert(1)<script>';
 const files=renderDirectory(d);const html=files.get('index.html');assert.ok(!html.includes('<img src=x'));assert.ok(html.includes('&lt;img'));assert.ok(!html.includes('<script>'));
 assert.equal(escape(`<"'&>`),'&lt;&quot;&#39;&amp;&gt;');
});
test('static output has all details, primary sources, provenance and no external image calls',()=>{
 const files=renderDirectory(data);assert.equal(files.size,35);
 for(const s of data.systems){const html=files.get(s.id+'.html');assert.ok(html.includes(escape(s.introduction)));assert.ok(html.includes(s.last_checked));assert.ok(html.includes('No working connector'));assert.ok(html.includes('Logo & brand provenance'));for(const ref of s.sources)assert.ok(html.includes(escape(ref.url)));}
 for(const html of files.values()){assert.ok(html.includes("connect-src 'none'"));assert.ok(!/<img[^>]+src="https?:/.test(html));assert.ok(!html.includes('affiliate='));}
 assert.equal((files.get('index.html').match(/data-system=/g)||[]).length,33);
});
test('original source language and current naming aliases remain differentiated',()=>{
 assert.ok(data.systems.find(s=>s.id==='optro').aliases.includes('AuditBoard'));
 assert.ok(data.systems.find(s=>s.id==='ripple-treasury').aliases.includes('GTreasury'));
 assert.ok(!data.systems.find(s=>s.id==='workiva').categories.includes('consolidation'));
 assert.ok(data.disclaimer.includes('not hands-on product tests'));
});
test('Unicode and whitespace normalization',()=>assert.equal(normalize('  ＡＲ\n COLLections  '),'ar collections'));
test('multiword search requires every word',()=>{const r=record(data.systems.find(s=>s.id==='highradius'));assert.ok(matches(r,{q:'cash collections',category:'ar',size:'enterprise'}));assert.ok(!matches(r,{q:'cash unicorn',category:'',size:''}));});
test('old vendor names are searchable',()=>{for(const [id,name]of [['optro','AuditBoard'],['ripple-treasury','GTreasury'],['workday-adaptive','Adaptive Insights']])assert.ok(matches(record(data.systems.find(s=>s.id===id)),{q:name,category:'',size:''}));});
test('search, workflow and size filters intersect',()=>{const r=record(data.systems.find(s=>s.id==='quickbooks-online'));assert.ok(matches(r,{q:'',category:'erp',size:'small'}));assert.ok(!matches(r,{q:'',category:'treasury',size:'small'}));assert.ok(!matches(r,{q:'',category:'erp',size:'enterprise'}));});
test('unknown URL filters, tracking keys and oversized queries cannot change the filter contract',()=>{
 const f=readFilters('?category=unknown&size=bogus&tracking=secret&q='+('x'.repeat(500)),['ap']);assert.equal(f.q.length,200);assert.equal(f.category,'');assert.equal(f.size,'');assert.ok(!filterQuery(f).includes('tracking'));
 assert.deepEqual(readFilters('?category=ap&size=small&q=cash',['ap']),{q:'cash',category:'ap',size:'small'});
});
class Element{
 constructor(attrs={}){this.attrs=attrs;this.dataset={};this.value='';this.hidden=false;this.listeners={};this.options=[];this.textContent='';this.focused=false;}
 addEventListener(type,fn){this.listeners[type]=fn;}
 setAttribute(key,value){this.attrs[key]=value;}
 getAttribute(key){return this.attrs[key];}
 focus(){this.focused=true;}
 trigger(type){this.listeners[type]?.({preventDefault(){}});}
}
function fixture(query=''){
 const ids=Object.fromEntries(['system-filters','system-search','system-category','system-size','system-results','system-empty','system-reset','system-empty-reset'].map(id=>[id,new Element()]));
 ids['system-category'].options=[{value:''},...data.categories.map(c=>({value:c.id}))];
 const nodes=data.systems.map(s=>{const e=new Element();const r=record(s);e.dataset={search:r.search,categories:r.categories.join(' '),sizes:r.sizes.join(' ')};return e;});
 const links=data.systems.map(s=>new Element({href:s.id+'.html'}));
 const doc={getElementById:id=>ids[id],querySelectorAll:s=>s==='[data-system]'?nodes:s==='[data-detail-link]'?links:[]};
 const events={};const changes=[];const win={location:{pathname:'/assets/systems/index.html',search:query},history:{},addEventListener:(type,fn)=>events[type]=fn};
 for(const mode of ['push','replace'])win.history[mode+'State']=(_a,_b,url)=>{changes.push([mode,url]);win.location.search=url.includes('?')?'?'+url.split('?')[1]:'';};
 mountDirectory(doc,win);return {ids,nodes,links,doc,win,events,changes,visible:()=>nodes.filter(n=>!n.hidden).length};
}
test('DOM initial query filters and detail links retain safe filters',()=>{
 const f=fixture('?q=AuditBoard&tracking=secret');assert.equal(f.visible(),1);assert.ok(f.links.every(a=>a.attrs.href.endsWith('?q=AuditBoard')));assert.equal(f.ids['system-empty'].hidden,true);
});
test('DOM repeated input, no results, clear and focus',()=>{
 const f=fixture();assert.equal(f.visible(),33);f.ids['system-search'].value='absent-zzzzz';f.ids['system-search'].trigger('input');assert.equal(f.visible(),0);assert.equal(f.ids['system-empty'].hidden,false);
 f.ids['system-empty-reset'].trigger('click');assert.equal(f.visible(),33);assert.equal(f.ids['system-search'].focused,true);f.ids['system-reset'].trigger('click');assert.equal(f.visible(),33);
});
test('DOM category, size, submit, Back and BFCache restoration',()=>{
 const f=fixture();f.ids['system-category'].value='treasury';f.ids['system-category'].trigger('change');assert.ok(f.visible()>0&&f.visible()<33);const treasury=f.visible();
 f.ids['system-size'].value='enterprise';f.ids['system-size'].trigger('change');assert.ok(f.visible()<=treasury);f.ids['system-filters'].trigger('submit');
 f.win.location.search='?q=AuditBoard';f.events.popstate();assert.equal(f.visible(),1);assert.equal(f.ids['system-category'].value,'');
 f.win.location.search='?category=erp&size=small';f.events.pageshow();assert.equal(f.visible(),3);assert.equal(f.ids['system-search'].value,'');
});
test('DOM detail return link drops unrecognized keys and contains only an encoded local query',()=>{
 const a=new Element({href:'index.html'});mountDirectory({getElementById:()=>null,querySelectorAll:()=>[a]},{location:{search:'?category=ap&q=%3Cscript%3E&size=small&token=secret'}});assert.equal(a.attrs.href,'index.html?q=%3Cscript%3E&category=ap&size=small');
});
