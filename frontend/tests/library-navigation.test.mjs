import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {openLibraryView} from '../dist/views/open-library.js';

const root=new URL('../../',import.meta.url);
const read=async path=>(await readFile(new URL(path,root))).toString();
const manifest=JSON.parse(await read('content/manifest.json'));
const item=manifest.items[0];
const body=await read('content/'+item.path);
const reader=JSON.parse(await read('frontend/dist/reader-editions/'+item.id+'.json'));
const tick=()=>new Promise(resolve=>setTimeout(resolve,0));
const pause=()=>new Promise(resolve=>setTimeout(resolve,230));
class FakeNode{
  constructor(tag,text=''){this.tag=tag;this.text=text;this.children=[];this.attrs={};this.events={};this.value='';this.disabled=false;}
  append(...children){for(const child of children){const n=typeof child==='string'?new FakeNode('#text',child):child;this.children.push(n);if(this.tag==='select'&&this.children.length===1)this.value=n.attrs.value;}}
  replaceChildren(...children){this.children=[];this.text='';this.append(...children);}
  setAttribute(k,v){this.attrs[k]=String(v);}
  addEventListener(k,fn){this.events[k]=fn;}
  get textContent(){return this.text+this.children.map(n=>n.textContent).join('');}
  set textContent(v){this.text=String(v);this.children=[];}
  click(event={}){if(this.disabled)return;const e={ctrlKey:false,metaKey:false,preventDefault(){},...event};this.onclick?.(e);this.events.click?.(e);}
}
const all=node=>[node,...node.children.flatMap(all)];
function fixture(start='/library'){
  const old={Node:globalThis.Node,document:globalThis.document,fetch:globalThis.fetch,history:globalThis.history,window:globalThis.window};
  globalThis.Node=FakeNode;
  globalThis.document={createElement:t=>new FakeNode(t),createTextNode:t=>new FakeNode('#text',t),createDocumentFragment:()=>new FakeNode('#fragment'),body:new FakeNode('body')};
  globalThis.window={setTimeout,clearTimeout};
  const entries=[{path:start,state:{}}];let pos=0;let currentRender=Promise.resolve();
  globalThis.history={get state(){return entries[pos].state;},replaceState(state){entries[pos].state=state;},pushState(state,_unused,path){entries.splice(++pos);entries.push({path,state});}};
  const requests=[];const holds=[];let holdNext=false;
  const facets={kinds:['guide','case'],topics:['audit','tax']};
  function list(url){const p=new URL(url,'https://local.test').searchParams;const q=p.get('q')||'';return {facets,total:60,items:Array.from({length:Math.min(24,60-Number(p.get('offset')||0))},(_,i)=>({id:item.id,title:`${q||'all'} result ${Number(p.get('offset')||0)+i}`,kind:'guide',topic:p.get('topic')||'audit',summary:'Synthetic result'}))};}
  const response=data=>({ok:true,status:200,json:async()=>data});
  globalThis.fetch=async url=>{
    requests.push(url);
    if(url==='/assets/reader-editions/'+item.id+'.json')return response(reader);
    if(url==='/api/v1/library/'+item.id)return response({...item,body,sources:[]});
    if(url.startsWith('/api/v1/library?')){
      if(holdNext){holdNext=false;return new Promise((resolve,reject)=>holds.push({url,resolve:()=>resolve(response(list(url))),reject}));}
      return response(list(url));
    }
    throw Error('Unexpected request '+url);
  };
  const app={content:new FakeNode('main'),errors:[],showError(e){this.errors.push(e);},navigate(path,state={}){app.cleanup?.();history.pushState(state,'',path);currentRender=render();}};
  async function render(){const path=entries[pos].path.split('/').filter(Boolean);if(path[0]==='library')await openLibraryView(app,path[1]);else app.content.replaceChildren(new FakeNode('#text','Other page'));}
  const find=(tag,text)=>all(app.content).find(n=>n.tag===tag&&n.textContent===text);
  return {app,entries,requests,holds,find,render,hold(){holdNext=true;},async settled(){await currentRender;await tick();},
    async go(delta){app.cleanup?.();pos+=delta;currentRender=render();await currentRender;await tick();},
    get path(){return entries[pos].path;},restore(){app.cleanup?.();Object.assign(globalThis,old);}};
}

test('list, detail, return link, browser Back/Forward and repeated visits retain per-entry state',async()=>{
 const f=fixture();try{
  await f.render();const q=all(f.app.content).find(n=>n.attrs.id==='library-search');q.value='lease & audit';q.oninput();await pause();await tick();
  const selects=all(f.app.content).filter(n=>n.tag==='select');selects[0].value='guide';selects[0].onchange();await tick();selects[1].value='audit';selects[1].onchange();await tick();
  f.find('button','Next').click();await tick();assert.ok(f.app.content.textContent.includes('25–48 of 60'));
  const read=f.find('a','Read article →');assert.equal(read.attrs.href,'/library/'+item.id);assert.ok(!JSON.stringify(f.entries).includes('lease'));
  read.click();await f.settled();assert.equal(f.path,'/library/'+item.id);assert.ok(f.app.content.textContent.includes(item.title));
  f.find('a','← Open library').click();await f.settled();assert.equal(f.path,'/library');assert.equal(all(f.app.content).find(n=>n.attrs.id==='library-search').value,'lease & audit');assert.ok(f.app.content.textContent.includes('25–48 of 60'));
  assert.deepEqual(all(f.app.content).filter(n=>n.tag==='select').map(n=>n.value),['guide','audit']);
  assert.match(f.requests.at(-1),/q=lease%20%26%20audit&topic=audit&kind=guide&offset=24/);
  const currentQ=all(f.app.content).find(n=>n.attrs.id==='library-search');currentQ.value='new';currentQ.oninput();await pause();await tick();assert.ok(f.app.content.textContent.includes('1–24 of 60'));
  await f.go(-1);assert.equal(f.path,'/library/'+item.id);
  await f.go(-1);assert.equal(all(f.app.content).find(n=>n.attrs.id==='library-search').value,'lease & audit');assert.ok(f.app.content.textContent.includes('25–48 of 60'));
  await f.go(1);await f.go(1);assert.equal(all(f.app.content).find(n=>n.attrs.id==='library-search').value,'new');
  f.find('a','Read article →').click();await f.settled();f.find('a','← Open library').click();await f.settled();assert.equal(all(f.app.content).find(n=>n.attrs.id==='library-search').value,'new');assert.deepEqual(f.app.errors,[]);
 }finally{f.restore();}
});

test('query/filter changes invalidate pending results and late failures, including after leaving',async()=>{
 const f=fixture();try{
  await f.render();const q=all(f.app.content).find(n=>n.attrs.id==='library-search');
  f.hold();q.value='first';q.oninput();await pause();assert.equal(f.holds.length,1);
  q.value='second';q.oninput();f.holds[0].resolve();await tick();assert.ok(!f.app.content.textContent.includes('first result'));assert.equal(f.find('a','Read article →'),undefined);
  await pause();await tick();assert.ok(f.app.content.textContent.includes('second result'));
  f.hold();const kind=all(f.app.content).find(n=>n.tag==='select');kind.value='case';kind.onchange();await tick();assert.equal(f.holds.length,2);
  q.value='third';q.oninput();f.holds[1].reject(Error('obsolete failure'));await tick();assert.deepEqual(f.app.errors,[]);await pause();await tick();assert.ok(f.app.content.textContent.includes('third result'));
  f.hold();f.find('button','Next').click();await tick();assert.equal(f.holds.length,3);f.app.navigate('/other');await f.settled();f.holds[2].resolve();await tick();assert.equal(f.app.content.textContent,'Other page');assert.deepEqual(f.app.errors,[]);
 }finally{f.restore();}
});

test('direct article entry has a clean list and interrupted initial list cannot redraw',async()=>{
 const f=fixture('/library/'+item.id);try{
  await f.render();f.find('a','← Open library').click();await f.settled();assert.equal(all(f.app.content).find(n=>n.attrs.id==='library-search').value,'');assert.ok(f.app.content.textContent.includes('1–24 of 60'));
  f.hold();f.app.navigate('/library');await tick();assert.equal(f.holds.length,1);f.app.navigate('/other');await f.settled();f.holds[0].resolve();await tick();assert.equal(f.app.content.textContent,'Other page');assert.deepEqual(f.app.errors,[]);
 }finally{f.restore();}
});
