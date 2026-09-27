import {el,textBlock} from './ui.js';
import type {Json} from './types.js';

// Text-only rendering: publisher notices are data, never executable markup.
export function sourceNotices(rows:Json[]=[]){
  const section=el('section',{class:'source-notices','aria-label':'Required source notices'});
  if(rows.length) section.append(el('h3',{},'Source notices'));
  for(const row of rows) section.append(el('article',{},
    el('p',{class:'muted'},`${row.title} · ${row.publisher} · ${row.version}`),
    textBlock(row.notice),el('p',{class:'muted'},row.url)));
  return section;
}
