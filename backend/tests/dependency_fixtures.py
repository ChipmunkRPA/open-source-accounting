"""Synthetic publication bindings only; never proof for shipped content."""
from app.models import Source,now
from app.services import editorial,rights,applicability
from app.editorial_schemas import EditorialDecision
from app.applicability_schemas import ApplicabilityDecision
from app.sec_core.core import digest


def bindings(client,sid):
    with client.app.state.db.Session() as db:
        parent=db.get(Source,sid)
        target=Source(title='Synthetic dependency, not actual cited publication',publisher='Test fixture',
            canonical_url='https://example.test/synthetic',version_label='synthetic-1',text='Synthetic dependency for software checks only.',
            kind='original_commentary',framework='BOTH',created_by='admin',reviewed=True,approved_by='approver',
            policy={'basis':'original','commercial_use':True,'display_full':True,'model_input':True,'quote':True,'export':True,'store_text':True,'requires_technical_review':True})
        db.add(target);db.flush();rights.record_approval(target,'approver');db.commit()
        editorial.record(db,target,EditorialDecision(expected_policy_version=target.policy_version,
            expected_review_revision=editorial.revision(target),content_sha256=digest(target.text),decision='approved',
            review_scope='Synthetic dependency fixture',review_note='Synthetic technical review; not a real professional review.',
            evidence_ref='ev_synthetic_dependency',evidence_sha256='a'*64,expires_at=now()+3600,confirm_actual_review_performed=True),'editor')
        applicability.record(db,target,ApplicabilityDecision(expected_policy_version=target.policy_version,
            expected_review_revision=editorial.revision(target),decision='approved',issued_at='2010-01-01',publicly_available_at='2010-01-01',
            effective_from='2010-01-01',confirm_open_ended=True,frameworks=['US_GAAP','IFRS'],entity_types=['public','private','nonprofit'],
            review_scope='Synthetic applicability fixture',review_note='Synthetic applicability only; no real professional review.',
            evidence_ref='ev_synthetic_dependency',evidence_sha256='a'*64,expires_at=now()+3600,confirm_actual_applicability_review=True),'editor')
        return [{'reference_id':ref,'source_id':target.id,'review_revision':editorial.revision(target),
                 'policy_version':target.policy_version,'locator':target.canonical_url} for ref in parent.policy['content_reference_ids']]
