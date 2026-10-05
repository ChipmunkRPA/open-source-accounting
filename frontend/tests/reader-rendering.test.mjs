import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const root=new URL('../../',import.meta.url);
const read=async path=>(await readFile(new URL(path,root))).toString();
const manifest=JSON.parse(await read('content/manifest.json'));
const sources=new Map(JSON.parse(await read('content/references/sources.json')).sources.map(s=>[s.id,s]));
const {openLibraryView}=await import(new URL('frontend/dist/views/open-library.js',root));
class FakeNode {
 constructor(tag,text=''){this.tag=tag;this.text=text;this.children=[];this.attrs={};this.events={};this.className='';}
 append(...nodes){for(const n of nodes)this.children.push(typeof n==='string'?new FakeNode('#text',n):n);}
 replaceChildren(...nodes){this.children=[];this.append(...nodes);}
 setAttribute(k,v){this.attrs[k]=v;}
 addEventListener(k,v){this.events[k]=v;}
 get textContent(){return this.text+this.children.map(n=>n.textContent).join('');}
 set textContent(value){this.text=String(value);this.children=[];}
 remove(){}
 click(){if(this.tag==='a'&&this.attrs.download)downloads.push({name:this.attrs.download,blob:blobs.get(this.attrs.href)});this.events.click?.();}
}
const blobs=new Map();const downloads=[];
const saved={Node:globalThis.Node,document:globalThis.document,fetch:globalThis.fetch,create:URL.createObjectURL,revoke:URL.revokeObjectURL};
const all=n=>[n,...n.children.flatMap(all)];let count=0;const failures=[];
try{
 globalThis.Node=FakeNode;
 globalThis.document={createElement:tag=>new FakeNode(tag),createTextNode:text=>new FakeNode('#text',text),createDocumentFragment:()=>new FakeNode('#fragment'),body:new FakeNode('body')};
 URL.createObjectURL=blob=>{const id='blob:reader-test-'+blobs.size;blobs.set(id,blob);return id;};URL.revokeObjectURL=()=>{};
 for(const item of manifest.items){
  const original=await read('content/'+item.path);const payload=JSON.parse(await read('frontend/dist/reader-editions/'+item.id+'.json'));
  const sourceRows=item.source_ids.map(id=>sources.get(id));
  globalThis.fetch=async url=>{
   if(url==='/api/v1/library/'+item.id)return {ok:true,status:200,json:async()=>({...item,body:original,sources:sourceRows})};
   if(url==='/assets/reader-editions/'+item.id+'.json')return {ok:true,json:async()=>payload};
   throw Error('Unexpected request: '+url);
  };
  const content=new FakeNode('main');const app={content,navigate(){},showError(e){throw e;}};
  await openLibraryView(app,item.id);
  const text=content.textContent;const bad=text.match(/AI-assisted|AI editorial|\bastra\b|\bgpt-|model knowledge|model-generated/ig);
  if(bad)failures.push({item:item.id,bad});
  assert.ok(text.includes('Ray Sang Annotation'),item.id+' missing brand');
  assert.ok(text.includes('UNREVIEWED'),item.id+' missing unreviewed warning');
  for(const source of sourceRows)assert.ok(all(content).some(n=>n.tag==='a'&&n.attrs.href===source.url),item.id+' source link missing');
  const button=all(content).find(n=>n.tag==='button'&&n.textContent==='Download Markdown');assert.ok(button,item.id+' download button missing');
  button.click();const download=downloads.at(-1);assert.equal(download.name,item.id+'.md');assert.equal(await download.blob.text(),payload.body);
  count++;
 }
}finally{globalThis.Node=saved.Node;globalThis.document=saved.document;globalThis.fetch=saved.fetch;URL.createObjectURL=saved.create;URL.revokeObjectURL=saved.revoke;}
console.log(JSON.stringify({rendered_articles:count,download_clicks:downloads.length,source_links_preserved:true,neutral_label_failures:failures},null,2));
assert.deepEqual(failures,[],'Rendered source provenance must also use neutral authoring labels');
