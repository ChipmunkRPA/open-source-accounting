import hashlib
import hmac
import json
from datetime import datetime, timezone
import pytest
from fastapi import HTTPException
from app.config import Settings
from app.models import Subscription, User, now
from app.services.entitlements import access, cycle
from app.services.billing import verify_signature, validate_price, paid_period, reconcile, process_event, StripeAPI
from conftest import activate


def price(**changes):
    return {'id':'price_agent','active':True,'unit_amount':8999,'currency':'usd','recurring':{'interval':'year','interval_count':1,'usage_type':'licensed'},**changes}


def invoice(start=None):
    start=start or now()
    return {'id':'in_paid','status':'paid','amount_paid':8999,'currency':'usd','subscription':'sub_agent',
            'lines':{'data':[{'price':{'id':'price_agent'},'quantity':1,'amount':8999,
                              'period':{'start':start,'end':start+365*86400}}], 'has_more':False}}


def test_valid_webhook_and_replay_window():
    body=json.dumps({'id':'evt_1','type':'invoice.paid','data':{'object':{}}}).encode();stamp=1000;secret='test-secret'
    signature=hmac.new(secret.encode(),b'1000.'+body,hashlib.sha256).hexdigest()
    assert verify_signature(body,f't=1000,v1={signature}',secret,timestamp=stamp)['id']=='evt_1'
    with pytest.raises(HTTPException):verify_signature(body,f't=1000,v1={signature}',secret,timestamp=2000)
    with pytest.raises(HTTPException):verify_signature(body+b' ',f't=1000,v1={signature}',secret,timestamp=stamp)


@pytest.mark.parametrize('changes',[{'unit_amount':8998},{'currency':'eur'},{'active':False},
                                  {'recurring':{'interval':'month','interval_count':1}}, {'id':'other'}])
def test_wrong_price_rejected(changes):
    with pytest.raises(HTTPException):validate_price(price(**changes),'price_agent')


def test_valid_price():validate_price(price(),'price_agent')


def test_paid_invoice_required_and_canonical_new_shape():
    inv=invoice();assert paid_period(inv,'sub_agent','price_agent')
    inv['status']='open';assert paid_period(inv,'sub_agent','price_agent') is None
    inv=invoice();inv['parent']={'subscription_details':{'subscription':inv.pop('subscription')}}
    line=inv['lines']['data'][0];line['pricing']={'price_details':{'price':line.pop('price')['id']}}
    assert paid_period(inv,'sub_agent','price_agent')
    inv['amount_paid']=0;assert paid_period(inv,'sub_agent','price_agent') is None


def test_active_status_alone_does_not_grant_access(client):
    cfg=client.app.state.settings.model_copy(update={'billing_enabled':True,'stripe_price_id':'price_agent'})
    with client.app.state.db.Session() as db:
        user=db.get(User,'demo');user.stripe_customer_id='cus_test';db.commit()
        def transport(method,path,data,headers):
            return {'id':'sub_agent','customer':'cus_test','status':'active','items':{'data':[{'price':price(),'quantity':1}]},'latest_invoice':{**invoice(),'status':'open'},'cancel_at_period_end':False}
        record=reconcile(db,user,'sub_agent',cfg,StripeAPI(cfg,transport))
        db.flush()
        assert record.paid_until==0 and not access(record,cfg)['agent_allowed']


def test_paid_reconciliation_and_duplicate_webhook(client):
    cfg=client.app.state.settings.model_copy(update={'billing_enabled':True,'stripe_price_id':'price_agent'})
    def transport(method,path,data,headers):
        return {'id':'sub_agent','customer':'cus_test','status':'active','items':{'data':[{'price':price(),'quantity':1}]},'latest_invoice':invoice(),'cancel_at_period_end':True}
    stripe=StripeAPI(cfg,transport)
    with client.app.state.db.Session() as db:
        user=db.get(User,'demo');user.stripe_customer_id='cus_test';db.commit()
        event={'id':'evt_1','type':'invoice.paid','data':{'object':{'id':'in_paid','customer':'cus_test','subscription':'sub_agent'}}}
        first=process_event(db,event,cfg,stripe);second=process_event(db,event,cfg,stripe)
        assert not first['duplicate'] and second['duplicate']
        sub=db.get(Subscription,'demo');assert access(sub,cfg)['state']=='ENDING'


def test_cancel_preserves_term_and_expiry_blocks_new_work(client):
    activate(client)
    original=client.get('/api/v1/me').json()['access']['access_until']
    assert client.post('/api/v1/billing/cancel-renewal').json()['state']=='ENDING'
    assert client.get('/api/v1/me').json()['access']['access_until']==original
    assert client.post('/api/v1/billing/resume-renewal').json()['state']=='ACTIVE'
    client.post('/api/v1/dev/subscription',json={'state':'expired'})
    assert not client.get('/api/v1/me').json()['access']['agent_allowed']


def test_grace_is_fixed_not_refreshed_by_event_arrival():
    cfg=Settings(renewal_grace_days=7,_env_file=None)
    sub=Subscription(user_id='u',term_start=1,paid_until=1000,status='past_due',renewal_failed=True,cancel_at_period_end=False,revoked=False)
    assert access(sub,cfg,timestamp=1001)['access_until']==1000+7*86400
    assert not access(sub,cfg,timestamp=1000+8*86400)['agent_allowed']
    sub.cancel_at_period_end=True
    assert not access(sub,cfg,timestamp=1001)['agent_allowed']


def test_month_end_usage_cycle_does_not_drift():
    def stamp(s):return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())
    sub=Subscription(user_id='u',term_start=stamp('2027-01-31'),paid_until=stamp('2028-01-31'))
    start,end=cycle(sub,stamp('2027-03-01'))
    assert start==stamp('2027-02-28') and end==stamp('2027-03-31')


def test_checkout_disabled_in_unapproved_deployment(client):
    r=client.post('/api/v1/billing/checkout',json={'accepted_annual_terms':True},headers={'Idempotency-Key':'checkout-test'})
    assert r.status_code==503


def test_unsigned_webhook_never_updates_subscription(client):
    r=client.post('/api/v1/billing/webhook',json={'status':'active'})
    assert r.status_code==503
    assert client.get('/api/v1/me').json()['access']['state']=='FREE'
