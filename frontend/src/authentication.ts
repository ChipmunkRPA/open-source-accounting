import {getIdentity,api} from './api.js';
import {el,modal,field,input,button,notice,checkbox,busy} from './ui.js';
export interface Factor{uid:string;factorId:string;displayName?:string;phoneNumber?:string}
export interface State{stage:'signed_out'|'verify_email'|'enroll'|'sign_in_again'|'challenge'|'ready';factors?:Factor[]}
export interface IdentityClient{
  logout:()=>Promise<void>;token:()=>Promise<string>;state:()=>Promise<State>;
  signin:(email:string,password:string,signup?:boolean)=>Promise<State>;
  sendVerification:()=>Promise<void>;checkEmail:()=>Promise<State>;resetPassword:(email:string)=>Promise<void>;
  clearEnrollment:()=>void;totpStart:()=>Promise<{key:string;qr:string}>;totpFinish:(code:string)=>Promise<void>;
  smsStart:(phone:string,consent:boolean,container:HTMLElement)=>Promise<void>;smsFinish:(code:string)=>Promise<void>;
  choose:(uid:string)=>Factor;smsChallenge:(container:HTMLElement)=>Promise<void>;challenge:(code:string)=>Promise<State>;
}
export function authMessage(error:unknown):string{
  const c=(error as {code?:string})?.code;
  if(!c)return error instanceof Error?error.message:'Authentication failed.';
  const messages:Record<string,string>={
    'auth/invalid-credential':'Sign-in details could not be verified.',
    'auth/user-not-found':'Sign-in details could not be verified.',
    'auth/wrong-password':'Sign-in details could not be verified.',
    'auth/email-already-in-use':'Unable to create this account. Try signing in or resetting your password.',
    'auth/weak-password':'Choose a stronger password meeting the project password policy.',
    'auth/invalid-email':'Enter a valid email address.',
    'auth/invalid-verification-code':'The code was not accepted. Check the current code and try again.',
    'auth/code-expired':'The code expired. Request a new one.',
    'auth/invalid-totp-code':'The code was not accepted. Check your device clock and try again.',
    'auth/requires-recent-login':'Sign in again before changing verification methods.',
    'auth/too-many-requests':'Too many attempts. Wait before retrying or choose another enrolled factor.',
    'auth/quota-exceeded':'SMS is temporarily unavailable. Use another enrolled factor or contact support.',
    'auth/captcha-check-failed':'Complete the security check again.',
    'auth/operation-not-allowed':'The operator has not enabled this authentication method.',
    'auth/network-request-failed':'The authentication service is unreachable. Check your connection.',
    'auth/user-token-expired':'Your session expired. Sign in again.',
  };
  return messages[c]||'Authentication could not be completed. Try again or contact support.';
}
export async function showAuthentication(onReady:()=>Promise<void>,addBackup=false){
  if(document.querySelector('[data-auth-dialog]'))return;
  const body=el('div',{class:'auth-body'}),message=el('div',{'aria-live':'polite'});
  const dialog=modal('Secure sign-in',notice('Free chat stays free. Every signed-in account requires an authenticator or SMS.'),body,message);
  dialog.setAttribute('data-auth-dialog','true');let identity:IdentityClient|undefined,done=false,pending=false;
  let enrollmentTimer:ReturnType<typeof setTimeout>|undefined;
  const clearTimer=()=>{if(enrollmentTimer)clearTimeout(enrollmentTimer);enrollmentTimer=undefined;};
  dialog.addEventListener('close',()=>{clearTimer();body.replaceChildren();if(!done)void identity?.logout();});
  const action=(label:string,fn:()=>Promise<unknown>,variant='primary')=>{
    const b=button(label,async()=>{
      if(pending)return;pending=true;busy(b,true);message.replaceChildren();
      try{await fn();}catch(e){if(dialog.open)message.replaceChildren(notice(authMessage(e),'error'));}
      finally{pending=false;busy(b,false);}
    },variant);return b;
  };
  function otp(){const n=input('text');n.inputMode='numeric';n.autocomplete='one-time-code';n.maxLength=6;n.pattern='[0-9]{6}';return n;}
  function login(info=''){
    clearTimer();const email=input('email'),password=input('password');email.autocomplete='username';password.autocomplete='current-password';password.minLength=8;
    const signup=checkbox('Create an account');
    const submit=action('Continue',async()=>{if(!form.reportValidity())return;const value=password.value;password.value='';await render(await identity!.signin(email.value,value,signup.input.checked));});
    const form=el('form',{},field('Email',email),field('Password',password),signup.element,submit);
    form.onsubmit=e=>{e.preventDefault();submit.click();};submit.type='submit';
    // Button helper handles click, form handles keyboard submission without bypassing validation.
    submit.onclick=e=>e.preventDefault();email.required=true;password.required=true;
    body.replaceChildren(el('h3',{},'Step 1 · Your account'),info?notice(info):el('span'),form,
      action('Reset password',async()=>{await identity!.resetPassword(email.value);message.replaceChildren(notice('A reset email will be sent when the account is eligible. Password reset does not remove MFA.'));},'quiet'));
  }
  function enroll(){
    clearTimer();identity!.clearEnrollment();body.replaceChildren(el('h3',{},'Step 2 · Choose verification'),
      el('p',{},'Use Google Authenticator or another TOTP app, or receive a text message. Add a backup method after signing in.'),
      action('Authenticator app',async()=>{
        const secret=await identity!.totpStart();if(!dialog.open)return;
        const n=otp();body.replaceChildren(el('h3',{},'Set up Google Authenticator'),
          el('p',{},'Scan the code or enter the setup key. Keep the key private.'),
          el('img',{src:secret.qr,alt:'Authenticator enrollment QR code',width:240,height:240,class:'auth-qr'}),
          el('code',{class:'auth-secret'},secret.key),field('Current six-digit code',n),
          action('Verify and enroll',async()=>{const value=n.value;n.value='';await identity!.totpFinish(value);clearTimer();addBackup=false;login('Authenticator enrolled. Sign in again and use its current code.');}),
          action('Choose another method',async()=>enroll(),'quiet'));
        enrollmentTimer=setTimeout(()=>{if(dialog.open){identity!.clearEnrollment();enroll();message.replaceChildren(notice('Setup expired. Generate a new key.'));}},300000);
      }),
      action('Text message',async()=>{
        identity!.clearEnrollment();const number=input('tel'),n=otp(),captcha=el('div',{class:'auth-captcha'});
        number.autocomplete='tel';const consent=checkbox('I agree to sending my phone number to Google to verify my identity and prevent abuse. Message/data rates may apply.');
        body.replaceChildren(el('h3',{},'Set up text verification'),field('Phone number',number,'Include + and country code.'),consent.element,captcha,
          action('Send verification text',async()=>{await identity!.smsStart(number.value,consent.input.checked,captcha);message.replaceChildren(notice('Text requested. Enter the code below.'));}),
          field('Six-digit SMS code',n),action('Verify and enroll',async()=>{const value=n.value;n.value='';await identity!.smsFinish(value);addBackup=false;login('Phone enrolled. Sign in again to verify the second factor.');}),
          action('Choose another method',async()=>enroll(),'quiet'));
      },'secondary'));
  }
  function challenge(state:State){
    clearTimer();const choices=el('div',{class:'auth-options'}),challengeBody=el('div');
    body.replaceChildren(el('h3',{},'Step 2 · Verify your sign-in'),choices,challengeBody,
      notice('Lost access? Choose another enrolled factor. Support must verify ownership before recovery; email alone does not bypass MFA.'),
      action('Use a different account',async()=>{await identity!.logout();login();},'quiet'));
    for(const f of state.factors||[]){
      choices.append(action(f.factorId==='totp'?(f.displayName||'Authenticator app'):`SMS ${f.phoneNumber||f.displayName||''}`,async()=>{
        identity!.choose(f.uid);const n=otp(),captcha=el('div',{class:'auth-captcha'});
        challengeBody.replaceChildren(el('p',{},f.factorId==='totp'?'Enter the current code from your authenticator.':'Request a code for your enrolled phone.'),
          ...(f.factorId==='phone'?[captcha,action('Send text',async()=>{await identity!.smsChallenge(captcha);message.replaceChildren(notice('Text requested.'));})]:[]),
          field('Six-digit code',n),action('Verify sign-in',async()=>{const value=n.value;n.value='';await render(await identity!.challenge(value));}));
      },'secondary'));
    }
    if(!(state.factors||[]).length)challengeBody.replaceChildren(notice('No supported second factor is available. Contact support.','error'));
  }
  async function render(state:State){
    if(!dialog.open)return;
    if(state.stage==='ready'){
      const result=await api<{next_step:string}>('/auth/status');
      if(result.next_step!=='ready')throw new Error('The server requires second-factor verification. Sign in again.');
      if(addBackup){enroll();return;}
      await onReady();done=true;dialog.close();return;
    }
    if(state.stage==='verify_email'){
      body.replaceChildren(el('h3',{},'Verify your email'),el('p',{},'Use the verification link before enrolling a second factor.'),
        action('I verified my email',async()=>render(await identity!.checkEmail())),
        action('Resend verification email',async()=>{await identity!.sendVerification();message.replaceChildren(notice('Verification email requested.'));},'secondary'),
        action('Return to sign-in',async()=>{await identity!.logout();login();},'quiet'));return;
    }
    if(state.stage==='enroll'){enroll();return;}
    if(state.stage==='challenge'){challenge(state);return;}
    if(state.stage==='sign_in_again'){await identity!.logout();login('Sign in again to verify your enrolled second factor.');return;}
    login();
  }
  try{identity=await getIdentity();if(!dialog.open){await identity.logout();return;}await identity.logout();login();}
  catch(e){body.replaceChildren(notice(authMessage(e),'error'));}
}
