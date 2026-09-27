/** Small safe reader for project Markdown, NOT a general HTML renderer.
 * Raw HTML and image markup are displayed as text, never executed or requested.
 */
import {el,table} from './ui.js';
export function inline(text:string):DocumentFragment{
  const fragment=document.createDocumentFragment();
  const pattern=/\[([^\]]+)\]\(([^\s)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`/g;
  let position=0;let match:RegExpExecArray|null;
  while((match=pattern.exec(text))){
    fragment.append(document.createTextNode(text.slice(position,match.index)));
    if(match[1]){
      try{const url=new URL(match[2]);if(url.protocol!=='https:'||url.username||url.password)throw new Error();
        fragment.append(el('a',{href:url.href,target:'_blank',rel:'noopener noreferrer'},match[1]));
      }catch{fragment.append(document.createTextNode(match[1]+' ('+match[2]+')'));}
    }else if(match[3])fragment.append(el('strong',{},match[3]));
    else fragment.append(el('code',{},match[4]));
    position=pattern.lastIndex;
  }
  fragment.append(document.createTextNode(text.slice(position)));return fragment;
}
export function markdown(text:string):{element:HTMLElement;headings:{id:string;text:string}[]}{
  const root=el('article',{class:'prose library-prose'});const lines=text.split('\n');const headings:{id:string;text:string}[]=[];
  const cell=(s:string)=>s.trim().replace(/^\||\|$/g,'').split('|').map(x=>{const n=el('span');n.append(inline(x.trim()));return n;});
  for(let i=0;i<lines.length;){
    const line=lines[i];if(!line.trim()){i++;continue;}
    if(line.startsWith('```')){const body=[];i++;while(i<lines.length&&!lines[i].startsWith('```'))body.push(lines[i++]);i++;
      root.append(el('pre',{},el('code',{},body.join('\n'))));continue;}
    const heading=line.match(/^(#{1,4}) (.+)$/);
    if(heading){const id='section-'+headings.length;headings.push({id,text:heading[2]});
      const level=Math.min(heading[1].length+1,4) as 2|3|4;const node=el(`h${level}`,{id});node.append(inline(heading[2]));root.append(node);i++;continue;}
    if(line.startsWith('|')&&/^\|?[\s:|-]+\|[\s:|-]*$/.test(lines[i+1]||'')){
      const columns=cell(line).map(x=>x.textContent||'');const rows:HTMLElement[][]=[];i+=2;
      while(i<lines.length&&lines[i].startsWith('|'))rows.push(cell(lines[i++]));root.append(table(columns,rows));continue;}
    if(/^[-*] /.test(line)){const list=el('ul');while(i<lines.length&&/^[-*] /.test(lines[i])){const li=el('li');li.append(inline(lines[i++].slice(2)));list.append(li);}root.append(list);continue;}
    if(line==='---'){root.append(el('hr'));i++;continue;}
    if(line.startsWith('> ')){const block=el('blockquote');block.append(inline(line.slice(2)));root.append(block);i++;continue;}
    const paragraph=[line];i++;
    while(i<lines.length&&lines[i].trim()&&!/^(#|\||>|```|[-*] )/.test(lines[i]))paragraph.push(lines[i++]);
    const p=el('p');p.append(inline(paragraph.join('\n')));root.append(p);
  }
  return {element:root,headings};
}
