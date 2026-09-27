import test from 'node:test';import assert from 'node:assert/strict';
import {Identity,code,phone} from '../vendor/machine.mjs';
function mock(){
 let time=1000000;const user={uid:'u',email:'e@example.test',emailVerified:true};const auth={currentUser:user};
 const log=[];let meta={};let factors=[];
 const resolver={hints:[{uid:'t',factorId:'totp'},{uid:'p',factorId:'phone'}],session:'session',
   async resolveSignIn(a){log.push(['resolve',a]);meta={sign_in_second_factor:a.kind,second_factor_identifier:a.uid};auth.currentUser=user;}};
 const sdk={initializeApp:x=>x,initializeAuth:()=>auth,inMemoryPersistence:'memory',
   async signOut(){log.push(['logout']);auth.currentUser=null;},async getIdToken(){return 'token';},
   async getIdTokenResult(){return {claims:{firebase:meta}};},async reload(){},
   async signInWithEmailAndPassword(){auth.currentUser=user;},async createUserWithEmailAndPassword(){auth.currentUser=user;},
   async sendEmailVerification(){log.push(['email']);},async sendPasswordResetEmail(){log.push(['reset']);},
   getMultiFactorResolver:()=>resolver,multiFactor:()=>({enrolledFactors:factors,getSession:async()=>'enrollsession',enroll:async a=>{log.push(['enroll',a]);factors.push({uid:'enrolled',factorId:'totp'});}}),
   TotpMultiFactorGenerator:{generateSecret:async()=>({secretKey:'TEST-ONLY',generateQrCodeUrl:()=> 'otpauth://example'}),assertionForEnrollment:(s,v)=>({secret:s.secretKey,code:v}),assertionForSignIn:(uid,v)=>({kind:'totp',uid,code:v})},
   PhoneAuthProvider:class {async verifyPhoneNumber(options){log.push(['sms',options]);return 'sms-id';}static credential(id,v){return {id,code:v};}},
   PhoneMultiFactorGenerator:{assertion:c=>({kind:'phone',uid:'p',credential:c})},
   RecaptchaVerifier:class{clear(){log.push(['captcha-clear']);}},qr:async value=>{log.push(['qr-local',value]);return 'data:image/png;base64,TEST';}};
 const identity=new Identity(sdk,{firebase_project_id:'test',firebase_api_key:'example'},()=>time);
 return {identity,sdk,auth,user,log,resolver,setMeta:x=>meta=x,setFactors:x=>factors=x,advance:x=>time+=x};
}
test('OTP rejects nonnumeric or wrong length',()=>{for(const x of ['','12345','1234567','abcdef'])assert.throws(()=>code(x));assert.equal(code(' 123456 '),'123456');});
test('phone validates international number',()=>{assert.equal(phone('+12025550123'),'+12025550123');for(const p of ['5551234','+01234567','+1<script>'])assert.throws(()=>phone(p));});
test('first factor alone is enrollment',async()=>{assert.equal((await mock().identity.state()).stage,'enroll');});
test('factor identifier required',async()=>{const m=mock();m.setMeta({sign_in_second_factor:'totp'});assert.equal((await m.identity.state()).stage,'enroll');});
test('reserved TOTP claims allow ready',async()=>{const m=mock();m.setMeta({sign_in_second_factor:'totp',second_factor_identifier:'x'});assert.equal((await m.identity.state()).stage,'ready');});
test('unverified email before enrollment',async()=>{const m=mock();m.user.emailVerified=false;assert.equal((await m.identity.state()).stage,'verify_email');await assert.rejects(m.identity.totpStart());});
test('TOTP QR local and enrollment signs out',async()=>{const m=mock();const s=await m.identity.totpStart();assert.equal(s.key,'TEST-ONLY');await m.identity.totpFinish('123456');assert.equal(m.auth.currentUser,null);assert.equal((await m.identity.state()).stage,'signed_out');assert.equal(m.identity.secret,null);});
test('expired setup rejected',async()=>{const m=mock();await m.identity.totpStart();m.advance(300001);await assert.rejects(m.identity.totpFinish('123456'));});
test('SMS requires consent',async()=>{const m=mock();await assert.rejects(m.identity.smsStart('+12025550123',false,{}));assert(!m.log.some(x=>x[0]==='sms'));});
test('SMS enrollment and cooldown',async()=>{const m=mock();await m.identity.smsStart('+12025550123',true,{});await assert.rejects(m.identity.smsStart('+12025550123',true,{}));});
test('SMS enrollment separate from sign-in',async()=>{const m=mock();await m.identity.smsStart('+12025550123',true,{});await m.identity.smsFinish('123456');assert.equal(m.auth.currentUser,null);});
test('TOTP resolver uses chosen factor',async()=>{const m=mock();m.sdk.signInWithEmailAndPassword=async()=>{throw {code:'auth/multi-factor-auth-required'};};assert.equal((await m.identity.signin('e','p')).stage,'challenge');m.identity.choose('t');assert.equal((await m.identity.challenge('123456')).stage,'ready');});
test('SMS requires selected factor and request',async()=>{const m=mock();m.identity.resolver=m.resolver;m.identity.choose('p');await assert.rejects(m.identity.challenge('123456'));await m.identity.smsChallenge({});assert.equal((await m.identity.challenge('123456')).stage,'ready');});
test('unknown factor rejected',()=>{const m=mock();m.identity.resolver=m.resolver;assert.throws(()=>m.identity.choose('unknown'));});
test('cancelled sign-in cannot restore session',async()=>{const m=mock();let resolve;m.sdk.signInWithEmailAndPassword=()=>new Promise(r=>{resolve=()=>{m.auth.currentUser=m.user;r();};});const p=m.identity.signin('e','p');await m.identity.logout();resolve();await p;assert.equal(m.auth.currentUser,null);});
test('cancelled secret generation discarded',async()=>{const m=mock();let resolve;m.sdk.TotpMultiFactorGenerator.generateSecret=()=>new Promise(r=>{resolve=r;});const p=m.identity.totpStart();await Promise.resolve();await m.identity.logout();resolve({secretKey:'cancelled',generateQrCodeUrl:()=>''});await assert.rejects(p);assert.equal(m.identity.secret,null);});
