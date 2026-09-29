import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve,relative} from 'node:path';
const root=resolve('../content');
const manifest=JSON.parse(await readFile(root+'/manifest.json','utf8'));
const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const page=(title,body)=>`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(title)}</title><link rel="stylesheet" href="/assets/styles.css"><main class="content"><h1>${escape(title)}</h1><p>Original educational draft · Not professionally reviewed · CC BY 4.0</p>${body}</main></html>`;
await mkdir('dist/library',{recursive:true});
let rows=[];
for(const item of manifest.items){
 if(!/^[a-z0-9-]+$/.test(item.id))throw Error('Invalid public item ID');
 const file=resolve(root,item.path);if(relative(root,file).startsWith('..'))throw Error('Invalid public content path');
 const bytes=await readFile(file);
 if(createHash('sha256').update(bytes).digest('hex')!==item.sha256)throw Error('Content hash mismatch: '+item.id);
 await writeFile(`dist/library/${item.id}.html`,page(item.title,`<p><a href="index.html">All library items</a></p><pre class="source-passage-text">${escape(bytes.toString('utf8'))}</pre>`));
 rows.push(`<li><a href="${item.id}.html">${escape(item.title)}</a> — ${escape(item.summary)}</li>`);
}
await writeFile('dist/library/index.html',page('Free original accounting library',`<p>${rows.length} original items. Third-party publications retain their own rights. Links and drafts are not approved authoritative evidence.</p><ul>${rows.join('')}</ul>`));
console.log(`Built ${rows.length} hash-verified offline library pages.`);
