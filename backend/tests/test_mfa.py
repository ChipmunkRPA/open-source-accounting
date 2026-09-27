import copy
import time
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app import auth as module
from app.config import Settings
from app.main import create_app
from app.models import User


def config(**kw):
    return Settings(auth_mode='firebase',firebase_project_id='osa-project',app_env='test',_env_file=None,**kw)


def claims(**kw):
    value={'uid':'real-user','sub':'real-user','aud':'osa-project',
      'iss':'https://securetoken.google.com/osa-project','email':'example@example.test',
      'email_verified':True,'auth_time':int(time.time()),
      'firebase':{'sign_in_provider':'password','sign_in_second_factor':'totp','second_factor_identifier':'factor-1'}}
    value.update(kw);return value

@pytest.mark.parametrize('factor',['totp','phone'])
def test_reserved_mfa_claims(factor):
    c=claims();c['firebase']['sign_in_second_factor']=factor
    assert module.identity_from_claims(c,config()).mfa_verified

@pytest.mark.parametrize('meta',[{'sign_in_provider':'password'},
 {'sign_in_provider':'password','sign_in_second_factor':'totp'},
 {'sign_in_provider':'password','sign_in_second_factor':'email','second_factor_identifier':'f'},
 {'sign_in_provider':'password','sign_in_second_factor':'totp','second_factor_identifier':''}])
def test_enrollment_or_custom_flag_is_not_mfa(meta):
    assert not module.identity_from_claims(claims(firebase=meta,mfa=True,enrolled=True),config()).mfa_verified

@pytest.mark.parametrize('change',[{'aud':'another'},{'iss':'bad'},{'sub':'other'},{'uid':''},
 {'uid':True},{'uid':'x'*129},{'auth_time':False},{'auth_time':float('nan')},{'auth_time':float('inf')},
 {'auth_time':-1},{'auth_time':time.time()+1000},{'auth_time':time.time()-50000},
 {'firebase':{}},{'firebase':{'sign_in_provider':'phone'}},{'firebase':{'sign_in_provider':'anonymous'}},
 {'firebase':{'sign_in_provider':'custom'}},{'firebase':{'sign_in_provider':'password','tenant':'foreign'}}])
def test_bad_identity_denied(change):
    with pytest.raises(HTTPException):module.identity_from_claims(claims(**change),config())

@pytest.mark.parametrize('change',[{'mfa_required':False},{'auth_recent_seconds':5},{'auth_session_max_age_seconds':90000},{'firebase_auth_domain':'https://invalid/' }])
def test_invalid_configuration_denied(change):
    with pytest.raises(ValueError):config(**change)


def test_emulator_denied(monkeypatch):
    monkeypatch.setenv('FIREBASE_AUTH_EMULATOR_HOST','localhost:9099')
    with pytest.raises(ValueError):config()


@pytest.fixture
def secured(tmp_path,monkeypatch):
    c=config(database_url=f'sqlite:///{tmp_path}/app.db',data_dir=str(tmp_path))
    token=claims()
    monkeypatch.setattr(module,'verify_firebase_token',lambda *a:copy.deepcopy(token))
    with TestClient(create_app(c)) as client:yield client,token


def bearer():return {'Authorization':'Bearer verified-by-mocked-sdk'}


def test_first_factor_status_without_provisioning(secured):
    client,c=secured;c['firebase']={'sign_in_provider':'password'}
    assert client.get('/api/v1/auth/status',headers=bearer()).json()['next_step']=='enroll_or_challenge'
    for path in ['/me','chats','workspaces','notifications','memos']:
        response=client.get('/api/v1/'+path.lstrip('/'),headers=bearer())
        assert response.status_code==403,response.text
        assert response.json()['error']['code']=='MFA_REQUIRED'
    with client.app.state.db.Session() as db:assert db.get(User,'real-user') is None
    assert client.get('/api/v1/library').status_code==200


def test_mfa_user_provision_and_no_paid_bypass(secured):
    client,_=secured;r=client.get('/api/v1/me',headers=bearer())
    assert r.status_code==200,r.text
    assert r.json()['security']['mfa_verified'] is True
    assert r.json()['access']['agent_allowed'] is False


def test_email_required(secured):
    client,c=secured;c['email_verified']=False
    assert client.get('/api/v1/auth/status',headers=bearer()).json()['next_step']=='verify_email'
    assert client.get('/api/v1/me',headers=bearer()).json()['error']['code']=='VERIFY_EMAIL'


def test_no_header_auth_bypass(secured):
    client,_=secured
    assert client.get('/api/v1/me',headers={'X-Dev-User':'admin'}).status_code==401


def test_recent_auth_on_sensitive_change(secured):
    client,c=secured;c['auth_time']=int(time.time())-600
    assert client.get('/api/v1/me',headers=bearer()).status_code==200
    r=client.post('/api/v1/billing/portal',headers=bearer())
    assert r.status_code==403 and r.json()['error']['code']=='RECENT_AUTH_REQUIRED'


def test_sdk_revocation_failure_is_redacted(secured,monkeypatch):
    client,_=secured
    def fail(*args):raise ValueError('sensitive token-body')
    monkeypatch.setattr(module,'verify_firebase_token',fail)
    r=client.get('/api/v1/me',headers=bearer());assert r.status_code==401 and 'sensitive' not in r.text


def test_config_and_csp(secured):
    client,_=secured;r=client.get('/api/v1/config')
    assert r.json()['mfa_required'] and r.json()['mfa_methods']==['totp','phone']
    assert 'stripe_secret' not in r.text
    csp=r.headers['Content-Security-Policy']
    assert "object-src 'none'" in csp and 'https://www.google.com/recaptcha/' in csp
    assert "script-src *" not in csp and 'unsafe-eval' not in csp
