from conftest import rights_approval
"""Original content validation, staging, editorial separation, and public API tests."""
import hashlib
import json
import shutil
from decimal import Decimal, getcontext
from pathlib import Path
import pytest
from app.content import Library, ContentError, stage_library
from app.models import Source, Run
from app.services.rights import allowed
from app.services.retrieval import search

ROOT = Path(__file__).resolve().parents[2] / 'content'

@pytest.fixture
def pack():
    return Library(ROOT)

@pytest.fixture
def copy_pack(tmp_path):
    target = tmp_path/'content'
    shutil.copytree(ROOT, target)
    return target


def test_pack_counts_and_draft_status(pack):
    assert pack.report()['items'] == 63
    assert len(pack.references) == 26
    assert all(not i.agent_eligible_by_default for i in pack.items.values())
    assert all(i.technical_review.status == 'unreviewed' for i in pack.items.values())
    assert pack.report()['words'] > 16000


def test_all_articles_have_provenance(pack):
    for item in pack.items.values():
        text = pack.bodies[item.id]
        assert 'AI-assisted editorial draft' in text
        assert 'Sources and verification' in text
        assert 'CC BY 4.0' in text
        assert all(r in pack.references for r in item.source_ids)
        assert item.sha256 == hashlib.sha256(text.encode()).hexdigest()


def mutate(path, fn):
    data = json.loads((path/'manifest.json').read_text())
    fn(data)
    (path/'manifest.json').write_text(json.dumps(data))

@pytest.mark.parametrize('case', ['absolute','parent','symlink','hash','missing','duplicate','source','license','review','extra'])
def test_reject_invalid_pack(copy_pack, case, tmp_path):
    if case=='absolute':mutate(copy_pack, lambda d:d['items'][0].update(path='/etc/passwd'))
    elif case=='parent':mutate(copy_pack, lambda d:d['items'][0].update(path='../hidden.md'))
    elif case=='symlink':
        p=copy_pack/'guides/authority-and-period.md';body=p.read_bytes();p.unlink();outside=tmp_path/'outside.md';outside.write_bytes(body);p.symlink_to(outside)
    elif case=='hash':(copy_pack/'guides/authority-and-period.md').write_text('tampered')
    elif case=='missing':(copy_pack/'guides/authority-and-period.md').unlink()
    elif case=='duplicate':mutate(copy_pack, lambda d:d['items'].append(d['items'][0]))
    elif case=='source':mutate(copy_pack, lambda d:d['items'][0].update(source_ids=['invented']))
    elif case=='license':mutate(copy_pack, lambda d:d['items'][0].update(license='unknown'))
    elif case=='review':mutate(copy_pack, lambda d:d['items'][0].update(technical_review={'status':'reviewed'}))
    else:mutate(copy_pack, lambda d:d['items'][0].update(secret_extra='unexpected'))
    with pytest.raises((ContentError,ValueError,OSError)):Library(copy_pack)

@pytest.mark.parametrize('url',['http://example.test','javascript:alert(1)','https://'+'user:'+ 'secret@'+'example.test'], ids=['http','script','userinfo'])
def test_reject_unsafe_reference_url(copy_pack,url):
    p=copy_pack/'references/sources.json';data=json.loads(p.read_text());data['sources'][0]['url']=url;p.write_text(json.dumps(data))
    with pytest.raises(ContentError):Library(copy_pack)


def test_remote_acquisition_not_enabled(copy_pack):
    p=copy_pack/'references/sources.json';data=json.loads(p.read_text());data['sources'][0]['automated_fetch_enabled']=True;p.write_text(json.dumps(data))
    with pytest.raises(ContentError):Library(copy_pack)


def test_public_library_no_subscription(client):
    result=client.get('/api/v1/library').json()
    assert result['total']==63
    assert len(result['items'])==24
    assert 'body' not in result['items'][0]
    assert client.get('/api/v1/library/lease-measurement').status_code==200
    assert client.get('/api/v1/library/does-not-exist').status_code==404
    assert client.get('/api/v1/me').json()['access']['agent_allowed'] is False


def test_public_library_without_auth_dependency(client):
    response=client.get('/api/v1/library',headers={'X-Dev-User':'unknown-person'})
    assert response.status_code==200


def test_filter_pagination_and_query(client):
    assert client.get('/api/v1/library?kind=case').json()['total']==8
    assert client.get('/api/v1/library?kind=playbook').json()['total']==16
    rows=client.get('/api/v1/library?q=26%2C730&kind=case').json()
    assert any(i['id']=='case-lease-present-value' for i in rows['items'])
    assert len(client.get('/api/v1/library?offset=24').json()['items'])==24
    assert client.get('/api/v1/library?topic=no-such-topic').json()['items']==[]

@pytest.mark.parametrize('params',['limit=101','limit=0','offset=-1','q='+('x'*201)])
def test_query_bounds(client,params):
    assert client.get('/api/v1/library?'+params).status_code==422


def test_failed_integrity_returns_safe_503(client,tmp_path):
    client.app.state.settings.content_dir=str(tmp_path/'missing')
    response=client.get('/api/v1/library')
    assert response.status_code==503
    assert str(tmp_path) not in response.text


def stage(client,pack):
    with client.app.state.db.Session() as db:
        result=stage_library(db,pack,'admin');db.commit();return result


def test_staging_idempotent_and_no_approval(client,pack):
    a=stage(client,pack);b=stage(client,pack)
    assert len(a['created'])==63 and len(b['existing'])==63 and not b['created']
    with client.app.state.db.Session() as db:
        for sid in a['created']:
            source=db.get(Source,sid)
            assert not source.reviewed and not allowed(source,'model_input')
        run=Run(context={'framework':'BOTH'},document_ids=[])
        assert not set(a['created']) & {r['source_id'] for r in search(db,run,'implementation',100)}


def test_non_admin_cannot_stage(client,pack):
    with client.app.state.db.Session() as db:
        with pytest.raises(ContentError):stage_library(db,pack,'demo')


def decision(s,**changes):
    from app.services.editorial import revision
    from app.models import now
    data={'expected_policy_version':s.policy_version,'expected_review_revision':revision(s),
          'review_scope':'Synthetic technical scope only', 'evidence_ref':'ev_synthetic_technical',
          'evidence_sha256':'a'*64, 'expires_at':now()+3600, 'content_sha256':s.policy['content_sha256'],
          'decision':'approved','review_note':'TEST FIXTURE ONLY: simulated review for permissions tests, not an accounting review.',
          'checked_reference_ids':s.policy['content_reference_ids'],'confirm_actual_review_performed':True}
    data.update(changes);return data


def source_and_payload(client,pack):
    sid=stage(client,pack)['created'][0]
    with client.app.state.db.Session() as db:return sid,decision(db.get(Source,sid))


def test_both_approval_gates_and_exact_hash(client,pack):
    sid,payload=source_and_payload(client,pack)
    assert client.post(f'/api/v1/editorial/sources/{sid}/review',headers={'X-Dev-User':'editor'},json=payload).status_code==409
    assert client.post(f'/api/v1/admin/sources/{sid}/approve',json=rights_approval(client,sid),headers={'X-Dev-User':'approver'}).status_code==200
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid)
        assert allowed(source,'display_full') and not allowed(source,'model_input')
        payload = decision(source)
    r=client.post(f'/api/v1/editorial/sources/{sid}/review',headers={'X-Dev-User':'editor'},json=payload)
    assert r.status_code==200,r.text
    assert r.json()['editorial_status']=='approved'
    with client.app.state.db.Session() as db:
        source=db.get(Source,sid)
        assert allowed(source,'model_input') and not allowed(source,'train')
        source.text+='\nA changed statement.'
        assert not allowed(source,'model_input')

@pytest.mark.parametrize('principal',['demo','admin','approver'])
def test_technical_review_separate_role(client,pack,principal):
    sid,payload=source_and_payload(client,pack)
    assert client.post(f'/api/v1/editorial/sources/{sid}/review',headers={'X-Dev-User':principal},json=payload).status_code==403


def test_technical_reviewer_cannot_grant_rights(client,pack):
    sid,_=source_and_payload(client,pack)
    assert client.post(f'/api/v1/admin/sources/{sid}/approve',json=rights_approval(client,sid),headers={'X-Dev-User':'editor'}).status_code==403

@pytest.mark.parametrize('change,expected',[({'content_sha256':'0'*64},409),({'expected_policy_version':999},409),({'checked_reference_ids':['invented']},422),({'checked_reference_ids':['fasb-asc']},422),({'confirm_actual_review_performed':False},422)])
def test_review_validation(client,pack,change,expected):
    sid,payload=source_and_payload(client,pack)
    client.post(f'/api/v1/admin/sources/{sid}/approve',json=rights_approval(client,sid),headers={'X-Dev-User':'approver'})
    with client.app.state.db.Session() as db:
        payload = decision(db.get(Source, sid))
    payload.update(change)
    assert client.post(f'/api/v1/editorial/sources/{sid}/review',headers={'X-Dev-User':'editor'},json=payload).status_code==expected


def test_source_changes_require_new_library_version(client,pack):
    stage(client,pack)
    first=next(iter(pack.items.values()))
    first.sha256='0'*64
    with client.app.state.db.Session() as db:
        with pytest.raises(ContentError):stage_library(db,pack,'admin')


def test_qa_references_and_related_articles(pack):
    questions=json.loads((ROOT/'qa/questions.json').read_text())['questions']
    assert len(questions)==58 and len({q['id'] for q in questions})==58
    for q in questions:
        assert q['related_item_id'] in pack.items
        assert all(r in pack.references for r in q['source_ids'])
        assert q['review_status']=='unreviewed'


def test_stipulated_arithmetic_only():
    getcontext().prec=36
    price=Decimal('90000');assert price*Decimal('.8')==72000
    rate=Decimal('.06');payment=Decimal(10000)
    pv=sum(payment/(1+rate)**t for t in range(1,4))
    assert pv.quantize(Decimal('.01'))==Decimal('26730.12')
    balance=pv
    for _ in range(3):balance=balance*(1+rate)-payment
    assert abs(balance)<Decimal('0.0000000001')
    assert Decimal(12000)*3==36000
