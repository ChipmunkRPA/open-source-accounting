import {api,requestKey} from '../api.js';
import {el,button,link,heading,badge,textarea,field,busy,notice,textBlock,empty} from '../ui.js';
import type {App,Json} from '../types.js';

export async function chatView(app:App,chatId?:string){
  const list=await api('/chats');let conversation:Json=chatId?await api('/chats/'+chatId):{messages:[]};
  const messages=el('div',{class:'messages','aria-live':'polite'});
  function draw(){messages.replaceChildren(...conversation.messages.map((m:Json)=>el('article',{class:'message '+m.role},
      badge(m.role==='user'?'You':'AI · general chat'),textBlock(m.body))));}
  draw();
  const input=textarea('','chat-message',4);input.placeholder='Ask an accounting question—or start a general conversation.';input.maxLength=8000;
  const send=button('Send message',async()=>{
    const value=input.value.trim();if(!value)return;
    busy(send,true,'Responding…');input.disabled=true;
    try{
      if(!chatId){const row=await api('/chats','POST',{title:'New chat'});chatId=row.id;window.history.replaceState({},'',`/chat/${chatId}`);}
      const answer=await api(`/chats/${chatId}/messages`,'POST',{message:value},requestKey());
      conversation.messages.push({role:'user',body:value},{role:'assistant',body:answer.body});
      input.value='';draw();messages.lastElementChild?.scrollIntoView({block:'nearest',behavior:'smooth'});
    }catch(e){app.showError(e);}finally{busy(send,false);input.disabled=false;input.focus();}
  });
  input.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();send.click();}});
  const examples=el('div',{class:'example-row'},...['Explain the difference between a fact and an assumption in accounting research.',
      'What information should I collect before evaluating a contract?', 'How should I organize an accounting research memo?'].map(text=>button(text,()=>{input.value=text;input.focus();},'example')));
  const chatHistory=el('div',{class:'recent-chats'},...list.items.slice(0,6).map((c:Json)=>link(app,c.title,`/chat/${c.id}`,'recent-link')));
  app.content.replaceChildren(heading('Ask freely.','General AI chat is free. Premium research is provided separately by the private hosted application.',
      link(app,'New chat','/chat','button secondary')),
      !chatId?el('section',{class:'hero-chat'},badge('CHAT · FREE','free'),el('h2',{},'A place to work through the question.'),examples):el('span'),
      messages,el('section',{class:'composer'},field('Your message',input),
      el('div',{class:'composer-actions'},el('span',{class:'muted'},'No document or live-source access in general chat.'),
        send)),chatHistory);
}
