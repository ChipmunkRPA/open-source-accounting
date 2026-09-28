"""Explicit bounded integrity observations, never acquisition or review approval."""
import json
from sqlalchemy import select
from ..models import SourceArtifact, SourceExtraction, Audit, now
from ..sec_core.core import canonical, digest
from ..errors import fail
from . import intake, rights, counsel
from .storage import Storage


def read(storage,key,expected_hash,maximum,expected_size=None):
    try:
        data=storage.get_bounded(key,maximum)
    except FileNotFoundError:
        return {'status':'missing'},None
    except OverflowError:
        return {'status':'oversized'},None
    except ValueError:
        return {'status':'invalid_object'},None
    except Exception:
        # Provider errors may contain private object names/credentials. Never return them.
        return {'status':'unreadable'},None
    observed={'observed_sha256':digest(data),'observed_bytes':len(data)}
    if observed['observed_sha256']!=expected_hash or expected_size is not None and len(data)!=expected_size:
        return {'status':'mismatch',**observed},None
    return {'status':'verified',**observed},data


def raw_check(storage,artifact,manifest):
    expected=f'sources/{artifact.work_id}/raw/{artifact.raw_sha256}.bin'
    if artifact.object_key!=expected or not 0<artifact.byte_count<=manifest['max_bytes']:
        return {'status':'invalid_record'},None
    return read(storage,artifact.object_key,artifact.raw_sha256,manifest['max_bytes'],artifact.byte_count)


def extraction_check(storage,artifact,extraction):
    expected=f'sources/{artifact.work_id}/parsed/{artifact.raw_sha256}-{extraction.normalized_sha256}.json'
    if extraction.object_key!=expected:return {'status':'invalid_record'},None
    result,data=read(storage,extraction.object_key,extraction.normalized_sha256,32_000_000)
    if data is None:return result,None
    try:
        passages=json.loads(data)
        if (not isinstance(passages,list) or not 0<len(passages)<=10000 or len(passages)!=extraction.passage_count
                or any(not isinstance(p,dict) or not isinstance(p.get('text'),str) or not isinstance(p.get('locator'),str)
                       or not p['locator'].strip() or digest(p['text'])!=p.get('sha256') for p in passages)):
            raise ValueError()
    except (ValueError,TypeError,KeyError,RecursionError):
        return {**result,'status':'invalid_passages'},None
    return result,passages


def verify(db,settings,artifact_id,actor_id,*,commit=True):
    artifact=db.get(SourceArtifact,artifact_id)
    if not artifact:fail('NOT_FOUND','Artifact not found.',404)
    from ..models import IntakeWork
    owner=db.get(IntakeWork,artifact.work_id)
    counsel.lock_source(db,owner.source_id)
    work,source,manifest=intake.authorize(db,artifact.work_id,['store_raw'],lock=True)
    extractions=db.scalars(select(SourceExtraction).where(SourceExtraction.artifact_id==artifact.id)
                          .order_by(SourceExtraction.id).limit(11)).all()
    if len(extractions)>10:fail('VERIFICATION_LIMIT','Verify this artifact through a partitioned maintenance process; more than 10 extractions exist.',422)
    storage=Storage(settings)
    raw,_=raw_check(storage,artifact,manifest)
    extracted=[]
    for ex in extractions:
        permitted=rights.allowed(source,'store_text',context={'route':manifest['route'],'audience':'internal_ingestion'})
        result,_=extraction_check(storage,artifact,ex) if permitted else ({'status':'not_authorized'},None)
        extracted.append({'extraction_id':ex.id,'expected_sha256':ex.normalized_sha256,
                          'parser_version':ex.parser_version,'passage_count':ex.passage_count,**result})
    # Expired permissions do not yield a completed verification receipt.
    operations=['store_raw']+(['store_text'] if any(r['status']!='not_authorized' for r in extracted) else [])
    intake.authorize(db,work.id,operations)
    failures=[{'unit':'raw','status':raw['status']}] if raw['status']!='verified' else []
    failures += [{'unit':r['extraction_id'],'status':r['status']} for r in extracted if r['status'] not in {'verified','not_authorized'}]
    holds=dict(source.policy.get('integrity_holds') or {})
    if failures:
        if artifact.id not in holds:source.policy_version+=1
        holds[artifact.id]={'failures':failures,'observed_at':now(),'actor_id':actor_id}
        source.policy={**source.policy,'integrity_holds':holds}
    data={'artifact_id':artifact.id,'work_id':work.id,'family_id':manifest['family_id'],
          'manifest_sha256':work.manifest_sha256,'policy_version':source.policy_version,
          'integrity_hold':artifact.id in holds,'work_on_hold':bool(holds),
          'raw':{'expected_sha256':artifact.raw_sha256,'expected_bytes':artifact.byte_count,**raw},
          'extractions':extracted,'observed_at':now(),
          'notice':'Point-in-time stored-byte integrity only. Not publisher authenticity, complete acquisition, citation accuracy, professional approval or index/evaluation verification. Failures place the entire work on hold for output and model use. Successful checks never release holds or restore old evidence. No repair or source approval performed.'}
    result={**data,'observation_sha256':digest(canonical(data))}
    db.add(Audit(actor_id=actor_id,action='intake.integrity_observed',target_id=artifact.id,detail=result))
    if commit:db.commit()
    else:db.flush()
    return result


def release(db,settings,artifact_id,payload,actor_id):
    from ..models import IntakeWork, Source
    artifact=db.get(SourceArtifact,artifact_id)
    if not artifact:fail('NOT_FOUND','Artifact not found.',404)
    work=db.get(IntakeWork,artifact.work_id)
    source=counsel.lock_source(db,work.source_id)
    if source.policy_version!=payload.expected_policy_version:
        fail('REVISION_CONFLICT','Reload the current work policy version.',409)
    if artifact.id not in (source.policy.get('integrity_holds') or {}):
        fail('NO_INTEGRITY_HOLD','This artifact has no active integrity hold.',409)
    result=verify(db,settings,artifact_id,actor_id,commit=False)
    if result['raw']['status']!='verified' or any(r['status']!='verified' for r in result['extractions']):
        # Preserve the failed recheck rather than roll back its observation.
        db.commit()
        fail('INTEGRITY_NOT_RESTORED','Every raw/normalized unit must verify with current permissions before release.',409)
    source=db.get(Source,source.id)
    holds=dict(source.policy.get('integrity_holds') or {});holds.pop(artifact.id)
    source.policy={**source.policy,'integrity_holds':holds};source.policy_version+=1
    db.add(Audit(actor_id=actor_id,action='intake.integrity_hold_released',target_id=artifact.id,
                 detail={'observation_sha256':result['observation_sha256'],'policy_version':source.policy_version,
                         'note':payload.note,'old_evidence_restored':False}))
    db.commit()
    return {'artifact_id':artifact.id,'policy_version':source.policy_version,'work_on_hold':bool(holds),
            'old_evidence_restored':False,'approval_granted':False}
