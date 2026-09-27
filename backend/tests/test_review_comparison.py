"""Synthetic revision comparisons never establish authority or professional review."""
import copy
import pytest
from app.models import Source, EditorialReview
from app.sec_core.core import canonical, digest
from app.services import editorial, rights, review_comparison
from test_content_library import pack as pack, stage
from test_editorial_ledger import prepared, EDITOR
from test_output_rights import fixture
from conftest import rights_approval


def pair(client, pack):
    left, _=prepared(client,pack)
    with client.app.state.db.Session() as db:item_id=db.get(Source,left).policy['content_item_id']
    item=pack.items[item_id]
    pack.bodies[item_id]+='\nSynthetic revision comparison fixture only.\n'
    pack.items[item_id]=item.model_copy(update={'version':'synthetic-2','sha256':digest(pack.bodies[item_id])})
    right=stage(client,pack)['created'][0]
    assert client.post('/api/v1/admin/sources/'+right+'/approve',headers={'X-Dev-User':'approver'},json=rights_approval(client,right)).status_code==200
    return left,right


def request(client,left,right,**changes):
    with client.app.state.db.Session() as db:
        a,b=db.get(Source,left),db.get(Source,right)
        body={'before_source_id':left,'after_source_id':right,'before_revision':editorial.revision(a),
              'after_revision':editorial.revision(b),'before_policy_version':a.policy_version,'after_policy_version':b.policy_version,**changes}
    return client.post('/api/v1/editorial/compare',headers=EDITOR,json=body)


def test_exact_line_changes_metadata_and_hash_without_approval(client,pack):
    left,right=pair(client,pack)
    response=request(client,left,right);assert response.status_code==200,response.text
    data=response.json();c=data['comparison']
    assert data['comparison_sha256']==digest(canonical(c))
    assert c['body_changed'] and not c['approval_transferred']
    assert any('Synthetic revision' in ''.join(row['after_lines']) for row in c['line_changes'])
    assert any(row['field']=='edition' for row in c['metadata_changes'])
    assert request(client,left,right).json()==data
    with client.app.state.db.Session() as db:
        assert db.query(EditorialReview).count()==0
        assert not rights.allowed(db.get(Source,right),'model_input')


def test_reference_changes_visible_with_identical_body(client,pack):
    left,right=pair(client,pack)
    with client.app.state.db.Session() as db:
        a,b=db.get(Source,left),db.get(Source,right)
        b.text=a.text;policy=copy.deepcopy(b.policy)
        policy['content_reference_snapshot'][0]['review_scope']='Different synthetic verification scope'
        policy['content_references_sha256']=digest(canonical(policy['content_reference_snapshot']))
        b.policy=policy;rights.record_approval(b,'approver');db.commit()
    c=request(client,left,right).json()['comparison']
    assert not c['body_changed'] and not c['line_changes']
    assert any(row['field']=='reference_metadata' for row in c['metadata_changes'])


@pytest.mark.parametrize('side',['before','after'])
def test_stale_revision_and_source_permissions_block_each_side(client,pack,side):
    left,right=pair(client,pack)
    assert request(client,left,right,**{side+'_revision':'0'*64}).status_code==409
    with client.app.state.db.Session() as db:
        source=db.get(Source,left if side=='before' else right)
        source.policy={**source.policy,'display_full':False};rights.record_approval(source,'approver');db.commit()
    assert request(client,left,right).status_code==403


def test_same_or_unrelated_unit_is_not_implicitly_matched(client,pack):
    left,right=pair(client,pack)
    assert request(client,left,left).status_code==422
    with client.app.state.db.Session() as db:
        b=db.get(Source,right);b.policy={**b.policy,'content_item_id':'different-item'};db.commit()
    assert request(client,left,right).status_code==422


def test_policy_version_and_role_are_required(client,pack):
    left,right=pair(client,pack)
    assert request(client,left,right,before_policy_version=999).status_code==409
    with client.app.state.db.Session() as db:
        a,b=db.get(Source,left),db.get(Source,right)
        body={'before_source_id':left,'after_source_id':right,'before_revision':editorial.revision(a),
              'after_revision':editorial.revision(b),'before_policy_version':a.policy_version,'after_policy_version':b.policy_version}
    assert client.post('/api/v1/editorial/compare',json=body).status_code==403


@pytest.mark.parametrize('body',['x'*(review_comparison.MAX_CHARACTERS+1),'x\n'*(review_comparison.MAX_LINES+1)])
def test_comparison_limit_fails_without_truncating(client,pack,body):
    left,right=pair(client,pack)
    with client.app.state.db.Session() as db:
        b=db.get(Source,right);b.text=body;rights.record_approval(b,'approver');db.commit()
    r=request(client,left,right)
    assert r.status_code==422 and r.json()['error']['code']=='COMPARISON_LIMIT'


def test_comparison_preserves_notices_and_obeys_both_work_limits(client,pack):
    left,right=pair(client,pack)
    with client.app.state.db.Session() as db:
        fixture(db,source_id=left,per=100000,total=1000000)
        fixture(db,source_id=right,per=100000,total=1000000)
    r=request(client,left,right);assert r.status_code==200
    assert 'Required synthetic notice' in r.text
    with client.app.state.db.Session() as db:
        # A distinct low-budget reviewed group on the after version must also gate the output.
        fixture(db,source_id=right,per=10,total=10)
    assert request(client,left,right).status_code==403


def test_private_findings_excluded_and_newline_changes_preserved(client,pack):
    left,right=pair(client,pack)
    with client.app.state.db.Session() as db:
        a,b=db.get(Source,left),db.get(Source,right)
        a.text='Line';b.text='Line\n'
        for source in (a,b):
            source.policy={**source.policy,'technical_review_note':'PRIVATE_TEST_FINDING',
                'sec_core':{'applicability_review_note':'PRIVATE_APPLICABILITY'}}
            rights.record_approval(source,'approver')
        db.commit()
    r=request(client,left,right);assert r.status_code==200
    assert 'PRIVATE_TEST_FINDING' not in r.text and 'PRIVATE_APPLICABILITY' not in r.text
    assert r.json()['comparison']['body_changed']
    assert r.json()['comparison']['line_changes'][0]['after_lines']==['Line\n']


@pytest.mark.parametrize('renumbered',[False,True])
def test_intake_editions_require_same_work_and_exact_locator(client,renumbered):
    from test_source_intake import registered,payload,fetch,parse,FakeGateway,RAW,ADMIN
    ids=[]
    for n in (1,2):
        work=registered(client,body=payload(edition='synthetic-'+str(n)))
        raw=RAW.replace(b'229.999',b'229.998') if n==2 and renumbered else RAW
        ex=parse(client,fetch(client,work,gateway=FakeGateway(raw)))
        sid=client.post('/api/v1/admin/intake/extractions/'+ex['id']+'/stage',headers=ADMIN).json()['source_ids'][0]
        assert client.post('/api/v1/admin/sources/'+sid+'/approve',headers={'X-Dev-User':'approver'},json=rights_approval(client,sid)).status_code==200
        ids.append(sid)
    response=request(client,*ids)
    assert response.status_code==(422 if renumbered else 200),response.text
    if not renumbered:assert response.json()['comparison']['logical_unit'][0]=='intake_passage'


def test_sec_snapshot_identity_is_explicit_and_url_alone_is_insufficient(client):
    ids=[]
    with client.app.state.db.Session() as db:
        for n in (1,2):
            source=Source(title='Synthetic SEC identity test',publisher='Test author',canonical_url='https://example.test/same',
                version_label=str(n),text='Synthetic original text '+str(n),created_by='admin',reviewed=True,
                policy={'basis':'original','commercial_use':True,'display_full':True,'requires_technical_review':True,
                        'sec_core':{'source_id':'synthetic-source','passage_id':'synthetic-passage','snapshot_id':str(n)}})
            db.add(source);db.flush();rights.record_approval(source,'approver');ids.append(source.id)
        db.commit()
    result=request(client,*ids)
    assert result.status_code==200 and result.json()['comparison']['logical_unit'][0]=='sec_excerpt'
    with client.app.state.db.Session() as db:
        for sid in ids:
            source=db.get(Source,sid);source.policy={k:v for k,v in source.policy.items() if k!='sec_core'}
        db.commit()
    assert request(client,*ids).status_code==422
