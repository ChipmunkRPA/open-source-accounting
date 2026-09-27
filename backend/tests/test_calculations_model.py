from decimal import Decimal
import pytest
from app.agents.calculations import allocate_revenue, lease_schedule, check_journal
from app.agents.verification import structural_verify
from app.providers.gemini import Gemini
from app.schemas import Plan, Analysis, Context, RunCreate
from app.config import Settings
from app.errors import ProviderError


def test_allocation_cent_reconciliation():
    result=allocate_revenue({'transaction_price':'100','items':[{'name':str(i),'ssp':'1'} for i in range(3)]})
    assert [r['allocated'] for r in result['rows']]==['33.33','33.33','33.34']
    assert result['total']=='100.00'


@pytest.mark.parametrize('value',['NaN','Infinity','-1','nonsense'])
def test_bad_allocation_inputs(value):
    with pytest.raises(ValueError):allocate_revenue({'transaction_price':value,'items':[{'name':'A','ssp':'10'}]})


def test_zero_discount_rate_schedule():
    result=lease_schedule({'monthly_payment':'1000','annual_discount_rate':'0','months':12,'first_payment_date':'2027-01-31'})
    assert result['present_value']=='12000.00'
    assert result['rows'][-1]['closing']=='0.00'
    assert result['rows'][1]['date']=='2027-02-28'
    assert result['rows'][2]['date']=='2027-03-31'


def test_positive_rate_schedule():
    result=lease_schedule({'monthly_payment':'1000','annual_discount_rate':'0.06','months':12,'first_payment_date':'2027-01-31'})
    assert Decimal(result['present_value'])<Decimal('12000')
    assert result['rows'][-1]['closing']=='0.00'


@pytest.mark.parametrize('months',[0,601,1.5,True])
def test_invalid_periods(months):
    with pytest.raises(ValueError):lease_schedule({'monthly_payment':1000,'annual_discount_rate':0.05,'months':months,'first_payment_date':'2027-01-01'})


def test_journal_balancing():
    assert check_journal([{'debit':'10'},{'credit':'10'}])['balanced']
    assert not check_journal([{'debit':'10'},{'credit':'9'}])['balanced']
    with pytest.raises(ValueError):check_journal([{'debit':'10','credit':'10'},{}])


def test_gemini_model_route_and_structured_schema():
    seen={}
    def transport(url,body):
        seen.update(url=url,body=body)
        return {'candidates':[{'finishReason':'STOP','content':{'parts':[{'thought':True,'text':'private'},{'text':'{"issues":[],"missing_questions":[],"proposed_queries":[],"scope":"test"}'}]}}],
                'usageMetadata':{'promptTokenCount':4,'candidatesTokenCount':3,'totalTokenCount':7}}
    config=Settings(model_provider='google_cloud',google_cloud_project='test-project',model_location='us',_env_file=None)
    model=Gemini(config,transport)
    result=model.structured(Plan,'Instruction',{'question':'Example'})
    assert result.scope=='test'
    assert 'gemini-3.8-flash:generateContent' in seen['url']
    assert '/locations/us/' in seen['url']
    assert 'responseJsonSchema' in seen['body']['generationConfig']
    assert 'tools' not in seen['body']
    assert 'temperature' not in seen['body']['generationConfig']
    assert model.last_usage['totalTokenCount']==7


def test_provider_failure_has_no_fallback_or_secret_leak():
    config=Settings(model_provider='google_cloud',google_cloud_project='project',_env_file=None)
    def fail_transport(*args):raise RuntimeError('SECRET PROMPT')
    with pytest.raises(ProviderError,match='MODEL_REQUEST_FAILED') as err:
        Gemini(config,fail_transport).structured(Plan,'x',{})
    assert 'SECRET' not in str(err.value)


def test_incomplete_provider_output_rejected():
    config=Settings(model_provider='google_cloud',google_cloud_project='project',_env_file=None)
    def transport(*args):return {'candidates':[{'finishReason':'MAX_TOKENS','content':{'parts':[{'text':'partial'}]}}]}
    with pytest.raises(ProviderError,match='INCOMPLETE'):Gemini(config,transport).structured(Plan,'x',{})


def test_bad_dates_and_duplicate_document_ids_rejected():
    with pytest.raises(ValueError):Context(period_start='2027-01-01',period_end='2026-12-31')
    with pytest.raises(ValueError):RunCreate(workspace_id='x',question='A valid long question',document_ids=['x','x'])


def test_fake_citation_is_blocked():
    analysis=Analysis(title='Example',summary='Example',sections=[{'heading':'Issue','body':'Draft','claim_ids':['a']}],
       claims=[{'id':'a','text':'Unsupported','basis':'source','evidence_ids':['invented']}],limitations=['Draft'])
    findings=structural_verify(analysis,[])
    assert any(x['severity']=='block' for x in findings)


def test_reference_only_cannot_support_primary_claim():
    analysis=Analysis(title='Example',summary='Example',sections=[{'heading':'Issue','body':'Draft','claim_ids':['a']}],
       claims=[{'id':'a','text':'Unsupported','basis':'source','evidence_ids':['e1']}],limitations=['Draft'])
    findings=structural_verify(analysis,[{'id':'e1','access':'reference_only'}])
    assert any(x['severity']=='block' for x in findings)


def test_production_configuration_rejects_demo():
    with pytest.raises(ValueError):Settings(app_env='production',_env_file=None)


def test_price_cannot_be_overridden():
    with pytest.raises(ValueError):Settings(annual_price_cents=999,_env_file=None)
