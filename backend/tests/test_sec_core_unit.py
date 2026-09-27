"""Offline SEC Core tests. Fixtures are synthetic; shipped excerpts are government text."""
import copy
import io
import json
from pathlib import Path
from urllib.error import HTTPError
from types import SimpleNamespace
import pytest
from app.sec_core.core import CorePack, CoreError, official_url, digest, canonical
from app.sec_core import parsers
from app.sec_core.fetch import RateBudget, Gateway, Blocked, acquire

ROOT = Path(__file__).resolve().parents[2] / 'content' / 'sec_core'

@pytest.fixture
def pack():
    return CorePack(ROOT)


def clone(tmp_path):
    for name in ['catalog.json','excerpts.json']:
        (tmp_path/name).write_bytes((ROOT/name).read_bytes())
    return tmp_path


def modify(tmp_path, change):
    root=clone(tmp_path);file=root/'excerpts.json';data=json.loads(file.read_text());change(data)
    file.write_text(json.dumps(data));return root


def test_inventory_honest(pack):
    r=pack.report()
    assert (r['sources_inventoried'],r['sources_with_excerpts'],r['selected_excerpts'])==(34,7,28)
    assert r['agent_approved']==r['professional_reviewed']==r['complete_source_documents']==0
    assert r['original_http_artifacts']==0
    assert sum(x['excerpts'] for x in r['families'])==28


def test_exact_public_excerpt(pack):
    p=pack.passage('cfi-100-04')
    assert 'CFI Non-GAAP 100.04'==p['locator']
    assert p['published_or_revised_at']=='2022-12-13'
    assert p['authority_type']=='staff_guidance'
    assert p['agent_approved'] is False
    assert 'accelerate revenue' in p['text']
    assert p['snapshot_id'] and p['sha256']


def test_preview_sanitizes_fts(pack):
    assert pack.preview('" OR * NOT foo; --') is not None
    assert any(x['id']=='cfi-100-04' for x in pack.preview('accelerate revenue',100))
    assert pack.preview('')==[]
    assert pack.preview('bookkeepingunfindableword')==[]
    assert all(x['source_id']=='ecfr-sk10' for x in pack.preview('prominence',100,'reg_sk'))


@pytest.mark.parametrize('url',[
 'http://www.sec.gov/x','https://www.sec.gov.evil.test/a','https://www.sec.gov@evil.test/',
 'https://www.sec.gov:444/a','https://127.0.0.1/a','file:///etc/passwd',
 'https://www.sec.gov/\r\nX:1','https://www.sec.gov\\@evil.test/'])
def test_url_rejects(url):
    with pytest.raises(CoreError):official_url(url)


@pytest.mark.parametrize('change',[
 lambda b:b['documents'][0]['passages'][0].update(text='tampered'),
 lambda b:b['documents'][0].update(raw_artifact_included=True),
 lambda b:b['documents'][0].update(professional_review='approved'),
 lambda b:b['documents'][0].update(source_as_of='2025-01-01'),
 lambda b:b['documents'][0].update(url='https://www.sec.gov/other'),
 lambda b:b['documents'][0]['passages'][0].update(locator=''),
 lambda b:b['documents'].append(copy.deepcopy(b['documents'][0])),
 lambda b:b['documents'][0].update(retrieved_at='2026-09-27T12:00:00'),
])
def test_tampering_and_false_claims_rejected(tmp_path,change):
    with pytest.raises((CoreError,ValueError)):CorePack(modify(tmp_path,change))


def test_symlink_rejected(tmp_path):
    clone(tmp_path);(tmp_path/'catalog.json').unlink();(tmp_path/'catalog.json').symlink_to(ROOT/'catalog.json')
    with pytest.raises(CoreError):CorePack(tmp_path)


XML=b'''<ECFR><DIV8 TYPE="SECTION" N="229.999"><HEAD>Fixture only</HEAD><P ID="p-a">(a) General <I>synthetic</I> rule.</P><P>(1) A child.</P><TABLE><TR><TH>Year</TH><TH>Value</TH></TR><TR><TD>20XX</TD><TD>123</TD></TR></TABLE><FTNT><P>1 Synthetic note.</P></FTNT></DIV8></ECFR>'''

def test_ecfr_structure():
    out=parsers.ecfr_xml(XML)
    assert len(out)==4
    assert out[0]['anchor']=='p-a' and out[0]['locator']=='17 CFR 229.999 — source block 1'
    assert '(a) General synthetic rule.'==out[0]['text']
    assert 'Year | Value\n20XX | 123'==out[2]['text']
    assert out[3]['kind']=='footnote'


@pytest.mark.parametrize('raw',[b'<!DOCTYPE x [<!ENTITY a "boom">]><x/>',b'<x/>',b'<bad',b'<SECTION><P>x</P></SECTION>'])
def test_xml_fail_closed(raw):
    with pytest.raises(CoreError):parsers.ecfr_xml(raw)


def test_cfi_grouping_suffix_and_hidden_content():
    raw=b'''<html><nav>Do not include</nav><main><h2>Section 102</h2><p>Question 102.10(a): Synthetic question?</p><p>Answer: First.<script>DROP TABLE</script></p><ul><li>Relevant bullet</li></ul><p>Question 102.10(b)</p><p>Question: Another?</p><p>Answer: Next.</p></main></html>'''
    out=parsers.html(raw,'cfi','Fixture')
    assert [p['locator'] for p in out if p['kind']=='question_and_answer']==['CFI 102.10(a)','CFI 102.10(b)']
    text='\n'.join(p['text'] for p in out)
    assert 'DROP TABLE' not in text and 'Do not include' not in text
    assert 'Relevant bullet' in out[1]['text']


def test_html_table_preserved():
    raw=b'<main><h3>1230.4 Synthetic</h3><table><tr><th>Column</th></tr><tr><td>Value</td></tr></table></main>'
    out=parsers.html(raw,'frm','Fixture')
    assert out[1]['kind']=='table_linearized' and out[1]['text']=='Column\nValue'
    assert out[1]['locator'].startswith('FRM 1230.4')


def test_no_whole_site_fallback():
    with pytest.raises(CoreError):parsers.html(b'<body><nav>Only navigation</nav></body>','sab','Fixture')


class Response(io.BytesIO):
    def __init__(self,data,mime='application/xml'):
        super().__init__(data);self.headers={'Content-Type':mime};self.status=200
class Opener:
    def __init__(self,sequence):self.sequence=list(sequence);self.urls=[]
    def open(self,req,timeout):
        self.urls.append(req.full_url)
        result=self.sequence.pop(0)
        if isinstance(result,Exception):raise result
        return result
class Budget:
    def __init__(self):self.calls=0
    def reserve(self):self.calls+=1


def gateway(opener,budget=None):
    return Gateway('SyntheticTest/1 maintainer@example.test',budget or Budget(),opener,lambda u:None)


@pytest.mark.parametrize('code',[401,403,429])
def test_stop_on_access_block(code):
    o=Opener([HTTPError('https://www.sec.gov/a',code,'blocked',{},None)])
    with pytest.raises(Blocked):gateway(o).get('https://www.sec.gov/a')
    assert len(o.urls)==1


def test_block_page_is_not_content():
    with pytest.raises(Blocked):gateway(Opener([Response(b'<title>Request Access</title>','text/html')])).get('https://www.sec.gov/a')


def test_redirect_target_revalidated():
    o=Opener([HTTPError('https://www.sec.gov/a',302,'redirect',{'Location':'http://127.0.0.1/'},None)])
    with pytest.raises(CoreError):gateway(o).get('https://www.sec.gov/a')
    assert len(o.urls)==1


def test_per_redirect_rate_reservation():
    b=Budget();o=Opener([HTTPError('https://www.sec.gov/a',302,'redirect',{'Location':'/b'},None),Response(XML)])
    r=gateway(o,b).get('https://www.sec.gov/a')
    assert b.calls==2 and r['resolved_url']=='https://www.sec.gov/b'


def test_acquisition_snapshot_idempotent(tmp_path):
    e=dict(id='test-source',url='https://www.sec.gov/a',family='reg_sk',title='Fixture',authority_type='commission_rule',parser='ecfr_xml')
    one=acquire(e,gateway(Opener([Response(XML)])),tmp_path)
    two=acquire(e,gateway(Opener([Response(XML)])),tmp_path)
    assert one['status']=='staged_no_approval' and two['status']=='already_staged'
    assert one['raw_sha256']==digest(XML)
    assert one['effective_from'] is None and one['public_available_at'] is None
    assert len(list((tmp_path/'raw').iterdir()))==1 and len(list((tmp_path/'snapshots').iterdir()))==1


def test_missing_ecfr_date_fails_before_network(tmp_path):
    e=dict(acquisition_url='https://www.ecfr.gov/api/{as_of}')
    with pytest.raises(CoreError):acquire(e,gateway(Opener([])),tmp_path)


def test_shared_local_rate_slots(tmp_path):
    clock=lambda:1000.0;slept=[]
    a=RateBudget(str(tmp_path/'budget.db'),rate=4,clock=clock,sleeper=slept.append)
    b=RateBudget(str(tmp_path/'budget.db'),rate=4,clock=clock,sleeper=slept.append)
    assert [a.reserve(),b.reserve(),a.reserve()]==[1000,1000.25,1000.5]
    assert slept==[0,0.25,0.5]


def test_cloud_refuses_local_budget(tmp_path,monkeypatch):
    monkeypatch.setenv('K_SERVICE','fixture')
    with pytest.raises(CoreError):RateBudget(str(tmp_path/'bad.db'))


def test_bad_rate_and_operator():
    with pytest.raises(CoreError):RateBudget('unused',rate=11)
    with pytest.raises(CoreError):Gateway('anonymous',Budget())


def test_downloaded_snapshot_reparse(tmp_path,pack):
    from app.sec_core.integration import snapshot_pack
    entry=pack.entries['ecfr-part-229']
    r=acquire(entry,gateway(Opener([Response(XML)])),tmp_path,'2026-09-24')
    path=next((tmp_path/'snapshots').iterdir())
    loaded=snapshot_pack(path,tmp_path/'raw',pack)
    assert len(loaded.passages)==4
    first=next(iter(loaded.passages.values()))
    assert first[0]['acquisition_method']=='direct_http' and first[0]['raw_artifact_included']
    bad=json.loads(path.read_text());bad['passages'][0]['text']='tampered';path.write_text(json.dumps(bad))
    with pytest.raises(CoreError):snapshot_pack(path,tmp_path/'raw',pack)


def test_downloaded_raw_hash_checked(tmp_path,pack):
    from app.sec_core.integration import snapshot_pack
    acquire(pack.entries['ecfr-part-229'],gateway(Opener([Response(XML)])),tmp_path,'2026-09-24')
    path=next((tmp_path/'snapshots').iterdir());next((tmp_path/'raw').iterdir()).write_bytes(b'bad')
    with pytest.raises(CoreError):snapshot_pack(path,tmp_path/'raw',pack)
