// No network calls, analytics or vendor SDKs. Filtering runs on the built snapshot.
export const normalize=value=>String(value).normalize('NFKC').toLocaleLowerCase('en').replace(/\s+/gu,' ').trim();
export function readFilters(search, categories){
  const params=new URLSearchParams(search);
  const category=params.get('category')||'';const size=params.get('size')||'';
  return {q:(params.get('q')||'').slice(0,200),category:categories.includes(category)?category:'',size:['small','midsize','enterprise'].includes(size)?size:''};
}
export function matches(record,filters){
  const words=normalize(filters.q).split(' ').filter(Boolean);
  return words.every(word=>normalize(record.search).includes(word))&&(!filters.category||record.categories.includes(filters.category))&&(!filters.size||record.sizes.includes(filters.size));
}
export function filterQuery(filters){
  const params=new URLSearchParams();if(filters.q.trim())params.set('q',filters.q.trim());if(filters.category)params.set('category',filters.category);if(filters.size)params.set('size',filters.size);return params.toString();
}
export function mountDirectory(doc,win){
  const form=doc.getElementById('system-filters');
  if(!form){
    const state=readFilters(win.location.search,[]); // Only safe query keys are retained in a return link.
    const params=new URLSearchParams(win.location.search);const category=params.get('category')||'';
    if(/^[a-z0-9-]{1,40}$/.test(category))state.category=category;
    const query=filterQuery(state);
    for(const a of doc.querySelectorAll('[data-directory-link]'))a.setAttribute('href','index.html'+(query?'?'+query:''));
    return;
  }
  const search=doc.getElementById('system-search');const category=doc.getElementById('system-category');const size=doc.getElementById('system-size');
  const status=doc.getElementById('system-results');const empty=doc.getElementById('system-empty');
  const categories=Array.from(category.options).map(o=>o.value).filter(Boolean);
  const cards=Array.from(doc.querySelectorAll('[data-system]')).map(node=>({node,search:node.dataset.search||'',categories:(node.dataset.categories||'').split(' '),sizes:(node.dataset.sizes||'').split(' ')}));
  const current=()=>({q:search.value.slice(0,200),category:category.value,size:size.value});
  function apply(mode){
    const filters=current();const query=filterQuery(filters);let count=0;
    for(const card of cards){const show=matches(card,filters);card.node.hidden=!show;if(show)count++;}
    status.textContent=`${count} of ${cards.length} systems · Alphabetical order · Company fit is editorial guidance`;empty.hidden=count!==0;
    for(const a of doc.querySelectorAll('[data-detail-link]')){
      const path=a.getAttribute('href').split('?')[0];a.setAttribute('href',path+(query?'?'+query:''));
    }
    if(mode){const url=win.location.pathname+(query?'?'+query:'');if(url!==win.location.pathname+win.location.search)win.history[mode+'State']({},'',url);}
  }
  function restore(){const state=readFilters(win.location.search,categories);search.value=state.q;category.value=state.category;size.value=state.size;apply();}
  function clear(){search.value='';category.value='';size.value='';apply('push');search.focus();}
  form.addEventListener('submit',event=>{event.preventDefault();apply('push');});
  search.addEventListener('input',()=>apply('replace'));
  category.addEventListener('change',()=>apply('push'));size.addEventListener('change',()=>apply('push'));
  doc.getElementById('system-reset').addEventListener('click',clear);doc.getElementById('system-empty-reset').addEventListener('click',clear);
  win.addEventListener('popstate',restore);win.addEventListener('pageshow',restore);restore();
}
if(typeof document!=='undefined')mountDirectory(document,window);
