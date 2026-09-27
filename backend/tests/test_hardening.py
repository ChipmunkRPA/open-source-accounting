import uuid
from unittest.mock import patch
from sqlalchemy import select
from fastapi import HTTPException
import pytest
from app.models import User, Subscription, Source, Evidence, Run, Job, Memo, now
from app.services.billing import StripeAPI, reconcile, process_event, checkout
from app.services.entitlements import access
from app.services.source_gateway import validate_sec_url, fetch_sec
from app.worker import tick
from app.services.rights import run_artifact_access
from conftest import complete_run, create_run, activate, key
from test_billing import price, invoice


def cfg(client):
    return client.app.state.settings.model_copy(update={'billing_enabled':True,'billing_terms_approved':True,'stripe_price_id':'price_agent'})


def test_archived_price_keeps_previously_paid_access(client):
    config=cfg(client)
    payload={'id':'sub_agent','customer':'cus_test','status':'active','items':{'data':[{'price':price(active=False)}]},'latest_invoice':invoice()}
    with client.app.state.db.Session() as db:
        u=db.get(User,'demo');u.stripe_customer_id='cus_test';db.flush()
        row=reconcile(db,u,'sub_agent',config,StripeAPI(config,lambda *args:payload));db.flush()
        assert access(row,config)['agent_allowed']


def test_transient_billing_pause_can_recover_without_clearing_risk_revocation(client):
    config=cfg(client)
    payload={'id':'sub_agent','customer':'cus_test','status':'unpaid','items':{'data':[{'price':price()}]},'latest_invoice':invoice()}
    with client.app.state.db.Session() as db:
        u=db.get(User,'demo');u.stripe_customer_id='cus_test';db.flush()
        api=StripeAPI(config,lambda *a:payload)
        row=reconcile(db,u,'sub_agent',config,api);db.flush();assert not access(row,config)['agent_allowed']
        payload['status']='active';reconcile(db,u,'sub_agent',config,api);assert access(row,config)['agent_allowed']
        row.revoked=True;reconcile(db,u,'sub_agent',config,api);assert not access(row,config)['agent_allowed']


def test_current_invoice_refund_revokes_access(client):
    config=cfg(client);activate(client)
    with client.app.state.db.Session() as db:
        db.get(User,'demo').stripe_customer_id='cus_test'
        db.get(Subscription,'demo').last_invoice_id='in_paid';db.commit()
        result=process_event(db,{'id':'evt_refund','type':'charge.refunded','data':{'object':{'id':'ch_test','customer':'cus_test','invoice':'in_paid','refunded':True}}},config)
        assert result['received'];assert not access(db.get(Subscription,'demo'),config)['agent_allowed']


def test_other_invoice_refund_does_not_revoke_current_coverage(client):
    config=cfg(client);activate(client)
    with client.app.state.db.Session() as db:
        db.get(User,'demo').stripe_customer_id='cus_test';db.get(Subscription,'demo').last_invoice_id='in_paid';db.commit()
        process_event(db,{'id':'evt_old','type':'charge.refunded','data':{'object':{'id':'ch_old','customer':'cus_test','invoice':'in_old','refunded':True}}},config)
        assert access(db.get(Subscription,'demo'),config)['agent_allowed']


def test_checkout_never_accepts_client_price_or_grants_access(client):
    config=cfg(client);calls=[]
    def provider(method,path,data,headers):
        calls.append((method,path,data))
        if path.startswith('prices/'):return price()
        if path=='customers':return {'id':'cus_new'}
        if path=='subscriptions':return {'data':[]}
        if path=='checkout/sessions':return {'id':'cs_test','url':'https://checkout.stripe.com/c/test'}
        raise AssertionError(path)
    with client.app.state.db.Session() as db:
        user=db.get(User,'demo');result=checkout(db,user,config,'request-key',StripeAPI(config,provider))
        assert result['session_id']=='cs_test'
        assert calls[-1][2]['line_items[0][price]']=='price_agent'
        assert not access(db.get(Subscription,'demo'),config)['agent_allowed']


@pytest.mark.parametrize('url',['http://www.sec.gov/a','https://dart.deloitte.com/a','https://www.sec.gov.evil.test/a','https://user@www.sec.gov/a','https://www.sec.gov:8443/a'])
def test_source_gateway_rejects_unapproved_routes(url):
    with pytest.raises(ValueError):validate_sec_url(url)


def test_source_gateway_rejects_nonpublic_resolution():
    with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):
        with pytest.raises(ValueError):validate_sec_url('https://www.sec.gov/a')


def test_source_connector_disabled_by_default(client):
    with pytest.raises(HTTPException):fetch_sec('https://www.sec.gov/a',client.app.state.settings)


def test_worker_expired_lease_attempt_cap_releases_allowance(client):
    activate(client);run=create_run(client)
    client.post('/api/v1/runs/'+run['id']+'/start',json={'expected_revision':1,'confirm_scope':True},headers=key())
    with client.app.state.db.Session() as db:
        job=db.scalar(select(Job).where(Job.run_id==run['id']));job.state='running';job.lease_until=now()-1;job.attempts=client.app.state.settings.max_job_attempts;db.commit()
    tick(client.app.state.db,client.app.state.settings)
    assert client.get('/api/v1/runs/'+run['id']).json()['state']=='failed'
    assert client.get('/api/v1/me').json()['usage']['reserved']==0


def test_saved_memo_critique_preserves_recursive_source_restrictions(client):
    run=complete_run(client)
    memo=client.post('/api/v1/runs/'+run['id']+'/memo').json()
    child=complete_run(client,'memo_review',inputs={'memo_id':memo['id']})
    with client.app.state.db.Session() as db:
        evidence=db.scalar(select(Evidence).where(Evidence.run_id==run['id'],Evidence.source_id.is_not(None),Evidence.access!='reference_only'))
        source=db.get(Source,evidence.source_id);source.enabled=False;db.commit()
        with pytest.raises(HTTPException):run_artifact_access(db,db.get(Run,child['id']))


def test_unknown_source_and_admin_paths_are_not_spa_html(client):
    assert client.get('/api/v1/does-not-exist').status_code==404
    assert client.get('/api/v1/sources/not-real').status_code==404
    assert client.get('/api/v1/admin/audit').status_code==403


def test_terminal_sse_has_resume_ids(client):
    run=complete_run(client)
    result=client.get('/api/v1/runs/'+run['id']+'/stream')
    assert result.status_code == 200
    assert 'text/event-stream' in result.headers['content-type']
    assert 'id:' in result.text and 'data:' in result.text
