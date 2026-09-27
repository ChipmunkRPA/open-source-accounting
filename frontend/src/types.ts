export type Json = Record<string, any>;
export interface Config {
  app_env: string; auth_mode: 'dev'|'firebase'; model_provider: string; model_id: string;
  firebase_api_key: string; firebase_project_id: string; firebase_auth_domain: string; firebase_tenant_id: string; mfa_required: boolean; auth_recent_seconds:number;
  billing_enabled: boolean; demo_billing_enabled: boolean; billing_terms_approved: boolean;
  agent_tasks_per_month: number; max_upload_mb: number; experimental_agents_enabled: boolean;
}
export interface Account {
  id: string; name: string; email: string; role: string; preferences: Json;
  security?: {mode:string;mfa_verified:boolean;factor:string|null;auth_time:number};
  access: {state: string; agent_allowed: boolean; access_until: number|null};
  usage: {consumed: number; reserved: number; limit: number; reset_at: number|null; proposed_policy: boolean};
  subscription: Json|null;
}
export interface Workspace {id:string; name:string; role:string}
export interface App {
  config: Config; me: Account|null; workspaces: Workspace[];
  content: HTMLElement; banner: HTMLElement;
  navigate: (path:string)=>void;
  refreshAccount: ()=>Promise<void>;
  showError: (error:unknown)=>void;
  upgrade: (task?:string)=>void;
  cleanup?: ()=>void;
  canLeave?: ()=>boolean;
}
