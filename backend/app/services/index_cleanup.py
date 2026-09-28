"""Explicit resumable cleanup with bounded hash-only receipts, no source acquisition."""
from sqlalchemy import select, func, update
from ..models import SearchIndexSweep, SourceSearchIndex, Source, Audit, uid, now
from ..sec_core.core import canonical, digest
from ..errors import fail
from . import source_search

VERSION='source-index-cleanup-1'
BATCH_SIZE=100


def status(sweep):
    return {key:getattr(sweep,key) for key in ('id','state','sequence','cursor','upper_id',
        'initial_stored','scanned','retained','removed','vanished','started_at','completed_at')} | {
        'cleanup_version':sweep.cleanup_version,'atomic_inventory':False,'backup_erasure_verified':False,
        'coverage_note':'Counts are observations during a bounded ID-range sweep, not a frozen corpus or permanent clearance. New entries behind the cursor require a new sweep.'}


def start(db, actor_id, request_key):
    request_hash=digest(canonical({'actor_id':actor_id,'request_key':request_key}))
    if db.bind.dialect.name=='postgresql':
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    # A conflict-safe insert acquires the SQLite writer lock before observing the inventory.
    result=db.execute(insert(SearchIndexSweep).values(id=uid(),request_sha256=request_hash,
        actor_id=actor_id,cleanup_version=VERSION,cursor='',upper_id='',state='running',sequence=0,initial_stored=0,
        scanned=0,retained=0,removed=0,vanished=0,started_at=now()).on_conflict_do_nothing(
            index_elements=['request_sha256']))
    sweep=db.scalar(select(SearchIndexSweep).where(SearchIndexSweep.request_sha256==request_hash).with_for_update())
    if result.rowcount:
        sweep.upper_id=db.scalar(select(func.max(SourceSearchIndex.source_id))) or ''
        sweep.initial_stored=db.scalar(select(func.count()).select_from(SourceSearchIndex).where(
            SourceSearchIndex.source_id<=sweep.upper_id))
        if not sweep.upper_id:sweep.state,sweep.completed_at='completed',now()
        db.add(Audit(actor_id=actor_id,action='source.index_cleanup_started',target_id=sweep.id,
            detail={'cleanup_version':VERSION,'upper_id':sweep.upper_id,'initial_stored':sweep.initial_stored,
                    'atomic_inventory':False}))
    db.flush()
    return sweep


def advance(db, sweep_id, expected_sequence, actor_id, *, batch_size=BATCH_SIZE):
    if not 1<=batch_size<=BATCH_SIZE:raise ValueError('Invalid cleanup batch size.')
    if db.bind.dialect.name=='sqlite':
        db.execute(update(SearchIndexSweep).where(SearchIndexSweep.id==sweep_id).values(sequence=SearchIndexSweep.sequence))
    sweep=db.scalar(select(SearchIndexSweep).where(SearchIndexSweep.id==sweep_id).with_for_update()
                    .execution_options(populate_existing=True))
    if not sweep:fail('NOT_FOUND','Index cleanup sweep not found.',404)
    if sweep.cleanup_version!=VERSION:
        fail('CLEANUP_VERSION_CHANGED','This sweep uses another cleanup version. Start a new sweep with a new request key.',409)
    if sweep.sequence!=expected_sequence:
        fail('REVISION_CONFLICT','Reload the cleanup sequence before advancing.',409)
    if sweep.state=='completed':return sweep
    ids=list(db.scalars(select(SourceSearchIndex.source_id).where(
        SourceSearchIndex.source_id>sweep.cursor,SourceSearchIndex.source_id<=sweep.upper_id)
        .order_by(SourceSearchIndex.source_id).limit(batch_size)))
    observations=[]
    for source_id in ids:
        # Same lock ordering as rebuild/disable: source before derived index.
        source=db.scalar(select(Source).where(Source.id==source_id).with_for_update()
                         .execution_options(populate_existing=True))
        entry=db.scalar(select(SourceSearchIndex).where(SourceSearchIndex.source_id==source_id).with_for_update()
                        .execution_options(populate_existing=True))
        observation={'source_id':source_id}
        if not entry:
            sweep.vanished+=1;observation['outcome']='vanished_before_check'
        else:
            observation.update(index_version=entry.index_version,index_revision=entry.revision,
                               indexed_text_sha256=digest(entry.search_text))
            if source and source_search.current(source,entry):
                sweep.retained+=1;observation['outcome']='retained_current_at_check'
            else:
                sweep.removed+=1;observation['outcome']='removed_stale_or_unauthorized'
                db.delete(entry)
        observations.append(observation)
        sweep.scanned+=1;sweep.cursor=source_id
    sweep.sequence+=1
    if len(ids)<batch_size or sweep.cursor==sweep.upper_id:
        sweep.state,sweep.completed_at='completed',now()
    receipt={'version':VERSION,'sequence':sweep.sequence,'observed_at':now(),'observations':observations,
             'cursor':sweep.cursor,'state':sweep.state}
    db.add(Audit(actor_id=actor_id,action='source.index_cleanup_batch',target_id=sweep.id,
        detail={'receipt':receipt,'receipt_sha256':digest(canonical(receipt))}))
    # Deletions, receipt, sequence and counters share the caller's atomic transaction.
    db.flush()
    return sweep
