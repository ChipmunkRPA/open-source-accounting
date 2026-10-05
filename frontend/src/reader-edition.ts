import {READER_ARTICLES,READER_EDITION,READER_NOTICE} from './reader-registry.js';
type Article = {id:string;body:string;title:string;license:string;version?:string;sha256?:string};
export type ReaderEdition = {schema:1;item_id:string;canonical_version:string;canonical_sha256:string;reader_edition:string;reader_sha256:string;title:string;creator_credit:string;license:string;body:string};

const readerNotice = READER_NOTICE;
const labelReplacements:ReadonlyArray<readonly [string,string]> = [
  [
    "AI-assisted by Open Source Accounting contributors.",
    "By Open Source Accounting contributors."
  ],
  [
    "AI-assisted editorial draft by Open Source Accounting contributors.",
    "Editorial draft by Open Source Accounting contributors."
  ],
  [
    "AI-assisted educational draft",
    "Educational draft"
  ],
  [
    "AI-assisted editorial draft",
    "Editorial draft"
  ],
  [
    "contributors, AI-assisted.",
    "contributors."
  ],
  [
    "contributors (AI-assisted)",
    "contributors"
  ],
  [
    "An AI receipt",
    "An editorial-check record"
  ],
  [
    "An AI editorial check",
    "An editorial check"
  ],
  [
    "an AI editorial check",
    "an editorial check"
  ],
  [
    "An AI editorial receipt",
    "An editorial-check record"
  ],
  [
    "an AI editorial receipt",
    "an editorial-check record"
  ],
  [
    "AI editorial checking",
    "Editorial checking"
  ],
  [
    "AI editorial arithmetic checks",
    "Editorial arithmetic checks"
  ],
  [
    "AI editorial checks",
    "Editorial checks"
  ],
  [
    "AI editorial check",
    "Editorial check"
  ],
  [
    "AI editorial review",
    "Editorial review"
  ],
  [
    "AI editorial;",
    "Editorial;"
  ],
  [
    "this AI-checked draft",
    "this editorially checked draft"
  ],
  [
    "model-generated suggestions",
    "draft suggestions"
  ],
  [
    "A model-generated checklist",
    "A draft checklist"
  ],
  [
    "A model-generated summary",
    "A draft summary"
  ],
  [
    "an AI check",
    "an editorial check"
  ],
  [
    "an AI critique",
    "an editorial critique"
  ],
  [
    "imply that an AI model is a licensed accountant",
    "present an editorial check as a licensed accountant’s review"
  ],
  [
    "An AI-generated date",
    "A generated date"
  ],
  [
    "an AI-generated checklist",
    "a generated checklist"
  ],
  [
    "The AI result",
    "The draft result"
  ],
  [
    "An AI explanation",
    "An educational explanation"
  ],
  [
    "AI work does not replace",
    "Drafting assistance does not replace"
  ],
  [
    "AI arithmetic is not",
    "Illustrative arithmetic is not"
  ],
  [
    "AI completion",
    "completion of a drafting task"
  ],
  [
    "../../CONTENT-TERMS.md",
    "https://github.com/ChipmunkRPA/open-source-accounting/blob/4ffc83f154a152c453438eafe63e8b6b77f27a93/CONTENT-TERMS.md"
  ]
];

export function expectedReaderText(source:string):string {
  if(!/^# [^\n]+\n/.test(source)) throw Error('The original article heading is invalid.');
  const body=source.split('\n').map(line=>{
    let result=line;
    for(const [before,after] of labelReplacements) result=result.replaceAll(before,after);
    return result.replaceAll('received Editorial','received editorial').replaceAll('completed Editorial','completed editorial').replaceAll('arithmetic and Editorial','arithmetic and editorial').replaceAll('exact-revision Editorial','exact-revision editorial').replaceAll('and the arithmetic received Editorial','and the arithmetic received editorial').replaceAll('by a Editorial','by an editorial').replaceAll('Ray Sang’s Annotation','Ray Sang Annotation');
  }).join('\n');
  return body.replace(/^(# [^\n]+\n)/,match=>match+'\n'+readerNotice+'\n');
}

const sourceReviewLabels:Readonly<Record<string,string>> = {
  "Edition 2.0; physical page 25 / printed 20, PR.AA-05, PR.DS-11, PR.PS-01, PR.PS-04. AI-assisted locator check only; no independent technical/applicability approval. Full original/extraction retained locally outside distributed library.": "Edition 2.0; physical page 25 / printed 20, PR.AA-05, PR.DS-11, PR.PS-01, PR.PS-04. Locator check only; no independent technical/applicability approval. Full original/extraction retained locally outside distributed library.",
  "June 2026 label; physical/printed page 5. AI-assisted locator check only; no independent technical, rights or applicability approval. Full original/extraction retained separately from distributed library.": "June 2026 label; physical/printed page 5. Locator check only; no independent technical, rights or applicability approval. Full original/extraction retained separately from distributed library.",
  "June 2026 label; physical/printed page 7. AI-assisted locator check only; no independent technical, rights or applicability approval. Full original/extraction retained separately from distributed library.": "June 2026 label; physical/printed page 7. Locator check only; no independent technical, rights or applicability approval. Full original/extraction retained separately from distributed library.",
  "Physical 2 copyright notice; physical 7 / printed 5 paragraphs 18–24, start of 25 and footnotes 2–3; physical 15 / printed 13 paragraphs 70–74 and materiality caveat. AI-assisted selected checks only; no professional, rights or applicability approval. Underlying SFFAS 64 text is not verified by this record.": "Physical 2 copyright notice; physical 7 / printed 5 paragraphs 18–24, start of 25 and footnotes 2–3; physical 15 / printed 13 paragraphs 70–74 and materiality caveat. Selected checks only; no professional, rights or applicability approval. Underlying SFFAS 64 text is not verified by this record."
};

export function readerSourceScope(value:unknown):string {
  if(typeof value!=='string') return 'Source review scope is not recorded.';
  return Object.hasOwn(sourceReviewLabels,value)?sourceReviewLabels[value]:value;
}

async function sha256(text:string):Promise<string> {
  if(!globalThis.crypto?.subtle) throw Error('This browser cannot verify the article reader edition.');
  const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
  return Array.from(new Uint8Array(bytes),value=>value.toString(16).padStart(2,'0')).join('');
}

// The original API body is checked but never rendered or offered as the active download.
// No fallback to an unverified or stale article is allowed.
export async function loadReaderEdition(item:Article, fetcher:typeof fetch=fetch):Promise<ReaderEdition> {
  if(typeof item.id!=='string' || !/^[a-z0-9-]+$/.test(item.id) || typeof item.body!=='string' || typeof item.title!=='string' || typeof item.license!=='string') throw Error('Invalid article for reader-edition verification.');
  const pinned=READER_ARTICLES[item.id];
  if(!pinned) throw Error('No pinned reader edition exists for this article.');
  const response=await fetcher('/assets/reader-editions/'+encodeURIComponent(item.id)+'.json',{credentials:'same-origin',cache:'no-store'});
  if(!response.ok) throw Error('A verified reader edition is not available for this article.');
  const reader=await response.json() as ReaderEdition;
  const keys=['schema','item_id','canonical_version','canonical_sha256','reader_edition','reader_sha256','title','creator_credit','license','body'];
  if(!reader || typeof reader!=='object' || Array.isArray(reader) || Object.keys(reader).length!==keys.length || keys.some(key=>!Object.hasOwn(reader,key)) || reader.schema!==1 || keys.filter(key=>key!=='schema').some(key=>typeof (reader as unknown as Record<string,unknown>)[key]!=='string')) throw Error('Invalid reader-edition response.');
  if(reader.item_id!==item.id || reader.title!==item.title || reader.license!==item.license || item.version!==undefined && reader.canonical_version!==item.version || item.sha256!==undefined && reader.canonical_sha256!==item.sha256 || !/^[0-9a-f]{64}$/.test(reader.canonical_sha256) || !/^[0-9a-f]{64}$/.test(reader.reader_sha256) || !/^\d{4}-\d{2}-\d{2}\.\d+$/.test(reader.reader_edition) || !['Open Accounting contributors','Open Source Accounting contributors'].includes(reader.creator_credit)) throw Error('The reader edition does not match this article revision.');
  if(reader.reader_edition!==READER_EDITION || reader.canonical_version!==pinned.canonical_version || reader.canonical_sha256!==pinned.canonical_sha256 || reader.reader_sha256!==pinned.reader_sha256 || reader.title!==pinned.title || reader.creator_credit!==pinned.creator_credit || reader.license!==pinned.license) throw Error('The reader edition does not match the pinned article revision.');
  if(reader.canonical_sha256!==await sha256(item.body) || reader.reader_sha256!==await sha256(reader.body)) throw Error('Article integrity verification failed.');
  if(reader.body!==expectedReaderText(item.body)) throw Error('The reader edition contains unapproved article changes.');
  return reader;
}
