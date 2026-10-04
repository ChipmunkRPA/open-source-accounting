import {readFile, writeFile, mkdir, copyFile, realpath, readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, relative, isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';

export const escape = value => String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
const slug = value => typeof value === 'string' && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value);
const fail = message => {throw new Error('Systems catalog: '+message);};
const fields = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === keys.length && keys.every(k=>Object.hasOwn(value,k));
const strings = (values,min=1) => Array.isArray(values) && values.length>=min && values.every(v=>typeof v==='string' && v.trim().length>0 && v.length<2000) && new Set(values).size===values.length;
const date = value => typeof value==='string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0,10)===value && value<=new Date().toISOString().slice(0,10);
export function safeURL(value){
  if(typeof value!=='string' || value.length>1800 || /[\s\\\u0000-\u001f]/.test(value))return false;
  try{const u=new URL(value);return u.protocol==='https:' && !u.username && !u.password && !!u.hostname && !u.port;}catch{return false;}
}
export function validateCatalog(data){
  if(!fields(data,['schema_version','version','last_checked','title','license','disclaimer','categories','systems']) || data.schema_version!==1 || !/^\d+\.\d+\.\d+$/.test(data.version) || !date(data.last_checked))fail('invalid release metadata');
  if(!strings([data.title,data.license,data.disclaimer]))fail('missing release text');
  if(!Array.isArray(data.categories)||!data.categories.length||!Array.isArray(data.systems)||!data.systems.length)fail('empty directory');
  const categories=new Set();const ids=new Set();
  for(const c of data.categories){
    if(!fields(c,['id','label','description'])||!slug(c.id)||categories.has(c.id)||!strings([c.label,c.description]))fail('invalid or duplicate category');
    categories.add(c.id);
  }
  const coverage=new Set();
  for(const s of data.systems){
    if(!fields(s,['id','name','aliases','categories','company_sizes','website','introduction','use_cases','company_fit','integration_context','evaluation_questions','last_checked','sources','logo']))fail('unexpected system fields');
    if(!slug(s.id)||ids.has(s.id))fail('invalid or duplicate system ID');ids.add(s.id);
    if(!strings([s.name,s.introduction,s.company_fit,s.integration_context])||!strings(s.aliases,0)||!strings(s.use_cases)||!strings(s.evaluation_questions))fail('missing system text');
    if(!strings(s.categories)||s.categories.some(c=>!categories.has(c)))fail('unknown category');s.categories.forEach(c=>coverage.add(c));
    if(!strings(s.company_sizes)||s.company_sizes.some(c=>!['small','midsize','enterprise'].includes(c)))fail('unknown company size');
    if(!safeURL(s.website)||!date(s.last_checked)||s.last_checked>data.last_checked)fail('invalid website or date');
    if(!Array.isArray(s.sources)||!s.sources.length)fail('missing primary sources');
    const urls=new Set();
    for(const ref of s.sources){
      if(!fields(ref,['label','url','checked_on','supports'])||!strings([ref.label])||!safeURL(ref.url)||urls.has(ref.url)||!date(ref.checked_on)||ref.checked_on!==s.last_checked||!strings(ref.supports)||ref.supports.some(x=>!['product_scope','integration_context','identity'].includes(x)))fail('invalid source');
      urls.add(ref.url);
    }
    if(!s.sources.some(r=>r.supports.includes('product_scope')))fail('missing product-scope source');
    const l=s.logo;
    if(!fields(l,['status','source_page','asset_url','path','sha256','usage_conditions','checked_on'])||!safeURL(l.source_page)||!strings([l.usage_conditions])||!date(l.checked_on)||l.checked_on!==s.last_checked)fail('invalid logo provenance');
    if(l.status==='official_media_asset'){
      if(l.path!==`logos/${s.id}.svg`||!safeURL(l.asset_url)||!/^\w{64}$/.test(l.sha256)||!/^[0-9a-f]+$/.test(l.sha256))fail('invalid official logo');
    }else if(l.status!=='pending_review'||l.path!==null||l.asset_url!==null||l.sha256!==null)fail('unreviewed logo must not be displayed');
  }
  if(coverage.size!==categories.size)fail('empty category');return data;
}
export function validateSVG(text){
  if(!text.startsWith('<svg ')||!text.trimEnd().endsWith('</svg>')||/<!|<\?|\bon\w+\s*=|\bhref\s*=|\bstyle\s*=|url\(\s*(?!#)/i.test(text))fail('active or external SVG content');
  const tags=[...text.matchAll(/<\/?([\w:-]+)\b/g)].map(m=>m[1]);
  if(tags.some(tag=>!['svg','g','path','defs','clipPath','rect','circle','ellipse','polygon','polyline','line','title','desc'].includes(tag)))fail('unsupported SVG element');
}
const sizeNames={small:'Small business',midsize:'Midsize',enterprise:'Enterprise'};
const list=values=>`<ul>${values.map(v=>`<li>${escape(v)}</li>`).join('')}</ul>`;
const external=(url,label)=>`<a href="${escape(url)}" rel="noreferrer noopener">${escape(label)} <span aria-hidden="true">↗</span></a>`;
const logo=s=>s.logo.path?`<div class="vendor-logo"><img src="${escape(s.logo.path)}" alt="${escape(s.name)} official logo" width="150" height="44"></div>`:`<div class="vendor-text">${escape(s.name)}</div>`;
export function renderDirectory(data){
  const cats=new Map(data.categories.map(c=>[c.id,c]));
  const tags=s=>`<div class="tags">${s.categories.map(id=>`<span>${escape(cats.get(id).label)}</span>`).join('')}</div>`;
  const shell=(title,body,detail=false)=>`<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'none'; base-uri 'none'; form-action 'self'"><meta name="description" content="Free independent directory of accounting systems across finance workflows, with original introductions and official sources."><title>${escape(title)} · Open Source Accounting</title><link rel="stylesheet" href="systems.css"></head>
<body><a class="skip" href="#main">Skip to content</a><header><a class="brand" href="/">Open Source Accounting</a><span class="edition">Standard / Free</span><nav aria-label="Directory navigation"><a href="../library/index.html">Original library</a><a href="index.html" ${detail?'':'aria-current="page"'}>Systems</a></nav></header><main id="main">${body}</main><footer><p><strong>Ray Sang’s Annotation</strong> identifies our original explanations only. It does not imply that Ray Sang personally reviewed them. <a href="/content-terms.txt">Content rights and automated-access terms</a></p><p>${escape(data.disclaimer)}</p><p>The directory is free. Vendor products have their own pricing and terms. Original editorial text: <a href="https://creativecommons.org/licenses/by/4.0/" rel="noreferrer">CC BY 4.0</a>, Open Source Accounting contributors. Vendor names and logos remain their owners’ property and are excluded from that license.</p><p>Release ${escape(data.version)} · Research checked ${escape(data.last_checked)} · <a href="methodology.html">Research & logo policy</a></p></footer><script type="module" src="systems.js"></script></body></html>`;
  const options=(pairs)=>pairs.map(([v,l])=>`<option value="${escape(v)}">${escape(l)}</option>`).join('');
  const sorted=[...data.systems].sort((a,b)=>a.name.localeCompare(b.name,'en'));
  const cards=sorted.map(s=>{
    const search=[s.name,...s.aliases,...s.categories.map(id=>cats.get(id).label),s.introduction,...s.use_cases,s.integration_context].join(' ');
    return `<article class="system-card" data-system="${escape(s.id)}" data-search="${escape(search)}" data-categories="${escape(s.categories.join(' '))}" data-sizes="${escape(s.company_sizes.join(' '))}">${logo(s)}<h2><a data-detail-link href="${s.id}.html">${escape(s.name)}</a></h2>${s.aliases.length?`<p class="aliases">Also searchable as ${escape(s.aliases.join(', '))}</p>`:''}${tags(s)}<p class="annotation-brand"><strong>Ray Sang’s Annotation</strong> · AI-assisted editorial description</p><p class="summary">${escape(s.introduction)}</p><p class="fit">${escape(s.company_sizes.map(id=>sizeNames[id]).join(' · '))}<span>Editorial fit, not eligibility</span></p><a class="card-link" data-detail-link href="${s.id}.html">Explore profile <span aria-hidden="true">→</span></a></article>`;
  }).join('\n');
  const body=`<section class="hero"><p class="eyebrow">The finance technology landscape</p><h1>Find the systems<br>behind the numbers.</h1><p class="lede">Explore the whole finance stack, from purchasing and receivables to the close, planning and core accounting.</p><div class="stats"><div><strong>${data.systems.length}</strong><span>system profiles</span></div><div><strong>${data.categories.length}</strong><span>workflow categories</span></div><div><strong>Free</strong><span>to explore, no sign-in</span></div></div></section><section aria-label="Browse systems"><form id="system-filters" class="filters" role="search"><label class="search-label">Search systems<input id="system-search" name="q" type="search" maxlength="200" placeholder="Try collections, revenue, NetSuite…" autocomplete="off"></label><label>Workflow<select id="system-category" name="category">${options([['','All workflows'],...data.categories.map(c=>[c.id,c.label])])}</select></label><label>Company size<select id="system-size" name="size">${options([['','All sizes'],...Object.entries(sizeNames)])}</select></label><button type="submit">Search</button><button id="system-reset" type="button" class="secondary">Clear</button></form><p id="system-results" class="results" role="status" aria-live="polite">${data.systems.length} systems · Alphabetical order · Company fit is editorial guidance</p><noscript><p>All profiles and source links are available below. Search and filtering require JavaScript.</p></noscript><div class="cards" id="system-cards">${cards}</div><div id="system-empty" class="empty" hidden><h2>No matching systems</h2><p>Try a shorter search or clear one of the filters.</p><button id="system-empty-reset" type="button">Clear filters</button></div></section><section class="workflow-guide"><h2>Start with the workflow</h2><div class="guide-grid">${data.categories.map(c=>`<article><p class="annotation-brand">Ray Sang’s Annotation</p><h3><a href="?category=${c.id}">${escape(c.label)}</a></h3><p>${escape(c.description)}</p></article>`).join('')}</div></section>`;
  const files=new Map([['index.html',shell('Accounting systems directory',body)]]);
  for(const s of sorted){
    const sourceLinks=s.sources.map(r=>`<li>${external(r.url,r.label)}<span class="source-note">Checked ${escape(r.checked_on)} · ${escape(r.supports.join(', ').replaceAll('_',' '))}</span></li>`).join('');
    files.set(`${s.id}.html`,shell(s.name,`<a class="back" data-directory-link href="index.html">← Back to all systems</a><div class="profile-heading">${logo(s)}<p class="eyebrow">Ray Sang’s Annotation · System profile / independent research</p><h1>${escape(s.name)}</h1>${s.aliases.length?`<p class="aliases">Also known as ${escape(s.aliases.join(', '))}</p>`:''}${tags(s)}<p class="lede">${escape(s.introduction)}</p><p>${external(s.website,'Visit official website')}</p></div><p class="annotation-brand"><strong>Ray Sang’s Annotation</strong> · Our descriptions, interpretations and examples below are AI-assisted, not personal professional review. Official source titles, vendor text and marks retain their original attribution.</p><div class="profile-grid"><div><section><h2>Where it fits</h2><p>${escape(s.company_fit)}</p><p class="muted">Company-size fit is an editorial assessment. It is not a vendor eligibility rule or a product recommendation.</p></section><section><h2>Example use cases</h2>${list(s.use_cases)}<p class="muted">Illustrative evaluation scenarios, not tested implementations.</p></section><section><h2>Integration context</h2><p>${escape(s.integration_context)}</p><div class="note">No working connector, vendor partnership or integration with Open Source Accounting is represented by this profile.</div></section><section><h2>Questions for an evaluation</h2>${list(s.evaluation_questions)}</section></div><aside><section><h2>Research record</h2><p>Last checked: <time datetime="${s.last_checked}">${s.last_checked}</time></p><ul class="source-list">${sourceLinks}</ul><p class="muted">Based on official public vendor materials. No hands-on product test or independent performance verification.</p></section><section><h2>Logo & brand provenance</h2><p class="brand-status">${s.logo.path?'Official media-kit asset':'Text name shown · logo review pending'}</p><p>${escape(s.logo.usage_conditions)}</p><p>${external(s.logo.source_page,'Official identity / brand source')}</p>${s.logo.asset_url?`<p>${external(s.logo.asset_url,'Vendor asset download')}</p><details><summary>Asset integrity</summary><p class="hash">SHA-256 ${s.logo.sha256}</p></details>`:''}<p class="muted">Names and marks identify their owners. They do not imply affiliation or endorsement and are not covered by our CC BY or MIT licenses.</p></section></aside></div>`,true));
  }
  files.set('methodology.html',shell('Research & logo policy',`<a class="back" data-directory-link href="index.html">← Back to all systems</a><h1>Research & logo policy</h1><div class="methodology"><h2>A starting point for learning</h2><p>${escape(data.disclaimer)}</p><p>Profiles use original, concise explanations of the role each system plays. Vendor performance statistics, promises of compliance and promotional rankings are deliberately excluded. Examples and company-size fit are editorial assessments. Categories overlap and are not feature-entitlement guarantees.</p><h2>Primary sources and dates</h2><p>Each profile links the official pages examined and the check date. Those pages can change. A website or documentation reference is not proof that a purchased edition supports a particular workflow; verify scope, country availability, costs and interfaces before deciding.</p><h2>Marks are not open-source assets</h2><p>${data.systems.filter(s=>s.logo.path).length} official media-kit logo files are included with source URLs, SHA-256 hashes and usage conditions. Other profiles use plain text while logo permission or access remains unresolved. No third-party logo service, invented mark, favicon substitution or remote image hotlink is used.</p><p>Included logos are preserved byte-for-byte and rendered on a plain light background with clear space. They remain subject to vendor rights and usage conditions. They must not be reused as our own branding, altered or treated as MIT/CC BY artwork. This record is a research trail, not a legal opinion or a general redistribution license.</p><h2>Coverage and independence</h2><p>This is a representative first release of ${data.systems.length} systems across ${data.categories.length} categories, not a complete market catalog. No paid placement, ranking, referral links or partnership claims are included. No real integrations, financial transactions, sign-ins or product trials were performed to create these descriptions.</p></div>`));
  return files;
}
export async function buildSystems(repository=resolve('..')){
  const root=await realpath(resolve(repository,'content/systems'));
  const raw=await readFile(resolve(root,'catalog.json'),'utf8');
  const data=validateCatalog(JSON.parse(raw));
  const output=resolve(repository,'frontend/dist/systems');await mkdir(output,{recursive:true});
  const expected=new Set(data.systems.filter(s=>s.logo.path).map(s=>s.logo.path.slice(6)));
  const actual=await readdir(resolve(root,'logos'));
  if(actual.length!==expected.size||actual.some(x=>!expected.has(x)))fail('unexpected logo file');
  for(const s of data.systems.filter(s=>s.logo.path)){
    const path=await realpath(resolve(root,s.logo.path));const rel=relative(root,path);
    if(isAbsolute(rel)||rel==='..'||rel.startsWith('../'))fail('logo escapes content root');
    const bytes=await readFile(path);
    if(createHash('sha256').update(bytes).digest('hex')!==s.logo.sha256)fail('logo hash mismatch');
    validateSVG(bytes.toString('utf8'));await mkdir(resolve(output,'logos'),{recursive:true});await copyFile(path,resolve(output,s.logo.path));
  }
  for(const [name,html]of renderDirectory(data))await writeFile(resolve(output,name),html);
  for(const name of ['systems.js','systems.css'])await copyFile(resolve(repository,'frontend/public',name),resolve(output,name));
  console.log(`Built ${data.systems.length} systems, ${data.categories.length} categories, ${expected.size} official media-kit logos; ${data.systems.length-expected.size} text-only logo records.`);
  return data;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))await buildSystems();
