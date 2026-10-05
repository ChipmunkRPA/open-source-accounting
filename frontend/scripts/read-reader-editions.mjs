import {READER_ARTICLES,READER_EDITION,READER_NOTICE,CANONICAL_MANIFEST_SHA256,READER_RULES_SHA256} from '../dist/reader-registry.js';
import {createHash} from 'node:crypto';

const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const fail = message => {throw Error('Reader edition: '+message);};
const fields = (value, keys) => value && typeof value==='object' && !Array.isArray(value) && Object.keys(value).length===keys.length && keys.every(key=>Object.hasOwn(value,key));
const sha = value => typeof value==='string' && /^[0-9a-f]{64}$/.test(value);

export function applyReaderLabels(text, rules) {
  if(!fields(rules,['schema','scope','reader_notice','replacements']) || rules.schema!==1 || typeof rules.scope!=='string' || typeof rules.reader_notice!=='string' || !rules.reader_notice || !rules.replacements || typeof rules.replacements!=='object' || Array.isArray(rules.replacements)) fail('invalid exact-label rules');
  if(Object.entries(rules.replacements).some(([before,after])=>typeof after!=='string' || before.includes('\n') || after.includes('\n') || before===after)) fail('invalid line substitution');
  if(!/^# [^\n]+\n/.test(text)) fail('missing article heading');
  const changed=text.split('\n').map(line=>Object.hasOwn(rules.replacements,line)?rules.replacements[line]:line).join('\n');
  return changed.replace(/^(# [^\n]+\n)/,match=>match+'\n'+rules.reader_notice+'\n');
}

export async function loadReaderEditions(content, manifest, manifestBytes, parseJson=bytes=>JSON.parse(bytes.toString('utf8'))) {
  const index=parseJson(await content('reader-editions/index.json'));
  const ruleBytes=await content('reader-editions/rules.json');
  const rules=parseJson(ruleBytes);
  if(!fields(index,['schema','reader_edition','annotation_brand','canonical_manifest_sha256','rules_sha256','items']) || index.schema!==1 || index.annotation_brand!=='Ray Sang Annotation' || !/^\d{4}-\d{2}-\d{2}\.\d+$/.test(index.reader_edition) || !sha(index.canonical_manifest_sha256) || !sha(index.rules_sha256) || !Array.isArray(index.items)) fail('invalid index');
  if(index.reader_edition!==READER_EDITION || rules.reader_notice!==READER_NOTICE || index.canonical_manifest_sha256!==CANONICAL_MANIFEST_SHA256 || index.rules_sha256!==READER_RULES_SHA256) fail('unapproved pinned edition or metadata');
  if(index.canonical_manifest_sha256!==hash(manifestBytes) || index.rules_sha256!==hash(ruleBytes)) fail('manifest or rule hash mismatch');
  if(index.items.length!==Object.keys(READER_ARTICLES).length) fail('pinned article count mismatch');
  if(index.items.length!==manifest.items.length) fail('incomplete article coverage');
  const originals=new Map(manifest.items.map(item=>[item.id,item]));
  const readers=new Map();
  for(const row of index.items) {
    if(!fields(row,['item_id','canonical_path','canonical_version','canonical_sha256','reader_path','reader_sha256','reader_author','license'])) fail('invalid item fields');
    const original=originals.get(row.item_id);
    const pinned=READER_ARTICLES[row.item_id];
    if(!pinned || !original || row.canonical_version!==pinned.canonical_version || row.canonical_sha256!==pinned.canonical_sha256 || row.reader_sha256!==pinned.reader_sha256 || row.reader_author!==pinned.creator_credit || row.license!==pinned.license || original.title!==pinned.title) fail('pinned article revision mismatch');
    if(!original || readers.has(row.item_id) || row.canonical_path!==original.path || row.canonical_version!==original.version || row.canonical_sha256!==original.sha256 || row.license!==original.license) fail('canonical item mismatch');
    if(row.reader_path!==`reader-editions/${index.reader_edition.slice(0,10)}/${row.item_id}.md` || !sha(row.reader_sha256) || !sha(row.canonical_sha256)) fail('invalid reader path or hash');
    if(row.reader_author!==original.author.replace(/ \(AI-assisted\)$/,'') || !['Open Accounting contributors','Open Source Accounting contributors'].includes(row.reader_author)) fail('creator identity changed');
    const originalBytes=await content(original.path);
    const readerBytes=await content(row.reader_path);
    if(hash(originalBytes)!==row.canonical_sha256 || hash(readerBytes)!==row.reader_sha256) fail('article hash mismatch');
    const body=readerBytes.toString('utf8');
    if(body!==applyReaderLabels(originalBytes.toString('utf8'),rules)) fail('unapproved reader text change');
    readers.set(row.item_id,{body,reader_edition:index.reader_edition,reader_sha256:row.reader_sha256,reader_author:row.reader_author});
  }
  return readers;
}

export function readerPayload(item, reader) {
  return {schema:1,item_id:item.id,canonical_version:item.version,canonical_sha256:item.sha256,reader_edition:reader.reader_edition,reader_sha256:reader.reader_sha256,title:item.title,creator_credit:reader.reader_author,license:item.license,body:reader.body};
}
