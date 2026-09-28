"""Bounded metadata-only staged coverage and reverse dependency reporting."""
from collections import Counter,defaultdict
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy import select,func
from ..models import Source,EditorialReview,IntakeWork,SourceArtifact,SourceExtraction,now
from ..sec_core.core import CorePack,canonical,digest
from ..errors import fail
from . import editorial,applicability,parser_review,dependencies,rights,intake

MAX_SOURCES=2000
SEC_FAMILIES={'reg_sx':'SEC_RULES','reg_sk':'SEC_RULES','reg_g':'SEC_RULES','sab':'SEC_SAB','frm':'SEC_FRM','cfi':'SEC_CFI','forms':'SEC_FORMS'}


def report(db,settings,*,offset=0,limit=50,affected_by=None):
    sources=db.scalars(select(Source).order_by(Source.id).limit(MAX_SOURCES+1)).all()
    if len(sources)>MAX_SOURCES:fail('REPORT_LIMIT','The staged corpus exceeds this report bound; partition it before reporting.',422)
    lookup={s.id:s for s in sources}
    if affected_by and affected_by not in lookup:fail('NOT_FOUND','Affected source not found.',404)
    registry=intake.families(settings)
    sec=CorePack(Path(settings.content_dir)/'sec_core')
    works={w.source_id:w for w in db.scalars(select(IntakeWork).where(IntakeWork.source_id.in_(lookup)))} if lookup else {}
    families={k:Counter(staged_sources=0,artifact_records=0,extraction_records=0,current_technical_records=0,
                        current_applicability_records=0,original_sources_missing_bindings=0) for k in registry}
    for family,count in db.execute(select(IntakeWork.family_id,func.count(SourceArtifact.id)).join(SourceArtifact,SourceArtifact.work_id==IntakeWork.id).group_by(IntakeWork.family_id)):
        families.setdefault(family,Counter())['artifact_records']=count
    for family,count in db.execute(select(IntakeWork.family_id,func.count(SourceExtraction.id)).join(SourceArtifact,SourceArtifact.work_id==IntakeWork.id).join(SourceExtraction,SourceExtraction.artifact_id==SourceArtifact.id).group_by(IntakeWork.family_id)):
        families.setdefault(family,Counter())['extraction_records']=count
    reverse=defaultdict(set);rows=[];graph_complete=True
    for source in sources:
        p=source.policy or {};issues=[]
        work=works.get(p.get('intake_parent_id') or source.id)
        family=work.family_id if work else 'ORIGINAL' if p.get('content_item_id') else None
        if p.get('sec_core'):
            entry=sec.entries.get(p['sec_core'].get('source_id'),{})
            family=SEC_FAMILIES.get(entry.get('family'))
        family=family or 'UNCLASSIFIED'
        record=db.get(EditorialReview,p.get('technical_review_record_id')) if p.get('technical_review_record_id') else None
        integrity=bool(record and record.source_id==source.id and record.payload_sha256==digest(canonical(record.payload)))
        if record and not integrity:issues.append('technical_record_integrity')
        bindings=record.payload.get('reference_bindings',[]) if integrity else []
        refs=set(p.get('content_reference_ids',[]))
        missing=sorted(refs-{b.get('reference_id') for b in bindings}) if p.get('content_item_id') else []
        complete=not p.get('content_item_id') or bool(refs and not missing)
        stale=[]
        for b in bindings:
            target=lookup.get(b.get('source_id'))
            reason='missing_source' if not target else 'disabled_source' if not target.enabled else None
            if target and not reason and (target.policy_version!=b.get('policy_version') or editorial.revision(target)!=b.get('review_revision') or dependencies.locator(target)!=b.get('locator')):
                reason='changed_revision_or_policy'
            if reason:stale.append({'reference_id':b.get('reference_id'),'source_id':b.get('source_id'),'reason':reason})
        try:
            historical=dependencies.output_bindings(source,all_bodies=True)
            for b in historical:reverse[b['source_id']].add(source.id)
        except HTTPException as exc:
            issues.append(exc.detail['code']);graph_complete=False;historical=[]
        if p.get('intake_parent_id'):reverse[p['intake_parent_id']].add(source.id)
        technical=editorial.current(source) if p.get('requires_technical_review') or record else None
        applicable=applicability.current(source) is not None
        parser=parser_review.current(source) if p.get('intake_extraction_id') else None
        rights_current=bool(source.reviewed and p.get('rights_reviewed_revision')==rights.revision(source))
        if not rights_current:issues.append('rights_revision_missing_or_stale')
        if not source.enabled:issues.append('source_disabled')
        if p.get('integrity_holds'):issues.append('integrity_hold')
        if not complete:issues.append('missing_exact_reference_bindings')
        if stale:issues.append('stale_reference_bindings')
        if technical is False:issues.append('no_current_technical_record')
        if not applicable:issues.append('no_current_applicability_record')
        if parser is False:issues.append('no_current_parser_record')
        row={'source_id':source.id,'title':source.title,'edition':source.version_label,'family_id':family,
             'enabled':source.enabled,'policy_version':source.policy_version,'review_revision':editorial.revision(source),
             'rights_revision_current':rights_current,
             'technical_record_current':technical,'applicability_record_current':applicable,'parser_record_current':parser,
             'reference_count':len(refs),'binding_count':len(bindings),'reference_coverage_complete':complete,
             'missing_reference_ids':missing,'stale_bindings':stale,'historical_dependency_count':len({b['source_id'] for b in historical}),
             'artifact_recorded':bool(p.get('intake_artifact_id') and db.get(SourceArtifact,p['intake_artifact_id'])),
             'extraction_recorded':bool(p.get('intake_extraction_id') and db.get(SourceExtraction,p['intake_extraction_id'])),
             'issues':sorted(set(issues))}
        rows.append(row);count=families.setdefault(family,Counter())
        count['staged_sources']+=1;count['current_technical_records']+=technical is True
        count['current_applicability_records']+=applicable
        count['original_sources_missing_bindings']+=not complete
    # Remove leaves to identify cycles and ancestors whose historical lineage reaches them.
    pending={sid:0 for sid in lookup}
    for target,parents in reverse.items():
        if target in lookup:
            for parent in parents:pending[parent]+=1
    leaves=[sid for sid,count in pending.items() if not count]
    while leaves:
        for parent in reverse[leaves.pop()]:
            pending[parent]-=1
            if pending[parent]==0:leaves.append(parent)
    cyclic=sorted(sid for sid,count in pending.items() if count>0)
    for row in rows:
        if row['source_id'] in cyclic:row['issues'].append('historical_cycle_or_dependency_on_cycle')
    impacted=set()
    if affected_by:
        todo=[affected_by]
        while todo:
            for parent in reverse[todo.pop()]:
                if parent not in impacted and parent!=affected_by:impacted.add(parent);todo.append(parent)
    selected=[r for r in rows if not affected_by or r['source_id'] in impacted]
    data={'scope':'staged_database_metadata','staged_source_count':len(rows),'source_limit':MAX_SOURCES,
          'graph_complete':graph_complete,'cyclic_or_dependent_source_ids':cyclic,'affected_by':affected_by,'affected_source_ids':sorted(impacted),
          'families':[{'family_id':k,**dict(v)} for k,v in sorted(families.items())],
          'total':len(selected),'offset':offset,'items':selected[offset:offset+limit],
          'notice':'Recorded states are not independent professional verification or Agent admission. Artifact/extraction counts are database records; bytes, indexing and evaluations were not verified. This observed read set may change; runtime gates recheck permissions and context.'}
    return {**data,'generated_at':now(),'report_sha256':digest(canonical(data))}
