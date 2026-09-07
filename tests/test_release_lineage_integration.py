from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripts import local_verify as lv
from scripts import main_lineage_sentinel as ml
from scripts import release_authority_guard as rg

ROOT = Path(__file__).resolve().parents[1]
REPO = 'rotprods/motion-OS'
SHA, OTHER = 'a' * 40, 'b' * 40


def pull(**changes):
    item = dict(number=42, state='closed', draft=False, merged_at='2026-08-30T12:00:00Z',
                merge_commit_sha=SHA, base={'ref':'main','repo':{'full_name':REPO}})
    item.update(changes)
    return item


def assess(**changes):
    args = dict(repository=REPO, release_sha=SHA, live_main_sha=SHA, live_main_sha_after=SHA,
                project_state={'release_status':'RELEASED','p0_blockers':[]}, associated_pulls=[pull()])
    args.update(changes)
    return rg.assess_release_authority(**args)


def test_exact_donor_contract_is_scoped_not_publish_permission():
    out = assess().to_dict()
    assert out['ok'] and out['state']=='RELEASE_LINEAGE_VERIFIED'
    assert out['matched_pr_numbers']==[42]
    assert out['promotion_authorized'] is False
    assert 'only' in out['authority_scope']


@pytest.mark.parametrize('changes,state', [
    ({'release_sha':OTHER}, 'RELEASE_TARGET_NOT_CURRENT_MAIN'),
    ({'live_main_sha_after':OTHER}, 'LIVE_MAIN_DRIFTED_DURING_CHECK'),
    ({'associated_pulls':[]}, 'MAIN_LINEAGE_UNVERIFIED'),
    ({'associated_pulls':[pull(merged_at=None)]}, 'MAIN_LINEAGE_UNVERIFIED'),
    ({'associated_pulls':[pull(state='open')]}, 'MAIN_LINEAGE_UNVERIFIED'),
    ({'associated_pulls':[pull(draft=True)]}, 'MAIN_LINEAGE_UNVERIFIED'),
    ({'associated_pulls':[pull(merged=False)]}, 'MAIN_LINEAGE_UNVERIFIED'),
    ({'associated_pulls':[pull(merge_commit_sha=OTHER)]}, 'MAIN_LINEAGE_UNVERIFIED'),
    ({'associated_pulls':[pull(base={'ref':'release','repo':{'full_name':REPO}})]}, 'MAIN_LINEAGE_UNVERIFIED'),
    ({'associated_pulls':[pull(base={'ref':'main','repo':{'full_name':'other/repo'}})]}, 'MAIN_LINEAGE_UNVERIFIED'),
])
def test_donor_denial_and_cross_repository_cases(changes,state):
    out=assess(**changes)
    assert not out.ok and out.state==state and out.authority=='BLOCKED'


@pytest.mark.parametrize('state', [None,[],{}, {'release_status':'RELEASED'},
    {'release_status':'RELEASED','p0_blockers':None}, {'release_status':'RELEASED','p0_blockers':False},
    {'release_status':'RELEASED','p0_blockers':''}, {'release_status':'RELEASED','p0_blockers':[False]},
    {'release_status':'RELEASED','p0_blockers':['']}, {'release_status':'RELEASED','p0_blockers':['P0']},
    {'release_status':True,'p0_blockers':[]}, {'release_status':'BLOCKED','p0_blockers':[]}])
def test_falsey_or_invalid_release_fields_never_pass(state):
    with pytest.raises(ValueError): assess(project_state=state)


@pytest.mark.parametrize('changes', [dict(number=True),dict(number=-1),dict(merged_at='bogus'),
    dict(merged_at='2026-08-30T12:00:00'),dict(merged_at=''),dict(merged_at=False),
    dict(merge_commit_sha='bad'),dict(base={}),dict(state=None),dict(draft=0)])
def test_invalid_lineage_record_rejected(changes):
    with pytest.raises(ValueError): assess(associated_pulls=[pull(**changes)])


def test_duplicate_or_malformed_association_set_rejected():
    for items in [None,{},[None],[pull(),pull()],[pull(number=i+1) for i in range(101)]]:
        with pytest.raises(ValueError): assess(associated_pulls=items)
    assert assess(associated_pulls=[pull(number=9),pull(number=2)]).matched_pr_numbers==(2,9)


@pytest.mark.parametrize('repo', ['../repo','a/..','a/.','a/b/c','a/b?x=y','a/b#x','a/b\n','/repo','a/'+'b'*101])
def test_repository_cannot_escape_fixed_api_resource(repo):
    with pytest.raises(ValueError): ml._validate_repo(repo)


@pytest.mark.parametrize('raw', [b'{"ok":true,"ok":false}',b'{"x":NaN}',b'{"x":Infinity}',
    b'{"x":1e999}',b'\xff',b'{',b'['*35+b'0'+b']'*35, b' '* (ml.MAX_BYTES+1)])
def test_json_parser_rejects_ambiguity_and_resource_excess(raw):
    with pytest.raises((ValueError,UnicodeError)): ml._strict_json(raw)


class Response:
    def __init__(self, *, raw=b'[]', status=200, url=None, headers=None):
        self.raw,self.status,self.url=raw,status,url
        self.headers={'Content-Type':'application/json; charset=utf-8',**(headers or {})}
        self.read_sizes=[]
    def __enter__(self): return self
    def __exit__(self,*_): return False
    def geturl(self): return self.url
    def read(self,size):
        self.read_sizes.append(size)
        return self.raw[:size]


def install_transport(monkeypatch,response):
    calls=[]
    def build(*handlers):
        assert any(isinstance(x,ml._NoRedirect) for x in handlers)
        assert any(isinstance(x,ml.ProxyHandler) and x.proxies=={} for x in handlers)
        def open_(req,timeout):
            calls.append((req,timeout))
            if response.url is None: response.url=req.full_url
            return response
        return SimpleNamespace(open=open_)
    monkeypatch.setattr(ml,'build_opener',build)
    return calls


def test_transport_is_fixed_origin_get_bounded_and_credential_scoped(monkeypatch):
    response=Response(); calls=install_transport(monkeypatch,response)
    assert ml.fetch_associated_pulls(repository=REPO,commit_sha=SHA,token='synthetic-token')==[]
    req,timeout=calls[0]
    assert req.full_url==f'https://api.github.com/repos/{REPO}/commits/{SHA}/pulls?per_page=100'
    assert req.get_method()=='GET' and req.get_header('Authorization')=='Bearer synthetic-token'
    assert timeout==10.0 and response.read_sizes==[ml.MAX_BYTES+1]


@pytest.mark.parametrize('kwargs', [dict(status=403),dict(status=500),dict(url='https://evil.invalid/'),
    dict(headers={'Link':'<https://evil.invalid/>; rel="next"'}),
    dict(headers={'Content-Type':'text/html'}),dict(headers={'Content-Encoding':'gzip'}),
    dict(raw=b' '* (ml.MAX_BYTES+1))])
def test_incomplete_redirected_or_invalid_http_cannot_authorize(monkeypatch,kwargs):
    install_transport(monkeypatch,Response(**kwargs))
    with pytest.raises(ValueError): ml.fetch_associated_pulls(repository=REPO,commit_sha=SHA,token='synthetic-token')


@pytest.mark.parametrize('timeout', [0,-1,True,float('nan'),float('inf'),31,'10'])
def test_invalid_timeouts_fail_before_network(monkeypatch,timeout):
    calls=install_transport(monkeypatch,Response())
    with pytest.raises(ValueError): ml.fetch_associated_pulls(repository=REPO,commit_sha=SHA,token='synthetic-token',timeout_s=timeout)
    assert not calls


def test_redirect_is_rejected_before_new_request_can_carry_credentials():
    with pytest.raises(ValueError):
        ml._NoRedirect().redirect_request(None,None,302,'moved',{},'https://evil.invalid/')


def test_live_main_requires_named_branch_and_typed_commit(monkeypatch):
    for value in [[],{},dict(name='dev',commit={'sha':SHA}),dict(name='main',commit={'sha':'bad'})]:
        monkeypatch.setattr(rg,'_github_json',lambda **kw:value)
        with pytest.raises(ValueError): rg.fetch_live_main_sha(repository=REPO,token='synthetic-token')


def git(root,*args):
    cp=subprocess.run(['git',*args],cwd=root,text=True,capture_output=True,timeout=10)
    assert cp.returncode==0,cp.stderr
    return cp.stdout.strip()


@pytest.fixture
def checkout(tmp_path,monkeypatch):
    git(tmp_path,'init','--quiet'); git(tmp_path,'config','user.name','Lineage Test')
    git(tmp_path,'config','user.email','test@example.invalid')
    path=tmp_path/'state/project_state.json'; path.parent.mkdir()
    path.write_text(json.dumps({'release_status':'RELEASED','p0_blockers':[]}))
    git(tmp_path,'add','.'); git(tmp_path,'commit','--quiet','-m','synthetic state')
    sha=git(tmp_path,'rev-parse','HEAD')
    monkeypatch.chdir(tmp_path); monkeypatch.setattr(lv,'ROOT',tmp_path)
    return tmp_path,path,sha


def test_state_matches_actual_committed_git_blob(checkout):
    root,path,sha=checkout
    state,digest=rg._read_bound_state(Path('state/project_state.json'),sha)
    assert state['release_status']=='RELEASED' and digest==hashlib.sha256(path.read_bytes()).hexdigest()
    git(root,'tag','-a','v-test','-m','test')
    assert git(root,'rev-parse','v-test^{commit}')==sha


@pytest.mark.parametrize('case',['dirty','wrong_head','untracked','absolute','traversal','symlink','parent_symlink'])
def test_mismatched_state_or_checkout_rejected(checkout,case):
    root,path,sha=checkout; rel=Path('state/project_state.json')
    if case=='dirty': path.write_text(path.read_text()+' ')
    if case=='wrong_head': sha=OTHER
    if case=='untracked': rel=Path('override.json');(root/rel).write_bytes(path.read_bytes())
    if case=='absolute': rel=path
    if case=='traversal': rel=Path('state/../state/project_state.json')
    if case=='symlink': path.rename(root/'real.json');path.symlink_to(root/'real.json')
    if case=='parent_symlink': path.parent.rename(root/'real');(root/'state').symlink_to(root/'real',target_is_directory=True)
    with pytest.raises(ValueError): rg._read_bound_state(rel,sha)


def metadata(monkeypatch,sha,*,drift=False):
    values=iter([sha,OTHER if drift else sha]); calls=[]
    def main(**kwargs): calls.append('main'); return next(values)
    monkeypatch.setattr(rg,'fetch_live_main_sha',main)
    monkeypatch.setattr(rg,'fetch_associated_pulls',lambda **kw:[pull(merge_commit_sha=sha)])
    return calls


def test_cli_full_boundary_with_real_git_and_injected_metadata(checkout,monkeypatch,capsys):
    root,path,sha=checkout;calls=metadata(monkeypatch,sha)
    assert rg.main(['--repository',REPO,'--release-sha',sha])==0
    out=json.loads((root/'.artifacts/release-lineage.json').read_text())
    assert out['ok'] and out['promotion_authorized'] is False and calls==['main','main']
    assert out['state_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()


def test_cli_drift_blocks_and_replaces_old_pass(checkout,monkeypatch):
    root,path,sha=checkout;metadata(monkeypatch,sha,drift=True)
    p=root/'.artifacts/release-lineage.json';p.parent.mkdir();p.write_text('{"ok":true}')
    assert rg.main(['--repository',REPO,'--release-sha',sha])==2
    assert json.loads(p.read_text())['state']=='LIVE_MAIN_DRIFTED_DURING_CHECK'


def test_cli_unreleased_state_does_not_request_network(checkout,monkeypatch):
    root,path,sha=checkout;path.write_text('{"release_status":"BLOCKED","p0_blockers":[]}')
    git(root,'add','.');git(root,'commit','--quiet','-m','blocked');sha=git(root,'rev-parse','HEAD')
    calls=metadata(monkeypatch,sha)
    assert rg.main(['--repository',REPO,'--release-sha',sha])==3
    assert not calls and not json.loads((root/'.artifacts/release-lineage.json').read_text())['ok']


def test_cli_state_drift_during_metadata_is_rejected(checkout,monkeypatch):
    root,path,sha=checkout;metadata(monkeypatch,sha)
    def pulls(**kwargs): path.write_bytes(path.read_bytes()+b' ');return [pull(merge_commit_sha=sha)]
    monkeypatch.setattr(rg,'fetch_associated_pulls',pulls)
    assert rg.main(['--repository',REPO,'--release-sha',sha])==3
    assert not json.loads((root/'.artifacts/release-lineage.json').read_text())['ok']


def test_api_exception_never_echoes_token_or_remote_body(checkout,monkeypatch,capsys):
    _,_,sha=checkout
    def fail(**kwargs): raise RuntimeError('PRIVATE_CREDENTIAL_AND_BODY')
    monkeypatch.setattr(rg,'fetch_live_main_sha',fail)
    assert rg.main(['--repository',REPO,'--release-sha',sha])==3
    assert 'PRIVATE_CREDENTIAL_AND_BODY' not in capsys.readouterr().out


def test_receipt_failure_never_returns_success(checkout,monkeypatch):
    _,_,sha=checkout;metadata(monkeypatch,sha)
    def fail(*args):raise OSError('private path')
    monkeypatch.setattr(rg,'_emit',fail)
    assert rg.main(['--repository',REPO,'--release-sha',sha])==3


def test_sentinel_cli_success_and_degradation(checkout,monkeypatch):
    root,_,sha=checkout
    monkeypatch.setattr(ml,'fetch_associated_pulls',lambda **kw:[pull(merge_commit_sha=sha)])
    assert ml.main(['--repository',REPO,'--sha',sha])==0
    monkeypatch.setattr(ml,'fetch_associated_pulls',lambda **kw:[])
    assert ml.main(['--repository',REPO,'--sha',sha])==2
    assert not json.loads((root/'.artifacts/main-lineage.json').read_text())['ok']


@pytest.mark.parametrize('module',['scripts.main_lineage_sentinel','scripts.release_authority_guard'])
def test_real_module_entrypoint_imports_without_editable_install(module):
    env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','GITHUB_TOKEN'}}
    cp=subprocess.run([sys.executable,'-m',module,'--help'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=10)
    assert cp.returncode==0 and 'usage:' in cp.stdout and 'Traceback' not in cp.stderr


def test_workflows_use_modules_read_only_and_persist_failed_reports():
    for filename,module in [('release-guard.yml','release_authority_guard'),('main-lineage-sentinel.yml','main_lineage_sentinel')]:
        text=(ROOT/'.github/workflows'/filename).read_text()
        assert f'python -m scripts.{module}' in text
        assert 'contents: read' in text and 'pull-requests: read' in text
        assert 'persist-credentials: false' in text and 'if-no-files-found: error' in text
        assert 'if: always()' in text and 'continue-on-error' not in text and '--token' not in text
        assert 'release create' not in text and 'git push' not in text


def test_policy_files_force_full_verification():
    from scripts.change_impact import classify
    for path in ['scripts/main_lineage_sentinel.py','scripts/release_authority_guard.py',
                 'tests/test_release_lineage_integration.py','.github/workflows/main-lineage-sentinel.yml']:
        assert all(classify([path]).values())
