import {api,requestKey} from '../api.js';
import {el,button,link,heading,badge,notice,card,checkbox,select,busy,dateText,table} from '../ui.js';
import type {App,Json} from '../types.js';

function trustedStripe(url:string){
  const parsed=new URL(url);if(parsed.protocol!=='https:'||!['checkout.stripe.com','billing.stripe.com'].includes(parsed.hostname))throw new Error('Unexpected payment redirect.');
  location.assign(url);
}

export async function pricingView(app:App){
  const consent=checkbox('I agree to USD $89.99 billed annually, renewing annually until I cancel. I have reviewed the published purchase terms and usage policy.');
  const message=el('div');
  const pay=button('Subscribe — $89.99 / year',async()=>{
    if(!app.me){app.showError(new Error('Sign in before subscribing.'));return;}
    if(!consent.input.checked){message.replaceChildren(notice('Review and accept the annual purchase terms first.','error'));return;}
    busy(pay,true,'Opening secure checkout…');
    try{const data=await api('/billing/checkout','POST',{accepted_annual_terms:true},requestKey());trustedStripe(data.url);}catch(e){app.showError(e);}finally{busy(pay,false);}
  });
  pay.disabled=!app.config.billing_enabled||!app.config.billing_terms_approved||!!app.me?.access.agent_allowed;
  const free=card('Chat',badge('FREE','free'),el('div',{class:'price'},'$0'),el('p',{class:'muted'},'For working through the question.'),
    el('ul',{class:'feature-list'},...['General AI conversations','Accounting concept explanations','Ordinary follow-up questions','Public original learning content','Manual editing and downloading saved deliverables'].map(x=>el('li',{},x))),
    link(app,'Continue free chat','/chat','button secondary'));
  const paid=card('Agent',badge('ANNUAL PLAN','paid'),el('div',{class:'price'},'$89.99',el('span',{},' / year')),
    el('p',{class:'muted'},'For delegating the research and documentation.'),
    el('ul',{class:'feature-list'},...['Deep research across approved sources','Technical accounting memo drafts','Your documents + GAAP reference analysis','Contract and amendment comparison','Challenge and review a draft memo'].map(x=>el('li',{},x))),
    el('p',{class:'muted'},'Experimental additions are labeled separately and are not promised as currently available paid benefits.'),consent.element,message,pay);
  paid.classList.add('featured');
  app.content.replaceChildren(heading('Ask freely. Delegate the work.','One free experience. One annual Agent subscription. No monthly plan or automatic per-task charges.'),
    el('div',{class:'pricing-grid'},free,paid),
    notice(app.config.billing_terms_approved?
      `Published allowance: ${app.config.agent_tasks_per_month} tasks per subscription month. General chat does not consume Agent tasks.`:
      `Proposed launch allowance: ${app.config.agent_tasks_per_month} tasks per subscription month. Live checkout remains disabled until usage and purchase terms are approved.`,'warning'),
    card('What happens when the subscription ends?',el('p',{},'General chat remains free. Existing work can still be read, manually edited, and downloaded, subject to source permissions and the retention policy. New Agent generation requires an active subscription.')),
    card('What does a subscription not include?',el('p',{},'It does not grant a license to proprietary standards, guarantee an accounting conclusion, or provide an audit opinion. Research source coverage is disclosed in each task.')));
  if(app.config.demo_billing_enabled && app.me){
    const demo=button('Activate local Agent demo — no charge',async()=>{await api('/dev/subscription','POST',{state:'active'});await app.refreshAccount();
      const back=sessionStorage.getItem('oa_return_draft');sessionStorage.removeItem('oa_return_draft');
      app.navigate(back?.startsWith('/runs/')?back:'/agents');},'secondary');
    app.content.append(card('Local testing only',notice('This changes the development account state. It is not checkout and no payment is collected.'),demo));
  }
}

export async function billingView(app:App){
  await app.refreshAccount();const me=app.me!;const usage=me.usage;
  const actions=el('div',{class:'row-actions'});
  if(me.access.agent_allowed){
    const cancelling=!!me.subscription?.cancel_at_period_end;
    actions.append(button(cancelling?'Resume annual renewal':'Cancel annual renewal',async()=>{
      try{await api(cancelling?'/billing/resume-renewal':'/billing/cancel-renewal','POST');await billingView(app);}catch(e){app.showError(e);}
    },'secondary'));
  }else actions.append(link(app,'View Agent plan','/pricing','button primary'));
  if(app.config.billing_enabled)actions.append(button('Manage payment method',async()=>{try{trustedStripe((await api('/billing/portal','POST')).url);}catch(e){app.showError(e);}},'secondary'),
    button('Refresh payment status',async()=>{try{await api('/billing/sync','POST');await billingView(app);}catch(e){app.showError(e);}},'quiet'));
  app.content.replaceChildren(heading('Billing & usage','USD $89.99 billed annually. Free chat remains available independently.'),
    el('div',{class:'grid two'},card('Your plan',badge(me.access.state,me.access.agent_allowed?'paid':'neutral'),
      el('h2',{},me.access.agent_allowed?'Agent · $89.99 / year':'Free'),
      el('p',{},`Paid access through: ${dateText(me.access.access_until)}`),
      me.subscription?.cancel_at_period_end?notice('Renewal is off. Agent access continues through your paid term.','warning'):el('p',{class:'muted'},'No automatic per-task charges.'),actions),
      card('Agent task allowance',el('div',{class:'price'},`${usage.consumed} / ${usage.limit}`),el('p',{},`${usage.reserved} task(s) currently reserved.`),
        el('p',{class:'muted'},`Next allowance window: ${dateText(usage.reset_at)}`),
        notice(usage.proposed_policy?'This is a proposed development allowance, not an approved published production limit.':'Completed deliverables consume an allowance. Unsuccessful tasks release their reservation.'))));
  if(app.config.demo_billing_enabled){
    const states=select([['free','Free'],['active','Active'],['ending','Renewal off'],['past_due','Payment issue'],['expired','Expired']],me.access.state.toLowerCase(),'demo-billing-state');
    states.onchange=async()=>{try{await api('/dev/subscription','POST',{state:states.value});await billingView(app);}catch(e){app.showError(e);}};
    app.content.append(card('Development controls',notice('These controls exist only in local mock mode. They never collect payment.'),states));
  }
}
