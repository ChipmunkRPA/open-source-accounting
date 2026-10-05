import {loadReaderEditions,readerPayload} from './read-reader-editions.mjs';
import {readFile,writeFile,mkdir,realpath} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve,relative,isAbsolute} from 'node:path';
const root=await realpath(resolve('../content'));
const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
function parse(bytes){
 const text=bytes.toString('utf8');const result=JSON.parse(text,(_key,v)=>{if(typeof v==='number'&&!Number.isFinite(v))throw Error('Non-finite public JSON number');return v;});let position=0;
 const space=()=>{while(/\s/.test(text[position]??'')&&position<text.length)position++;};
 const string=()=>{const start=position++;while(text[position]!=='"'){if(text[position]==='\\')position++;position++;}position++;return JSON.parse(text.slice(start,position));};
 function scan(){
  space();const token=text[position];
  if(token==='{'){
   position++;space();const keys=new Set();
   if(text[position]!=='}')while(true){
    space();const key=string();if(keys.has(key))throw Error('Duplicate public JSON key');keys.add(key);
    space();position++;scan();space();if(text[position]!==',')break;position++;
   }
   position++;
  }else if(token==='['){
   position++;space();if(text[position]!==']')while(true){scan();space();if(text[position]!==',')break;position++;}position++;
  }else if(token==='"')string();
  else while(position<text.length&&!/[\s,}\]]/.test(text[position]))position++;
 }
 scan();return result;
}
function sameCalculation(a,b){
 // Decimal spellings include signed/signalling NaNs and diagnostic digits.
 // Reject them before literal equality, including underscores accepted by
 // some decimal parsers; equal non-finite spellings are never a passing check.
 if([a,b].some(v=>/^[+-]?(?:s?nan\p{Decimal_Number}*|inf(?:inity)?)$/iu.test(v.trim().replaceAll('_',''))))return false;
 if(a===b)return true;
 const normalize=value=>{
  const m=/^([+-]?)(\d+)(?:\.(\d*))?$/.exec(value);if(!m)return null;
  const integer=m[2].replace(/^0+(?=\d)/,'');const fraction=(m[3]??'').replace(/0+$/,'');
  return (m[1]==='-'&&(integer!=='0'||fraction)?'-':'')+integer+(fraction?'.'+fraction:'');
 };
 return normalize(a)!==null&&normalize(a)===normalize(b);
}
const canonical=value=>JSON.stringify(value,(_key,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
async function content(path){
 if(typeof path!=='string'||isAbsolute(path)||path.split(/[\\/]/).some(p=>p==='..'||p==='.'||!p))throw Error('Invalid public content path');
 const file=await realpath(resolve(root,path));const rel=relative(root,file);
 if(rel==='..'||rel.startsWith('../')||isAbsolute(rel))throw Error('Content escapes public root');
 return readFile(file);
}
// The public JSON schemas describe data only. This small build-time validator
// covers their keywords without importing a private runtime or a new dependency.
function valid(s,v,defs){
 if(s.$ref)return valid(defs[s.$ref.split('/').at(-1)],v,defs);
 if(s.anyOf&&!s.anyOf.some(x=>valid(x,v,defs)))return false;
 if('const'in s&&v!==s.const||s.enum&&!s.enum.includes(v))return false;
 const type=v===null?'null':Array.isArray(v)?'array':typeof v;
 if(s.type&&s.type!==type&&!(s.type==='integer'&&Number.isInteger(v)))return false;
 if(type==='string'&&(v.length<(s.minLength??0)||v.length>(s.maxLength??Infinity)||s.pattern&&!new RegExp(s.pattern).test(v)))return false;
 if(type==='array'&&(v.length<(s.minItems??0)||v.length>(s.maxItems??Infinity)||s.items&&!v.every(x=>valid(s.items,x,defs))))return false;
 if(type==='object'){
  if(s.required?.some(k=>!Object.hasOwn(v,k)))return false;
  if(s.additionalProperties===false&&Object.keys(v).some(k=>!Object.hasOwn(s.properties??{},k)))return false;
  if(Object.entries(s.properties??{}).some(([k,p])=>Object.hasOwn(v,k)&&!valid(p,v[k],defs)))return false;
 }
 return true;
}
const manifestBytes=await content('manifest.json');
const manifest=parse(manifestBytes);
const manifestSchema=parse(await content('manifest.schema.json'));
if(!valid(manifestSchema,manifest,manifestSchema.$defs))throw Error('Invalid public manifest');
const items=new Map(manifest.items.map(item=>[item.id,item]));
if(items.size!==manifest.items.length)throw Error('Duplicate public item');
const references=parse(await content('references/sources.json')).sources;
const referenceMap=new Map(references.map(source=>[source.id,source]));
if(referenceMap.size!==references.length)throw Error('Duplicate source reference');
const index=parse(await content('ai_reviews/manifest.json'));
const indexSchema=parse(await content('ai_reviews/index.schema.json'));
const receiptSchema=parse(await content('ai_reviews/receipt.schema.json'));
if(!valid(indexSchema,index,indexSchema.$defs))throw Error('Invalid AI editorial index');
const reviews=new Map();
const readerEditions=await loadReaderEditions(content,manifest,manifestBytes,parse);
for(const entry of index.reviews){
 const item=items.get(entry.item_id);
 if(!item||reviews.has(item.id)||entry.version!==item.version||entry.content_sha256!==item.sha256)throw Error('AI editorial article mismatch');
 const snapshot=[...item.source_ids].sort().map(id=>{if(!referenceMap.has(id))throw Error('Missing source reference');return referenceMap.get(id);});
 if(hash(canonical(snapshot))!==entry.references_sha256)throw Error('AI editorial reference mismatch');
 if(entry.receipt_path!==`ai_reviews/${item.id}-${item.version}.json`||!entry.input_path.endsWith('.md'))throw Error('Invalid AI editorial paths');
 const bytes=await content(entry.receipt_path);const receipt=parse(bytes);
 if(hash(bytes)!==entry.receipt_sha256||hash(await content(entry.input_path))!==entry.input_sha256)throw Error('AI editorial retained-data hash mismatch');
 if(!valid(receiptSchema,receipt,receiptSchema.$defs)||receipt.item_id!==item.id||receipt.input_sha256!==entry.input_sha256||receipt.output_sha256!==item.sha256)throw Error('Invalid AI editorial receipt');
 const reviewed=Date.parse(receipt.reviewed_at_utc);
 if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)$/.test(receipt.reviewed_at_utc)||receipt.reviewed_at_utc.startsWith('0000-')||!Number.isFinite(reviewed)||new Date(reviewed).toISOString().slice(0,19)!==receipt.reviewed_at_utc.slice(0,19)||reviewed>Date.now()+300000)throw Error('Invalid AI editorial review date');
 const reviewedIds=receipt.reviewed_sources.map(s=>s.reference_id);
 if(canonical([...new Set(reviewedIds)].sort())!==canonical([...item.source_ids].sort()))throw Error('Incomplete AI editorial source coverage');
 const claims=new Set(receipt.findings.map(f=>f.claim_id));
 if(claims.size!==receipt.findings.length)throw Error('Duplicate AI editorial finding');
 if(receipt.reviewed_sources.some(source=>source.checked_claim_ids.some(id=>!claims.has(id))))throw Error('Unknown checked AI editorial claim');
 if(receipt.findings.some(finding=>finding.source_reference_ids.some(id=>!reviewedIds.includes(id))))throw Error('Unrecorded AI editorial finding source');
 const modelRecorded=receipt.model_id!==undefined&&receipt.model_id!==null;
 const effortRecorded=receipt.reasoning_effort!==undefined&&receipt.reasoning_effort!==null;
 if(modelRecorded!==effortRecorded)throw Error('Incomplete AI editorial model settings');
 const arithmeticIds=new Set();
 for(const check of receipt.arithmetic_checks){
  if(arithmeticIds.has(check.check))throw Error('Duplicate AI editorial arithmetic check');
  arithmeticIds.add(check.check);
  const hasResult=check.result!==undefined&&check.result!==null;
  const hasPassed=check.passed!==undefined&&check.passed!==null;
  if(hasResult===hasPassed)throw Error('Ambiguous AI editorial arithmetic result');
  const passed=check.result==='pass'||check.passed===true;
  if(passed&&!sameCalculation(check.actual,check.expected))throw Error('False AI editorial arithmetic success');
  if(receipt.outcome==='pass_ai_editorial_only'&&!passed)throw Error('AI editorial pass contains failed arithmetic');
 }
 if(receipt.outcome==='pass_ai_editorial_only'&&receipt.findings.some(f=>f.severity==='block'))throw Error('AI editorial pass contradicts findings');
 reviews.set(item.id,receipt);
}
function reviewSection(item){
 const r=reviews.get(item.id);
 if(!r)return '<section aria-label="Editorial checks"><h2>Editorial checks</h2><p>No editorial-check record is available for the original article revision. No professional review is claimed.</p></section>';
 const outcome={pass_ai_editorial_only:'Bounded editorial checks recorded',changes_required:'Changes required',primary_text_unavailable:'Primary text unavailable',rights_scope_unresolved:'Source-rights scope unresolved'}[r.outcome];
 return `<section aria-label="Editorial checks"><h2>Editorial checks</h2><p>${escape(outcome)} for original version ${escape(item.version)}. Reader-edition changes are limited to labels and notices. No professional accounting or legal approval, source rights or Agent admission is granted.</p></section>`;
}
const page=(title,body)=>`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(title)}</title><link rel="stylesheet" href="/assets/styles.css"><main class="content"><h1>${escape(title)}</h1><section aria-label="Original annotation"><p><strong>Ray Sang Annotation</strong></p><p>Original educational draft · Not professionally reviewed · Existing CC BY 4.0 rights and creator credits preserved; new items use the license stated on each article. This label does not mean Ray Sang personally reviewed it.</p><p><a href="/content-terms.txt">Content rights and automated-access terms</a></p></section>${body}</main></html>`;
await mkdir('dist/library',{recursive:true});
await mkdir('dist/reader-editions',{recursive:true});
const rows=[];
for(const item of manifest.items){
 if(!/^[a-z0-9-]+$/.test(item.id))throw Error('Invalid public item ID');
 const bytes=await content(item.path);
 if(hash(bytes)!==item.sha256)throw Error('Content hash mismatch: '+item.id);
 const reader=readerEditions.get(item.id);
 await writeFile(`dist/reader-editions/${item.id}.md`,reader.body);
 await writeFile(`dist/reader-editions/${item.id}.json`,JSON.stringify(readerPayload(item,reader))+'\n');
 await writeFile(`dist/library/${item.id}.html`,page(item.title,`<p><a href="index.html">All library items</a></p><p>Original credit: ${escape(reader.reader_author)} · Original version ${escape(item.version)} · Reader edition ${escape(reader.reader_edition)} · ${escape(item.license)}</p>${reviewSection(item)}<p><a href="../reader-editions/${item.id}.md" download>Download Markdown</a></p><pre class="source-passage-text">${escape(reader.body)}</pre>`));
 rows.push(`<li><strong>Ray Sang Annotation</strong> · <a href="${item.id}.html">${escape(item.title)}</a> — ${escape(item.summary)}${reviews.has(item.id)?' · Editorial-check record available':''}</li>`);
}
await writeFile('dist/library/index.html',page('Free original accounting library',`<p><a href="../systems/index.html">Explore the free accounting systems directory</a></p><p>${rows.length} original items; ${reviews.size} original-revision editorial-check records. Third-party publications retain their own rights. Links and drafts are not approved authoritative evidence.</p><ul>${rows.join('')}</ul>`));
console.log(`Built ${rows.length} hash-verified offline library pages with ${reviews.size} AI editorial records.`);
