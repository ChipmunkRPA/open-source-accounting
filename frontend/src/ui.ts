import type {App} from './types.js';
type Child=Node|string|number|null|undefined|false;
export function el<K extends keyof HTMLElementTagNameMap>(tag:K,attrs:Record<string,string|boolean|number>={},...children:Child[]):HTMLElementTagNameMap[K]{
  const node=document.createElement(tag);
  for(const [key,value]of Object.entries(attrs)){
    if(value===false)continue;
    if(key==='class')node.className=String(value);else node.setAttribute(key,value===true?'':String(value));
  }
  for(const c of children)if(c!==null && c!==undefined && c!==false)node.append(c instanceof Node?c:document.createTextNode(String(c)));
  return node;
}
export function button(label:string,fn:()=>unknown,variant='primary'):HTMLButtonElement{
  const b=el('button',{type:'button',class:`button ${variant}`},label);b.addEventListener('click',()=>{void fn();});return b;
}
export function link(app:App,label:string,path:string,cls=''):HTMLAnchorElement{
  const a=el('a',{href:path,class:cls},label);a.onclick=e=>{if(!e.ctrlKey&&!e.metaKey){e.preventDefault();app.navigate(path);}};return a;
}
export function heading(title:string,subtitle:string,action?:HTMLElement){
  return el('div',{class:'page-heading'},el('div',{},el('h1',{},title),el('p',{class:'muted'},subtitle)),action);
}
export function badge(text:string,kind='neutral'){return el('span',{class:`badge ${kind}`},text);}
export function notice(text:string,kind='info'){return el('div',{class:`notice ${kind}`,role:kind==='error'?'alert':'status'},text);}
export function card(title:string,...content:Child[]){return el('section',{class:'card'},el('h2',{},title),...content);}
export function field(label:string,input:HTMLElement,help=''){
  const id=input.id||'field-'+crypto.randomUUID();input.id=id;
  return el('div',{class:'field'},el('label',{for:id},label),input,help?el('small',{class:'muted'},help):null);
}
export function input(type='text',value='',id=''){
  const n=el('input',{type,id});n.value=value;return n;
}
export function textarea(value='',id='',rows=5){const n=el('textarea',{id,rows});n.value=value;return n;}
export function select(options:[string,string][],value='',id=''){
  const n=el('select',{id});for(const [v,label] of options)n.append(el('option',{value:v},label));if(value)n.value=value;return n;
}
export function checkbox(label:string,checked=false){
  const i=input('checkbox');i.checked=checked;
  return {input:i,element:el('label',{class:'checkbox'},i,el('span',{},label))};
}
export function modal(title:string,...nodes:Child[]){
  const dialog=el('dialog',{class:'modal','aria-label':title});
  const close=button('Close',()=>dialog.close(),'quiet');
  dialog.append(el('div',{class:'modal-head'},el('h2',{},title),close));
  for(const n of nodes) if(n!==null && n!==undefined && n!==false) dialog.append(n instanceof Node?n:String(n));
  const previouslyFocused=document.activeElement as HTMLElement|null;
  dialog.addEventListener('close',()=>{dialog.remove();previouslyFocused?.focus();});
  document.body.append(dialog);dialog.showModal();return dialog;
}
export function busy(b:HTMLButtonElement,state:boolean,label='Working…'){
  if(state){b.dataset.label=b.textContent||'';b.textContent=label;b.disabled=true;}
  else {b.textContent=b.dataset.label||b.textContent;b.disabled=false;}
}
export function empty(title:string,description:string,action?:HTMLElement){
  return el('div',{class:'empty'},el('h2',{},title),el('p',{class:'muted'},description),action);
}
export function dateText(value:number|null|undefined){return value?new Date(value*1000).toLocaleDateString(undefined,{dateStyle:'medium'}):'—';}
export function table(columns:string[],rows:(string|number|HTMLElement)[][]){
  const t=el('table');t.append(el('thead',{},el('tr',{},...columns.map(c=>el('th',{scope:'col'},c)))));
  t.append(el('tbody',{},...rows.map(row=>el('tr',{},...row.map(c=>el('td',{},c))))));
  return el('div',{class:'table-scroll',tabindex:0,role:'region','aria-label':columns.join(', ')},t);
}
export function textBlock(text:string){return el('div',{class:'prose'},...text.split(/\n\n+/).map(p=>el('p',{},p)));}
export function errorBox(app:App,error:unknown){app.showError(error);}
