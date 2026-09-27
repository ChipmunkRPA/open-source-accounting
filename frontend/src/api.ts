import type {Config, Json} from './types.js';
import type {IdentityClient} from './authentication.js';
let config: Config;
let identity: IdentityClient|undefined;
export const requestKey=():string=>crypto.randomUUID();
export class APIError extends Error {
  constructor(public code:string,message:string,public status:number,public details:Json={}){super(message);}
}
export function configure(value:Config){config=value;}
export async function getIdentity():Promise<IdentityClient>{
  if(identity)return identity;
  if(!config.firebase_api_key||!config.firebase_project_id)throw new Error('Firebase public client configuration is missing.');
  const modulePath='/assets/vendor/identity.js';
  try{const mod=await import(modulePath);identity=mod.createIdentity(config);return identity!;}
  catch{throw new Error('Authentication bundle unavailable. The operator must build the production frontend.');}
}
export async function signOut(){if(identity)await identity.logout();}
async function headers():Promise<Record<string,string>>{
  if(config?.auth_mode==='dev')return {'X-Dev-User':localStorage.getItem('oa_demo_identity')||'demo'};
  const token=identity?await identity.token():'';
  return token?{Authorization:`Bearer ${token}`} : {};
}
export async function api<T=Json>(path:string,method='GET',body?:unknown,key?:string):Promise<T>{
  const h=await headers();
  if(body!==undefined && !(body instanceof FormData)) h['Content-Type']='application/json';
  if(key)h['Idempotency-Key']=key;
  const response=await fetch('/api/v1'+path,{method,headers:h,credentials:'omit',
    body:body===undefined?undefined:body instanceof FormData?body:JSON.stringify(body)});
  if(response.status===204)return {} as T;
  const data=await response.json();
  if(!response.ok) throw new APIError(data.error?.code||'REQUEST_FAILED',data.error?.message||'Request failed.',response.status,data.error||{});
  return data as T;
}
export async function download(path:string,filename:string){
  const response=await fetch('/api/v1'+path,{headers:await headers(),credentials:'omit'});
  if(!response.ok){const data=await response.json();throw new APIError(data.error?.code,data.error?.message,response.status);}
  saveBlob(await response.blob(),filename);
}
export function saveBlob(blob:Blob,name:string){
  const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
