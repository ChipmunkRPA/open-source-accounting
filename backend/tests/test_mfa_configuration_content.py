import importlib.util
from pathlib import Path
from decimal import Decimal
import pytest
ROOT=Path(__file__).resolve().parents[2]

def load(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

@pytest.mark.parametrize('domains,regions,adjacent',[([],['US'],1),(['https://bad.test'],['US'],1),(['*.test'],['US'],1),(['app.test'],[],1),(['app.test'],['USA'],1),(['app.test'],['US'],3)])
def test_invalid_cloud_plan_rejected(domains,regions,adjacent):
    with pytest.raises(ValueError):load('config','configure_identity_platform.py').plan({},domains,regions,adjacent)

def test_mfa_configuration_preserves_scope():
    m=load('config','configure_identity_platform.py')
    old={'authorizedDomains':['existing.test'],'mfa':{'state':'MANDATORY','enabledProviders':['PHONE_SMS'],'providerConfigs':[{'state':'ENABLED','otherProvider':{}}]}}
    result=m.plan(old,['app.test'],['US'])
    assert result['authorizedDomains']==['app.test','existing.test']
    assert result['mfa']['state']=='MANDATORY'
    assert old['authorizedDomains']==['existing.test']
    assert result['mfa']['providerConfigs'][0]['otherProvider']=={}
    m.verify(result,result)
    assert 'signIn.email.enabled' in m.MASK

def test_cloud_config_missing_factor_rejected():
    m=load('config','configure_identity_platform.py');r=m.plan({},['app.test'],['US'])
    with pytest.raises(RuntimeError):m.verify({'mfa':{'state':'DISABLED'}},r)

def test_progress_inventory_is_current():
    m=load('inventory','content_progress.py');assert m.render(ROOT) in (ROOT/'progress.md').read_text()

def test_cash_flow_case_arithmetic():
    assert 400000+120000+100000-30000==590000
    assert -120000+25000==-95000

def test_fx_case_units_and_arithmetic():
    initial=Decimal('100000')*Decimal('1.10');closing=Decimal('100000')*Decimal('1.12')
    assert closing-initial==Decimal('2000')

def test_liquidity_case_timing():
    path=[800000-150000*m for m in range(1,7)]
    assert path==[650000,500000,350000,200000,50000,-100000]
    assert path[-1]+500000==400000


def test_cloud_run_cannot_boot_demo(monkeypatch):
    from app.config import Settings
    monkeypatch.setenv('K_SERVICE','example-service')
    with pytest.raises(ValueError):Settings(app_env='local',_env_file=None)
