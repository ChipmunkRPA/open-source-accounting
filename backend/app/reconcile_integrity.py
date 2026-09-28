"""Explicit authenticated operator client; private resumable state, no background work."""
import argparse
from collections import Counter
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import time
from urllib.parse import urlsplit
import httpx

MAX_ARTIFACTS=10000
ROOT=Path(__file__).resolve().parents[2]


def checksum(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def base_url(value):
    parsed=urlsplit(value)
    if (parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'','/'}
            or not parsed.hostname or parsed.scheme not in {'https','http'}
            or parsed.scheme=='http' and parsed.hostname not in {'localhost','127.0.0.1','::1'}):
        raise ValueError('Use an HTTPS origin or a local loopback HTTP origin, without credentials/path/query.')
    return value.rstrip('/')


def require(response):
    if response.status_code!=200:
        raise ValueError('Inventory request failed with HTTP '+str(response.status_code)+'. No state was created.')
    return response.json()


def collect(client,origin,family=None):
    started=int(time.time())
    registry=require(client.get('/api/v1/admin/intake/families'))['items']
    families=sorted({r['id'] for r in registry})
    if family and family not in families:raise ValueError('Unknown source family.')
    items=[];seen=set();after='';pages=0
    while True:
        pages+=1
        if pages>101:raise ValueError('Inventory pagination exceeded its bound.')
        page=require(client.get('/api/v1/admin/intake/artifacts',params={'after':after,'limit':100,**({'family':family} if family else {})}))
        for row in page['items']:
            if row['artifact_id'] in seen:raise ValueError('Duplicate inventory identity; restart inventory.')
            seen.add(row['artifact_id']);items.append(row)
            if len(items)>MAX_ARTIFACTS:raise ValueError('Inventory exceeds 10,000 artifacts; partition before reconciliation.')
        cursor=page['next_after']
        if cursor is None:break
        if cursor<=after:raise ValueError('Inventory cursor did not advance.')
        after=cursor
    inventory={'base_url':origin,'selected_family':family,'families':families,'items':items,'started_at':started,'finished_at':int(time.time())}
    state={'schema_version':1,'inventory':inventory,'inventory_sha256':checksum(inventory),'results':{},
            'notice':'Frozen membership from a non-atomic paginated scan. New/changed records require a new inventory. Observations are not authenticity, approval, indexing or evaluation evidence.'}
    state['state_sha256']=checksum(state)
    return state


def validate(state,origin):
    if checksum({k:v for k,v in state.items() if k!='state_sha256'})!=state.get('state_sha256'):
        raise ValueError('State checksum mismatch.')
    if state.get('schema_version')!=1 or state['inventory'].get('base_url')!=origin:
        raise ValueError('State schema/origin mismatch.')
    if checksum(state['inventory'])!=state['inventory_sha256']:
        raise ValueError('Inventory changed; refusing to resume.')
    ids=[r['artifact_id'] for r in state['inventory']['items']]
    if len(ids)>MAX_ARTIFACTS or len(ids)!=len(set(ids)) or set(state['results'])-set(ids):
        raise ValueError('Invalid inventory membership.')


def advance(client,state,steps,save):
    """Each observed result is durable before proceeding; interruptions leave remaining units pending."""
    completed=0
    for row in state['inventory']['items']:
        aid=row['artifact_id']
        if aid in state['results']:continue
        if completed>=steps:break
        try:
            response=client.post('/api/v1/admin/intake/artifacts/'+aid+'/verify',json={'expected_raw_sha256':row['raw_sha256']})
        except httpx.HTTPError:
            return {'paused':'transport_error','completed_this_run':completed}
        if response.status_code in {401,429} or response.status_code>=500:
            return {'paused':'http_'+str(response.status_code),'completed_this_run':completed}
        data=response.json()
        code=data.get('error',{}).get('code','')
        if code in {'RECENT_AUTH_REQUIRED','FORBIDDEN'}:
            return {'paused':code,'completed_this_run':completed}
        if response.status_code==200:
            if (data.get('artifact_id')!=aid or data.get('work_id')!=row['work_id'] or data.get('family_id')!=row['family_id']
                    or data.get('manifest_sha256')!=row['manifest_sha256']
                    or data.get('raw',{}).get('expected_sha256')!=row['raw_sha256']
                    or checksum({k:v for k,v in data.items() if k!='observation_sha256'})!=data.get('observation_sha256')):
                return {'paused':'response_identity_mismatch','completed_this_run':completed}
            observed={'status':'observed','observation':data}
        elif response.status_code==403 and code=='SOURCE_POLICY_BLOCK':observed={'status':'denied','error_code':code}
        elif response.status_code in {404,409,422}:observed={'status':'unobserved_error','error_code':code or 'http_'+str(response.status_code)}
        else:return {'paused':'unexpected_http_'+str(response.status_code),'completed_this_run':completed}
        state['results'][aid]={**observed,'recorded_at':int(time.time())};save(state);completed+=1
    return {'completed_this_run':completed,'remaining':len(state['inventory']['items'])-len(state['results'])}


def report(state):
    families={f:Counter(inventory_artifacts=0,verified_raw=0,failed_raw=0,denied=0,unobserved=0,held_at_observation=0) for f in state['inventory']['families']}
    for row in state['inventory']['items']:
        counts=families.setdefault(row['family_id'],Counter())
        counts['inventory_artifacts']+=1
        result=state['results'].get(row['artifact_id'],{})
        if result.get('status')=='observed':
            observation=result['observation'];counts['verified_raw' if observation['raw']['status']=='verified' else 'failed_raw']+=1
            counts['held_at_observation']+=bool(observation.get('work_on_hold'))
            for ex in observation.get('extractions',[]):counts['observed_extractions_'+ex['status']]+=1
        elif result.get('status')=='denied':counts['denied']+=1
        else:counts['unobserved']+=1
    return {'inventory_sha256':state['inventory_sha256'],'families':[{'family_id':f,'in_scope':not state['inventory'].get('selected_family') or state['inventory']['selected_family']==f,**dict(c)} for f,c in sorted(families.items())],
            'pending':len(state['inventory']['items'])-len(state['results']),
            'notice':state['notice']+' Held artifacts overlap other columns. Extractions count only returned observations; missing/unobserved extraction inventory is not inferred. Results may subsequently become stale.'}


@contextmanager
def state_lock(path):
    import fcntl
    # Local operator state must not become a public repository artifact.
    if path.is_relative_to(ROOT):raise ValueError('Keep reconciliation state outside this repository.')
    if path.is_symlink():raise ValueError('State cannot be a symlink.')
    fd=os.open(str(path)+'.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        if os.fstat(fd).st_mode & 0o077:raise ValueError('Lock file must be private.')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:os.close(fd)


def save_state(path,state):
    state['state_sha256']=checksum({k:v for k,v in state.items() if k!='state_sha256'})
    fd,temp=tempfile.mkstemp(prefix='.integrity-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as handle:
            json.dump(state,handle,sort_keys=True);handle.flush();os.fsync(handle.fileno())
        os.replace(temp,path)
        directory=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['plan','run','report'])
    parser.add_argument('--base-url',required=True)
    parser.add_argument('--state',required=True,type=Path)
    parser.add_argument('--token-env',default='OSA_ADMIN_ID_TOKEN')
    parser.add_argument('--steps',type=int,default=5)
    parser.add_argument('--family',help='Optional source-family partition, plan command only.')
    args=parser.parse_args()
    try:
        if args.family and args.command!='plan':raise ValueError('Family scope is frozen in the plan; omit --family when resuming.')
        origin=base_url(args.base_url);path=args.state.parent.resolve()/args.state.name
        if not 1<=args.steps<=25:raise ValueError('Choose 1–25 artifact steps per run.')
        with state_lock(path):
            state=None
            if path.exists():
                if not stat.S_ISREG(path.stat().st_mode) or path.stat().st_mode & 0o077:raise ValueError('State must be a private regular file (mode 600).')
                if path.stat().st_size>64_000_000:raise ValueError('State exceeds 64 MB.')
                state=json.loads(path.read_text());validate(state,origin)
            if args.command=='report':
                if state is None:raise ValueError('Create a plan first.')
                print(json.dumps(report(state),indent=2));return
            token=os.environ.get(args.token_env,'')
            if not token:raise ValueError('Supply a current verified-MFA administrator ID token through the named environment variable.')
            with httpx.Client(base_url=origin,headers={'Authorization':'Bearer '+token},follow_redirects=False,timeout=360,trust_env=False) as client:
                if args.command=='plan':
                    if state is not None:raise ValueError('State exists; choose a new path for a new inventory.')
                    state=collect(client,origin,args.family);save_state(path,state)
                    print(json.dumps({'planned_artifacts':len(state['inventory']['items']),'inventory_sha256':state['inventory_sha256']}))
                else:
                    if state is None:raise ValueError('Create a plan first.')
                    print(json.dumps(advance(client,state,args.steps,lambda value:save_state(path,value))))
    except (ValueError,OSError,KeyError,TypeError,httpx.HTTPError) as exc:
        # Never print a transport exception, token, URL query or private response body.
        message=str(exc) if isinstance(exc,ValueError) and not isinstance(exc,json.JSONDecodeError) else type(exc).__name__
        parser.exit(2,'Reconciliation stopped: '+message+'\n')


if __name__=='__main__':main()
