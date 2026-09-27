/** Browser-only Identity Platform MFA controller. No analytics or third-party QR service. */
import {initializeApp} from 'firebase/app';
import {initializeAuth,inMemoryPersistence,signInWithEmailAndPassword,createUserWithEmailAndPassword,
  sendEmailVerification,sendPasswordResetEmail,signOut,getIdToken,getIdTokenResult,reload,
  multiFactor,getMultiFactorResolver,TotpMultiFactorGenerator,PhoneAuthProvider,
  PhoneMultiFactorGenerator,RecaptchaVerifier} from 'firebase/auth';
import QRCode from 'qrcode';
import {Identity} from './machine.mjs';
const sdk={initializeApp,initializeAuth,inMemoryPersistence,signInWithEmailAndPassword,
  createUserWithEmailAndPassword,sendEmailVerification,sendPasswordResetEmail,signOut,
  getIdToken,getIdTokenResult,reload,multiFactor,getMultiFactorResolver,
  TotpMultiFactorGenerator,PhoneAuthProvider,PhoneMultiFactorGenerator,RecaptchaVerifier,
  qr:(value)=>QRCode.toDataURL(value,{width:240,margin:2,errorCorrectionLevel:'M'})};
export const createIdentity=(config)=>new Identity(sdk,config);
