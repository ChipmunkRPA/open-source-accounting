/** Isolated MFA logic with an injectable SDK for unit tests. Never persist secrets or tokens. */
export function code(value){if(!/^\d{6}$/.test(value.trim()))throw new Error('Enter the six-digit verification code.');return value.trim();}
export function phone(value){if(!/^\+[1-9]\d{7,14}$/.test(value.trim()))throw new Error('Use an international phone number beginning with + and the country code.');return value.trim();}
export class Identity {
  constructor(sdk,cfg,clock=()=>Date.now()){
    this.sdk=sdk;this.clock=clock;this.epoch=0;this.cooldown=0;
    this.auth=sdk.initializeAuth(sdk.initializeApp({apiKey:cfg.firebase_api_key,projectId:cfg.firebase_project_id,
      authDomain:cfg.firebase_auth_domain||`${cfg.firebase_project_id}.firebaseapp.com`}),{persistence:sdk.inMemoryPersistence});
    if(cfg.firebase_tenant_id)this.auth.tenantId=cfg.firebase_tenant_id;
  }
  clear(){this.secret=null;this.resolver=null;this.selected=null;this.smsId='';this.smsPurpose='';this.verifier?.clear();this.verifier=null;}
  async logout(){++this.epoch;this.clear();await this.sdk.signOut(this.auth);}
  async token(){return this.auth.currentUser?this.sdk.getIdToken(this.auth.currentUser):'';}
  user(){if(!this.auth.currentUser?.emailVerified)throw new Error('Verify your email address before setting up a second factor.');return this.auth.currentUser;}
  async state(){
    if(this.resolver)return {stage:'challenge',factors:this.resolver.hints.filter(x=>['totp','phone'].includes(x.factorId))};
    const u=this.auth.currentUser;if(!u)return {stage:'signed_out'};
    if(!u.emailVerified)return {stage:'verify_email'};
    const result=await this.sdk.getIdTokenResult(u,true);const f=result.claims.firebase;
    if(['totp','phone'].includes(f?.sign_in_second_factor)&&typeof f?.second_factor_identifier==='string'&&f.second_factor_identifier)return {stage:'ready'};
    return {stage:this.sdk.multiFactor(u).enrolledFactors.length?'sign_in_again':'enroll'};
  }
  async signin(email,password,signup=false){
    const epoch=++this.epoch;this.clear();
    try{
      if(signup){await this.sdk.createUserWithEmailAndPassword(this.auth,email.trim(),password);await this.sdk.sendEmailVerification(this.auth.currentUser);}
      else await this.sdk.signInWithEmailAndPassword(this.auth,email.trim(),password);
    }catch(error){
      if(epoch!==this.epoch){await this.sdk.signOut(this.auth);return {stage:'signed_out'};}
      if(error.code!=='auth/multi-factor-auth-required')throw error;
      this.resolver=this.sdk.getMultiFactorResolver(this.auth,error);
    }
    if(epoch!==this.epoch){await this.sdk.signOut(this.auth);return {stage:'signed_out'};}
    return this.state();
  }
  async sendVerification(){if(this.auth.currentUser)await this.sdk.sendEmailVerification(this.auth.currentUser);}
  async checkEmail(){if(this.auth.currentUser)await this.sdk.reload(this.auth.currentUser);return this.state();}
  async resetPassword(email){await this.sdk.sendPasswordResetEmail(this.auth,email.trim());}
  clearEnrollment(){++this.epoch;this.secret=null;this.smsId='';this.smsPurpose='';this.verifier?.clear();this.verifier=null;}
  async totpStart(){
    this.clearEnrollment();const epoch=this.epoch;
    const u=this.user(), session=await this.sdk.multiFactor(u).getSession();
    const secret=await this.sdk.TotpMultiFactorGenerator.generateSecret(session);
    if(epoch!==this.epoch)throw new Error('Setup was cancelled.');
    this.secret=secret;this.expires=this.clock()+300000;
    const qr=await this.sdk.qr(secret.generateQrCodeUrl(u.email,'Open Source Accounting'));
    if(epoch!==this.epoch)throw new Error('Setup was cancelled.');
    return {key:secret.secretKey,qr};
  }
  async totpFinish(value){
    value=code(value);if(!this.secret||this.clock()>this.expires){this.secret=null;throw new Error('This setup expired. Generate a new key.');}
    const epoch=this.epoch;
    await this.sdk.multiFactor(this.user()).enroll(this.sdk.TotpMultiFactorGenerator.assertionForEnrollment(this.secret,value),'Authenticator app');
    // Never treat enrollment as proof of a second-factor sign-in.
    if(epoch===this.epoch)await this.logout();
  }
  async smsSend(options,container,purpose){
    if(this.clock()<this.cooldown)throw new Error('Wait at least 60 seconds before requesting another text.');
    this.cooldown=this.clock()+60000;this.verifier?.clear();this.smsId='';this.smsPurpose='';
    const epoch=this.epoch;
    this.verifier=new this.sdk.RecaptchaVerifier(this.auth,container,{size:'normal'});
    try{
      const id=await new this.sdk.PhoneAuthProvider(this.auth).verifyPhoneNumber(options,this.verifier);
      if(epoch!==this.epoch)throw new Error('Verification was cancelled.');
      this.smsId=id;this.smsPurpose=purpose;
    }catch(error){this.verifier?.clear();this.verifier=null;throw error;}
  }
  async smsStart(value,consent,container){
    if(!consent)throw new Error('Consent to using your number for Google verification before requesting a text.');
    const number=phone(value);this.clearEnrollment();
    const session=await this.sdk.multiFactor(this.user()).getSession();
    await this.smsSend({phoneNumber:number,session},container,'enroll');
  }
  async smsFinish(value){
    value=code(value);if(!this.smsId||this.smsPurpose!=='enroll')throw new Error('Request a verification text first.');
    const credential=this.sdk.PhoneAuthProvider.credential(this.smsId,value);
    await this.sdk.multiFactor(this.user()).enroll(this.sdk.PhoneMultiFactorGenerator.assertion(credential),'Text message');
    await this.logout();
  }
  choose(uid){
    this.selected=this.resolver?.hints.find(x=>x.uid===uid&&['totp','phone'].includes(x.factorId));
    if(!this.selected)throw new Error('Choose an enrolled verification method.');
    this.smsId='';this.smsPurpose='';this.verifier?.clear();this.verifier=null;
    return this.selected;
  }
  async smsChallenge(container){
    if(this.selected?.factorId!=='phone')throw new Error('Choose an enrolled SMS method first.');
    await this.smsSend({multiFactorHint:this.selected,session:this.resolver.session},container,'challenge:'+this.selected.uid);
  }
  async challenge(value){
    value=code(value);const f=this.selected;if(!f)throw new Error('Choose an enrolled verification method.');
    let assertion;
    if(f.factorId==='totp')assertion=this.sdk.TotpMultiFactorGenerator.assertionForSignIn(f.uid,value);
    else{
      if(!this.smsId||this.smsPurpose!=='challenge:'+f.uid)throw new Error('Request a text for this factor first.');
      assertion=this.sdk.PhoneMultiFactorGenerator.assertion(this.sdk.PhoneAuthProvider.credential(this.smsId,value));
    }
    const epoch=this.epoch;await this.resolver.resolveSignIn(assertion);
    if(epoch!==this.epoch){await this.sdk.signOut(this.auth);return {stage:'signed_out'};}
    this.clear();return this.state();
  }
}
