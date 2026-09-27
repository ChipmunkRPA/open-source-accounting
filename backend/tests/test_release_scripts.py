import json
import sys
from pathlib import Path
from subprocess import CompletedProcess
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from release_preflight import collect
import publish_github as publish

@pytest.mark.parametrize('filename',['.env','backend/.env','data/client.db','.git/config','node_modules/lib/index.js','private.key'])
def test_excludes_sensitive_paths(tmp_path,filename):
    p=tmp_path/filename;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('not published')
    report=collect(tmp_path)
    assert not any(f['path']==filename for f in report['files']) or bool(report['findings'])


def test_detects_key_without_echoing_it(tmp_path):
    secret='sk_'+'live_'+'A'*30
    (tmp_path/'bad.py').write_text('key = '+repr(secret))
    report=collect(tmp_path)
    assert report['findings'] and secret not in json.dumps(report)


def test_empty_env_example_allowed(tmp_path):
    (tmp_path/'.env.example').write_text('STRIPE_SECRET_KEY=\n')
    report=collect(tmp_path)
    assert len(report['files'])==1 and not report['findings']


def test_snapshot_change_rejected(tmp_path):
    p=tmp_path/'readme.md';p.write_text('hello')
    (tmp_path/'release-manifest.json').write_text(json.dumps(collect(tmp_path)))
    assert len(publish.validate_snapshot(tmp_path)['files'])==1
    p.write_text('changed')
    with pytest.raises(ValueError):publish.validate_snapshot(tmp_path)


def test_dry_run_no_network(tmp_path,monkeypatch,capsys):
    (tmp_path/'readme.md').write_text('hello')
    (tmp_path/'release-manifest.json').write_text(json.dumps(collect(tmp_path)))
    monkeypatch.setattr(publish,'ROOT',tmp_path)
    monkeypatch.setattr(publish,'run',lambda *a,**k:pytest.fail('No network or subprocess permitted in dry-run.'))
    publish.main(['--owner','ChipmunkRPA','--dry-run'])
    assert json.loads(capsys.readouterr().out)['published'] is False

@pytest.mark.parametrize('scenario',['existing','wrong_user','unavailable'])
def test_target_fail_closed(monkeypatch,scenario):
    def fake(*args,**kwargs):
        if args[2]=='user':return CompletedProcess(args,0,'Other' if scenario=='wrong_user' else 'ChipmunkRPA','')
        return CompletedProcess(args,0 if scenario=='existing' else 1,'{}','Timeout')
    monkeypatch.setattr(publish,'run',fake)
    with pytest.raises(ValueError):publish.check_target('ChipmunkRPA','open-source-accounting')


def test_nonexistent_target(monkeypatch):
    def fake(*args,**kwargs):
        if args[2]=='user':return CompletedProcess(args,0,'ChipmunkRPA','')
        return CompletedProcess(args,1,'','HTTP 404')
    monkeypatch.setattr(publish,'run',fake)
    publish.check_target('ChipmunkRPA','open-source-accounting')

@pytest.mark.parametrize('private_result',[False,True])
def test_publish_flow_with_mocked_commands(tmp_path,monkeypatch,capsys,private_result):
    (tmp_path/'readme.md').write_text('Public original source')
    (tmp_path/'release-manifest.json').write_text(json.dumps(collect(tmp_path)))
    monkeypatch.setattr(publish,'ROOT',tmp_path)
    monkeypatch.setattr(publish.shutil,'which',lambda name:'/test/'+name)
    monkeypatch.setattr(publish,'check_target',lambda *args:None)
    commands=[]
    def fake(*args,**kwargs):
        commands.append(args)
        if args[:2]==('git','rev-parse'):return CompletedProcess(args,0,'a'*40,'')
        if args[:3]==('gh','repo','create'):return CompletedProcess(args,0,'created','')
        if args[:2]==('gh','api'):
            body={'object':{'sha':'a'*40}} if '/git/ref/' in args[2] else {'private':private_result,'html_url':'https://github.com/ChipmunkRPA/open-source-accounting'}
            return CompletedProcess(args,0,json.dumps(body),'')
        return CompletedProcess(args,0,'','')
    monkeypatch.setattr(publish,'run',fake)
    if private_result:
        with pytest.raises(SystemExit,match='Repository was created'):publish.main(['--owner','ChipmunkRPA','--confirm-public'])
    else:
        publish.main(['--owner','ChipmunkRPA','--confirm-public'])
        assert json.loads(capsys.readouterr().out)['published'] is True
    creation=next(c for c in commands if c[:3]==('gh','repo','create'))
    assert '--public' in creation and '--push' in creation
    assert not any('--force' in c for c in commands)
