from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripts import local_verify as lv
from scripts.security_static import scan_repository
from scripts.pre_push_ref_guard import parse_push_updates, blocked_main_updates

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def harness(tmp_path, monkeypatch):
    monkeypatch.setattr(lv, 'ROOT', tmp_path)
    monkeypatch.setattr(lv, '_observed_head', lambda: 'a' * 40)
    monkeypatch.setattr(lv.importlib.util, 'find_spec', lambda name: SimpleNamespace(origin='fixture'))
    (tmp_path/'scripts').mkdir()
    (tmp_path/'scripts/security_static.py').write_text('raise SystemExit(0)\n')
    calls=[]
    def fake_run(name, cmd, **kwargs):
        calls.append((name, cmd, kwargs))
        return {'name':name,'command':cmd,'required':True,'status':'PASS','returncode':0,'duration_s':0.0}
    monkeypatch.setattr(lv, 'run', fake_run)
    return tmp_path, calls


@pytest.mark.parametrize('profile',['security','merge'])
@pytest.mark.parametrize('skip',[False,True])
def test_missing_auditor_blocks_even_when_install_check_skipped(harness,monkeypatch,profile,skip):
    root,calls=harness
    monkeypatch.setattr(lv.importlib.util,'find_spec',lambda _:None)
    args=[profile,'--json-out','receipt.json']+(['--skip-install-check'] if skip else [])
    assert lv.main(args)==2
    report=json.loads((root/'receipt.json').read_text())
    assert report['status']=='BLOCKED'
    assert report['results'][0]['reason']=='required_module_missing'
    assert report['results'][0]['required'] is True
    assert calls==[]


@pytest.mark.parametrize('case',['absent','symlink'])
def test_scanner_cannot_disappear_or_be_redirected(harness,case):
    root,calls=harness;p=root/'scripts/security_static.py';p.unlink()
    if case=='symlink':p.symlink_to(root/'target.py')
    assert lv.main(['security','--skip-install-check','--json-out','receipt.json'])==2
    report=json.loads((root/'receipt.json').read_text())
    assert report['results'][0]['reason']=='required_scanner_missing' and not calls


def test_security_requires_both_scanner_and_same_interpreter_audit(harness):
    root,calls=harness
    assert lv.main(['security','--skip-install-check','--json-out','receipt.json'])==0
    assert [c[0] for c in calls]==['static-security','pip-audit']
    assert calls[-1][1][:3]==[sys.executable,'-m','pip_audit']
    assert calls[-1][2]['quiet'] is True
    report=json.loads((root/'receipt.json').read_text())
    assert report['status']=='PASS' and all(x['status']=='PASS' for x in report['results'])
    assert report['git_sha']=='a'*40


@pytest.mark.parametrize('failed',['import-smoke','compileall','pytest','repo-health'])
def test_failure_persists_actual_step_and_aborts(harness,monkeypatch,failed):
    root,calls=harness
    (root/'receipt.json').write_text('{"status":"PASS","old":true}')
    def fake_run(name,cmd,**kwargs):
        assert json.loads((root/'receipt.json').read_text())['status']=='RUNNING'
        calls.append(name)
        return {'name':name,'command':cmd,'required':True,'status':'FAIL' if name==failed else 'PASS','returncode':7 if name==failed else 0}
    monkeypatch.setattr(lv,'run',fake_run)
    assert lv.main(['quick','--json-out','receipt.json'])==1
    report=json.loads((root/'receipt.json').read_text())
    assert report['status']=='FAIL' and 'old' not in report
    assert calls[-1]==failed and report['results'][-1]['returncode']==7


@pytest.mark.parametrize('failed',['static-security','pip-audit'])
def test_security_command_failure_cannot_pass(harness,monkeypatch,failed):
    root,calls=harness
    def fake_run(name,cmd,**kwargs):
        calls.append(name)
        return {'name':name,'required':True,'status':'FAIL' if name==failed else 'PASS','returncode':1 if name==failed else 0}
    monkeypatch.setattr(lv,'run',fake_run)
    assert lv.main(['security','--skip-install-check','--json-out','receipt.json'])==1
    assert calls[-1]==failed
    assert json.loads((root/'receipt.json').read_text())['status']=='FAIL'


@pytest.mark.parametrize('case',['timeout','unavailable','interrupt'])
def test_run_records_runtime_failures_without_exception_payload(monkeypatch,tmp_path,capsys,case):
    def fail(*args,**kwargs):
        assert kwargs['shell'] is False and kwargs['timeout']==1
        if case=='timeout':raise subprocess.TimeoutExpired(args[0],1,output='DO_NOT_LOG_THIS')
        if case=='unavailable':raise OSError('DO_NOT_LOG_THIS')
        raise KeyboardInterrupt
    monkeypatch.setattr(lv.subprocess,'run',fail)
    result=lv.run('check',['trusted-tool'],cwd=tmp_path,timeout=1)
    assert result['status']=='BLOCKED'
    assert 'DO_NOT_LOG_THIS' not in json.dumps(result)+capsys.readouterr().out


def test_real_child_failure_and_quiet_output(tmp_path,capfd):
    result=lv.run('isolated-negative',[sys.executable,'-c','import sys; print("PRIVATE_CHILD_OUTPUT"); sys.exit(7)'],cwd=tmp_path,quiet=True)
    assert result['status']=='FAIL' and result['returncode']==7
    assert 'PRIVATE_CHILD_OUTPUT' not in capfd.readouterr().out


def test_real_child_timeout_is_bounded(tmp_path):
    result=lv.run('timeout',[sys.executable,'-c','import time; time.sleep(5)'],cwd=tmp_path,timeout=0.05)
    assert result['status']=='BLOCKED' and result['reason']=='command_timeout'


def test_unexpected_error_replaces_old_pass_without_raw_message(harness,monkeypatch,capsys):
    root,_=harness
    (root/'receipt.json').write_text('{"status":"PASS"}')
    def fail(*args,**kwargs):raise RuntimeError('SECRET_EXCEPTION_PAYLOAD')
    monkeypatch.setattr(lv,'run',fail)
    assert lv.main(['quick','--json-out','receipt.json'])==2
    report=(root/'receipt.json').read_text()
    assert json.loads(report)['status']=='BLOCKED'
    assert 'SECRET_EXCEPTION_PAYLOAD' not in report+capsys.readouterr().out


@pytest.mark.parametrize('case',['outside','symlink-file','symlink-parent','non-json'])
def test_unsafe_receipt_path_blocks_before_execution(harness,case):
    root,calls=harness
    target=root.parent/(root.name+'-outside.json'); target.write_text('sentinel')
    if case=='outside': path=target
    elif case=='symlink-file':path=root/'receipt.json';path.symlink_to(target)
    elif case=='symlink-parent':
        (root/'linked').symlink_to(root.parent,target_is_directory=True);path=root/'linked'/target.name
    else:path=root/'report.py'
    assert lv.main(['quick','--json-out',str(path)])==2
    assert calls==[] and target.read_text()=='sentinel'


def test_atomic_replace_failure_never_returns_success(harness,monkeypatch):
    root,calls=harness
    def fail(*args):raise OSError('not persisted')
    monkeypatch.setattr(lv.os,'replace',fail)
    assert lv.main(['quick','--json-out','receipt.json'])==2
    assert not calls and not list(root.glob('.verification-*'))


def test_missing_media_binary_is_blocked_and_persisted(harness,monkeypatch):
    root,calls=harness
    monkeypatch.setattr(lv.shutil,'which',lambda _:None)
    assert lv.main(['analysis','--skip-install-check','--json-out','receipt.json'])==2
    assert json.loads((root/'receipt.json').read_text())['results'][-1]['reason']=='required_binary_missing'
    assert not calls


@pytest.mark.parametrize('case',['missing','empty','outside','symlink','invalid-text'])
def test_scanner_rejects_unverifiable_scope(tmp_path,case):
    selected=tmp_path/'scope';selected.mkdir()
    target=tmp_path/'target.py';target.write_text('value=1\n')
    if case=='missing':selected=tmp_path/'missing'
    if case=='outside':selected=tmp_path.parent
    if case=='symlink':(selected/'redirect.py').symlink_to(target)
    if case=='invalid-text':(selected/'config.json').write_bytes(b'\xff\xfe')
    findings=scan_repository((selected,),root=tmp_path)
    assert findings and any(x.rule in ('SCAN_SCOPE_INVALID','TEXT_SOURCE_UNREADABLE') for x in findings)


@pytest.mark.parametrize('remote',['refs/heads/main','refs/heads/feature','refs/tags/v1'])
@pytest.mark.parametrize('local',['HEAD','refs/heads/feature','a'*40,'(delete)'])
def test_donor_guard_destination_semantics(remote,local):
    sha='0'*40 if local=='(delete)' else 'a'*40
    updates=parse_push_updates([f'{local} {sha} {remote} {"b"*40}\n'])
    assert bool(blocked_main_updates(updates))==(remote=='refs/heads/main')


def test_actual_git_push_is_blocked_without_touching_main(tmp_path):
    work=tmp_path/'work';work.mkdir();remote=tmp_path/'remote.git'
    def git(*args,cwd=work,check=True):
        return subprocess.run(['git',*args],cwd=cwd,capture_output=True,text=True,check=check,timeout=20)
    git('init','-q','--initial-branch=fixture');git('config','user.name','Isolated test');git('config','user.email','ci@example.invalid')
    (work/'README.md').write_text('fixture');git('add','.');git('commit','-qm','fixture')
    git('clone','--bare',str(work),str(remote),cwd=tmp_path)
    git('remote','add','origin',str(remote))
    (work/'scripts').mkdir();(work/'.githooks').mkdir()
    shutil.copyfile(ROOT/'scripts/pre_push_ref_guard.py',work/'scripts/pre_push_ref_guard.py')
    (work/'scripts/change_impact.py').write_text('print("")\n')
    (work/'scripts/local_verify.py').write_text('from pathlib import Path\nPath("CHECKS_EXECUTED").write_text("yes")\n')
    (work/'scripts/agent_event.py').write_text('raise SystemExit(0)\n')
    hook=work/'.githooks/pre-push';shutil.copyfile(ROOT/'.githooks/pre-push',hook);hook.chmod(0o755)
    git('config','core.hooksPath','.githooks')
    before=git('show-ref',cwd=remote).stdout
    denied=git('push','origin','HEAD:refs/heads/main',check=False)
    assert denied.returncode!=0 and 'prohibited' in denied.stderr
    assert git('show-ref',cwd=remote).stdout==before
    assert not (work/'CHECKS_EXECUTED').exists()
    allowed=git('push','origin','HEAD:refs/heads/allowed',check=False)
    assert allowed.returncode==0 and (work/'CHECKS_EXECUTED').exists()


def test_workflows_require_shared_runner_and_security_receipt():
    baseline=(ROOT/'.github/workflows/security.yml').read_text()
    assert 'python scripts/local_verify.py security' in baseline
    workflow=(ROOT/'.github/workflows/merge-gate.yml').read_text()
    security=workflow.split('\n  security:\n')[1].split('\n  merge-safe:\n')[0]
    assert 'python scripts/local_verify.py security' in security
    assert 'name: merge-safe-security-evidence' in security
    assert 'if: always()' in security and 'if-no-files-found: error' in security


def test_hook_does_not_override_same_interpreter_auditor_preflight():
    hook=(ROOT/'.githooks/pre-push').read_text()
    assert 'command -v pip-audit' not in hook
    assert 'python scripts/local_verify.py security --skip-install-check' in hook
    assert hook.index('python scripts/pre_push_ref_guard.py') < hook.index('scripts/change_impact.py')
