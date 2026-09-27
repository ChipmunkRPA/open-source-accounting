"""Local demonstration data only: original teaching prose, reference metadata, no scraped standards."""
from .models import User, Workspace, Membership, Source
from .config import Settings
from .db import Database
from .services.rights import record_approval

ORIGINAL_POLICY = {'basis': 'original', 'commercial_use': True, 'model_input': True,
                   'store_text': True, 'display_full': True, 'quote': True, 'export': True,
                   'embed': True, 'train': False, 'review_note': 'Original sample content written for this code package; not authoritative accounting guidance.'}
REFERENCE_POLICY = {'basis': 'reference_only', 'commercial_use': False, 'model_input': False,
                    'store_text': False, 'display_full': False, 'quote': False, 'export': False,
                    'embed': False, 'train': False, 'review_note': 'Reference metadata only. No permission to reproduce publisher text is represented.'}


SAMPLES = [
    ('sample-research', 'How to document an accounting research question',
     'Start with the reporting framework, the entity type, the reporting period, and the issue to be resolved. Separate user-confirmed facts from assumptions.\n\n'
     'For a subscription arrangement with implementation services, collect the agreement and amendments, identify the promises and relevant dependencies, and explain which facts remain unresolved. This checklist does not determine revenue treatment.\n\n'
     'Record the sources actually examined. A citation to unavailable authoritative text is a reference, not proof that the text was reviewed. Preserve alternative interpretations and questions for the reviewer.'),
    ('sample-memo', 'Preparing a reviewable technical memo',
     'A draft memo can separate the issue, facts, authority, analysis, alternatives, conclusion and unresolved items. Every material claim should point to the actual evidence examined.\n\n'
     'Do not turn an AI check into a professional-review badge. A reviewer should record their identity, the revision reviewed and the scope of their review.'),
    ('sample-documents', 'Reading contracts and amendments for research',
     'Compare the original contract and amendments without assuming that every textual change changes the accounting outcome. Confirm effective dates, pricing, services, renewal terms and unresolved commercial facts.\n\n'
     'Extracted document text can omit layout details. Consult the original document where a table, signature, footnote or missing page changes the interpretation. This application does not perform OCR.'),
    ('sample-audit', 'Organizing an audit evidence request',
     'A draft evidence request identifies the process, risk, assertion, document owner and missing evidence. This is preparation, not evidence that procedures have been performed.\n\n'
     'A description of a control does not demonstrate operating effectiveness. Record design questions and implementation evidence separately from tests of operation.'),
]


def seed(db):
    for key, email, name, role in [
        ('demo', 'ray.demo@example.test', 'Ray · local demo', 'member'),
        ('reviewer', 'reviewer@example.test', 'Demo Reviewer', 'member'),
        ('admin', 'admin@example.test', 'Source Administrator', 'admin'),
        ('approver', 'approver@example.test', 'Rights Approver', 'rights_approver'),
        ('editor', 'editor@example.test', 'Technical Reviewer', 'technical_reviewer')]:
        if not db.get(User, key):
            db.add(User(id=key, email=email, name=name, role=role))
    db.flush()
    if not db.get(Workspace, 'demo-workspace'):
        db.add(Workspace(id='demo-workspace', owner_id='demo', name='My accounting research'))
        db.flush()
        db.add(Membership(workspace_id='demo-workspace', user_id='demo', role='owner'))
        db.add(Membership(workspace_id='demo-workspace', user_id='reviewer', role='reviewer'))
    if not db.get(Workspace, 'reviewer-private'):
        db.add(Workspace(id='reviewer-private', owner_id='reviewer', name='Reviewer private workspace'))
        db.flush()
        db.add(Membership(workspace_id='reviewer-private', user_id='reviewer', role='owner'))
    for source_id, title, text in SAMPLES:
        if not db.get(Source, source_id):
            row = Source(id=source_id, title=title, publisher='Open Source Accounting · original demonstration material',
                          text=text, kind='original_commentary', framework='BOTH', policy=ORIGINAL_POLICY,
                          reviewed=True, created_by='admin', approved_by='approver', version_label='Demo 1')
            db.add(row)
            db.flush()
            record_approval(row, 'approver')  # Synthetic local demo only; production prohibits seed().
    for source_id, title, publisher, url in [
        ('ref-asc606', 'ASC 606 — Revenue from Contracts with Customers', 'FAF / FASB', 'https://asc.fasb.org/'),
        ('ref-asc842', 'ASC 842 — Leases', 'FAF / FASB', 'https://asc.fasb.org/'),
        ('ref-pcaob2201', 'PCAOB AS 2201 — Internal Control Audit', 'PCAOB', 'https://pcaobus.org/oversight/standards/auditing-standards')]:
        if not db.get(Source, source_id):
            db.add(Source(id=source_id, title=title, publisher=publisher, canonical_url=url, text=None,
                          kind='reference', framework='US_GAAP', policy=REFERENCE_POLICY, reviewed=True,
                          created_by='admin', approved_by='approver'))
    db.commit()


if __name__ == '__main__':
    config = Settings()
    if config.app_env == 'production':
        raise SystemExit('Demo seed is prohibited in production.')
    database = Database(config.database_url)
    database.create_all()
    with database.Session() as db:
        seed(db)
    print('Local demo initialized. No proprietary accounting standard text was imported.')
