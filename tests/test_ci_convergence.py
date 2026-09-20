from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import textwrap
from types import SimpleNamespace

import pytest

from scripts.change_impact import changed_paths, classify
from scripts.verify_node_lock import verify_runtime

ROOT = Path(__file__).resolve().parents[1]
CLASSIFIER = ROOT / 'scripts/change_impact.py'


@pytest.mark.parametrize('path', [
    'src/avatar/render_guard.py', 'src/qa/release_manifest.py',
    'schemas/new_contract.schema.json', 'src/reverse_engineering/a.py',
    'src/compilers/other.py', 'state/project_state.json', 'unrecognized/runtime.py',
    'STATE.md', 'TASKS.md', 'HANDOFF.md', 'GOAL.md', 'AGENTS.md',
    'state/checkpoints.json', 'state/github_sync.json', 'state/drive_sync.json',
    'registry/artifact_registry.json', 'coordination/ACTIVE_AGENTS.yaml',
    'config/alignment_weights.yaml', 'scripts/repo_health.py',
    'src/studio/api.py', 'src/content/tts_integrity.py', 'src/skills/runtime.py',
    '.github/workflows/new-workflow.yaml', '.github/actions/build/action.yml',
    'backend/new.py', 'frontend/src/new.tsx', 'Dockerfile', '.npmrc',
    'scripts/verify_node_lock.py', 'tests/test_ci_convergence.py',
])
def test_shared_authority_and_unknown_paths_force_full(path):
    assert all(classify([path]).values())


@pytest.mark.parametrize('path', ['README.md', 'docs/user_guide.md', 'CHANGELOG.md',
                                   'reports/results.txt', 'evidence/session/HANDOFF.md'])
def test_plain_documentation_remains_cheap(path):
    assert not any(classify([path]).values())


@pytest.mark.parametrize('paths', [None, True, 'README.md', [None], [''], ['../README.md'],
    ['/README.md'], ['./README.md'], ['src//extraction/a.py'], ['src/extraction/a\\b.py'],
    ['src/extraction/a\nb.py'], ['"src/extraction/a.py"'], ['src/extraction/a.py ']])
def test_ambiguous_transport_forces_full(paths):
    assert all(classify(paths).values())


def git(repo, *args):
    return subprocess.run(['git', *args], cwd=repo, capture_output=True, check=True).stdout


def init_repo(repo):
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.name', 'MOTION CI fixture')
    git(repo, 'config', 'user.email', 'ci@example.invalid')


def commit(repo):
    git(repo, 'add', '-A')
    git(repo, 'commit', '-qm', 'fixture')
    return git(repo, 'rev-parse', 'HEAD').decode().strip()


def cli(repo, *args, data=b''):
    return subprocess.run([sys.executable, str(CLASSIFIER), *args], cwd=repo,
                          input=data, capture_output=True, timeout=15)


def test_git_rename_from_runtime_to_docs_preserves_deleted_source(tmp_path):
    init_repo(tmp_path)
    old = tmp_path / 'runtime/remotion/src/Layer.tsx'
    old.parent.mkdir(parents=True); old.write_text('same content\n')
    base = commit(tmp_path)
    new = tmp_path / 'docs/archived.md'; new.parent.mkdir(); old.rename(new)
    commit(tmp_path)
    paths, uncertain = changed_paths(base, cwd=tmp_path)
    assert not uncertain
    assert sorted(paths) == ['docs/archived.md', 'runtime/remotion/src/Layer.tsx']
    assert classify(paths)['remotion'] is True
    result = cli(tmp_path, '--git-base', base)
    assert result.returncode == 0 and json.loads(result.stdout) == classify(paths)


def test_git_newline_name_cannot_hide_a_change(tmp_path):
    init_repo(tmp_path)
    (tmp_path/'README.md').write_text('first'); base = commit(tmp_path)
    (tmp_path/'docs').mkdir(); (tmp_path/'docs/odd\nname.md').write_text('second')
    commit(tmp_path)
    paths, uncertain = changed_paths(base, cwd=tmp_path)
    assert paths == ['docs/odd\nname.md'] and not uncertain
    assert all(classify(paths).values())
    assert all(json.loads(cli(tmp_path, '--git-base', base).stdout).values())


def test_missing_merge_base_is_full_not_empty(tmp_path):
    init_repo(tmp_path)
    (tmp_path/'README.md').write_text('first'); commit(tmp_path)
    assert changed_paths('origin/main', cwd=tmp_path) == ([], True)
    assert all(json.loads(cli(tmp_path, '--git-base', 'origin/main').stdout).values())


def test_git_failure_does_not_claim_no_changes(tmp_path):
    assert changed_paths('HEAD^1', cwd=tmp_path) == ([], True)


@pytest.mark.parametrize('ref', ['--help', 'HEAD;touch OWNED', '$(touch OWNED)', 'HEAD\nmain'])
def test_revision_text_is_never_shell_code(tmp_path, ref):
    assert changed_paths(ref, cwd=tmp_path) == ([], True)
    assert not (tmp_path/'OWNED').exists()


@pytest.mark.parametrize('data', [b'\xff\0', b'README.md', b'\0', b' ' * 1_048_577], ids=['invalid-utf8','unterminated','empty-record','oversized'])
def test_invalid_nul_transport_is_conservative(tmp_path, data):
    result = cli(tmp_path, '--nul', data=data)
    assert result.returncode == 0 and all(json.loads(result.stdout).values())


def test_valid_nul_input_and_fixed_profile_output(tmp_path):
    data = b'README.md\0runtime/remotion/src/Layer.tsx\0'
    assert json.loads(cli(tmp_path, '--nul', data=data).stdout)['remotion']
    result = cli(tmp_path, '--nul', '--profiles', data=data)
    assert result.stdout == b'remotion\n'


def test_real_hook_uses_same_git_impact_and_propagates_profile_failure(tmp_path):
    init_repo(tmp_path)
    scripts = tmp_path/'scripts'; scripts.mkdir()
    shutil.copyfile(ROOT/'scripts/pre_push_ref_guard.py', scripts/'pre_push_ref_guard.py')
    shutil.copyfile(CLASSIFIER, scripts/'change_impact.py')
    (scripts/'local_verify.py').write_text(
        'import os,sys\nwith open(os.environ["TRACE"], "a") as f: f.write(sys.argv[1]+"\\n")\n'
        'raise SystemExit(7 if sys.argv[1]=="remotion" else 0)\n')
    (scripts/'agent_event.py').write_text('raise SystemExit(0)\n')
    old = tmp_path/'runtime/remotion/src/Layer.tsx'; old.parent.mkdir(parents=True)
    old.write_text('same'); base = commit(tmp_path)
    git(tmp_path, 'update-ref', 'refs/remotes/origin/main', base)
    new = tmp_path/'docs/old.md'; new.parent.mkdir(); old.rename(new); commit(tmp_path)
    trace=tmp_path/'trace'
    cp=subprocess.run(['bash', str(ROOT/'.githooks/pre-push')], cwd=tmp_path,
                      env={**os.environ,'TRACE':str(trace)}, input=b'HEAD '+b'a'*40+b' refs/heads/feature '+b'b'*40+b'\n', capture_output=True, timeout=20)
    assert cp.returncode == 7
    assert trace.read_text().splitlines() == ['quick','remotion']


def test_classifier_crash_cannot_be_swallowed_by_hook(tmp_path):
    init_repo(tmp_path)
    (tmp_path/'scripts').mkdir()
    (tmp_path/'scripts/change_impact.py').write_text('raise SystemExit(2)\n')
    shutil.copyfile(ROOT/'scripts/pre_push_ref_guard.py',tmp_path/'scripts/pre_push_ref_guard.py')
    cp=subprocess.run(['bash', str(ROOT/'.githooks/pre-push')], cwd=tmp_path,
                      input=b'HEAD '+b'a'*40+b' refs/heads/feature '+b'b'*40+b'\n', capture_output=True, timeout=20)
    assert cp.returncode == 2
    assert b'local_verify' not in cp.stderr


def make_lock(tmp_path):
    package={'name':'fixture','dependencies':{'example':'1.0.0'}}
    lock={'name':'fixture','lockfileVersion':3,'packages':{'':package}}
    (tmp_path/'package.json').write_text(json.dumps(package))
    (tmp_path/'package-lock.json').write_text(json.dumps(lock))


def fake_runner(calls, mutate=None):
    def run(argv, **kwargs):
        calls.append(argv)
        assert kwargs['shell'] is False
        if mutate:
            response=mutate(argv,kwargs)
            if response is not None:
                return response
        return SimpleNamespace(returncode=0, stdout='22.16.0\n' if '--version' in argv else '{}')
    return run


def test_lock_proof_installs_twice_without_any_resolution(tmp_path):
    make_lock(tmp_path); calls=[]
    report=verify_runtime(tmp_path,runner=fake_runner(calls))
    assert report['status']=='PASS'
    assert calls.count(['npm','ci','--no-audit','--no-fund'])==2
    assert all('install' not in cmd for cmd in calls)
    assert len(report['installs'])==2


def test_lock_drift_aborts_before_second_install(tmp_path):
    make_lock(tmp_path); calls=[]
    def mutate(argv,kwargs):
        if 'ci' in argv:
            with (tmp_path/'package-lock.json').open('a') as f: f.write(' ')
    report=verify_runtime(tmp_path,runner=fake_runner(calls,mutate))
    assert report['errors']==['approved_inputs_changed']
    assert len(report['installs'])==1


def test_install_failure_is_not_retried_or_hidden(tmp_path):
    make_lock(tmp_path); calls=[]
    def fail(argv,kwargs):
        if 'ci' in argv: return SimpleNamespace(returncode=1,stdout='PRIVATE_ERROR_PAYLOAD')
    report=verify_runtime(tmp_path,runner=fake_runner(calls,fail))
    assert report['status']=='FAIL' and len(report['installs'])==1
    assert 'PRIVATE_ERROR_PAYLOAD' not in json.dumps(report)


def test_install_timeout_is_not_blindly_retried(tmp_path):
    make_lock(tmp_path); calls=[]
    def fail(argv,kwargs):
        if 'ci' in argv: raise subprocess.TimeoutExpired(argv,1,output='PRIVATE_TIMEOUT')
    report=verify_runtime(tmp_path,runner=fake_runner(calls,fail))
    assert report['errors']==['runtime_execution_failed']
    assert sum('ci' in cmd for cmd in calls)==1
    assert 'PRIVATE_TIMEOUT' not in json.dumps(report)


@pytest.mark.parametrize('case', ['missing','json','duplicate','mismatch','symlink'])
def test_invalid_lock_never_invokes_npm(tmp_path,case):
    make_lock(tmp_path); calls=[]; lock=tmp_path/'package-lock.json'
    if case=='missing': lock.unlink()
    if case=='json': lock.write_text('{')
    if case=='duplicate': lock.write_text('{"a":1,"a":2}')
    if case=='mismatch': (tmp_path/'package.json').write_text('{"dependencies":{"bad":"2"}}')
    if case=='symlink':
        lock.rename(tmp_path/'target'); lock.symlink_to(tmp_path/'target')
    assert verify_runtime(tmp_path,runner=fake_runner(calls))['status']=='FAIL'
    assert not calls


def workflows():
    return sorted(p for p in (ROOT/'.github/workflows').iterdir() if p.suffix in ('.yml','.yaml'))


def test_all_workflows_keep_pinned_actions_and_nonpersistent_credentials():
    files=workflows(); assert len(files)>=8
    for p in files:
        text=p.read_text()
        assert 'permissions:\n  contents: read' in text, p
        assert not any(x in text for x in ('pull_request_target:', 'workflow_run:', 'self-hosted',
                                          'write-all','persist-credentials: true','secrets: inherit')),p
        for uses in re.findall(r'^\s*-?\s*uses:\s+(\S+)',text,re.M):
            assert re.fullmatch(r'[A-Za-z0-9_./-]+@[0-9a-f]{40}',uses), (p,uses)
        for block in re.split(r'(?=^      - uses:)',text,flags=re.M):
            if block.lstrip().startswith('- uses: actions/checkout@'):
                assert 'persist-credentials: false' in block,p
        assert 'npm install' not in text,p
        assert 'rm -f package-lock' not in text,p


def test_required_remotion_job_consumes_lock_proof_and_persists_it():
    text=(ROOT/'.github/workflows/merge-gate.yml').read_text()
    block=text.split('\n  remotion:\n')[1].split('\n  security:\n')[0]
    assert 'python scripts/verify_node_lock.py --json-out .artifacts/node-lock-verification.json' in block
    assert '.artifacts/node-lock-verification.json' in block.split('path: |')[1]
    assert 'if-no-files-found: error' in block


def test_local_and_cloud_use_the_same_git_transport():
    workflow=(ROOT/'.github/workflows/merge-gate.yml').read_text()
    classify_block=workflow.split('\n  classify:\n')[1].split('\n  quick:\n')[0]
    hook=(ROOT/'.githooks/pre-push').read_text()
    assert 'scripts/change_impact.py --git-base HEAD^1' in classify_block
    assert 'scripts/change_impact.py --git-base origin/main --profiles' in hook
    assert 'git diff --name-only' not in classify_block+hook
    assert '|| git diff' not in hook


def test_actionlint_is_digest_pinned_and_required_before_quick():
    text=(ROOT/'.github/workflows/merge-gate.yml').read_text()
    assert text.index('Validate every workflow with pinned actionlint') < text.index('Run the same local-first gate')
    assert '8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8' in text
    assert 'sha256sum --check --strict' in text
    assert 'curl |' not in text


def test_actionlint_checksum_mismatch_stops_before_extraction(tmp_path):
    text=(ROOT/'.github/workflows/merge-gate.yml').read_text()
    block=text.split('      - name: Validate every workflow with pinned actionlint\n')[1].split('      - name:')[0]
    shell=textwrap.dedent(block.split('        run: |\n')[1])
    bin_dir=tmp_path/'bin'; bin_dir.mkdir(); marker=tmp_path/'extracted'
    curl=bin_dir/'curl'
    curl.write_text('#!/usr/bin/env bash\nwhile [[ $# -gt 0 ]]; do\nif [[ "$1" == "-o" ]]; then printf bad > "$2"; exit 0; fi\nshift\ndone\nexit 1\n')
    curl.chmod(0o755)
    tar=bin_dir/'tar'; tar.write_text('#!/usr/bin/env bash\ntouch "$MARKER"\n');tar.chmod(0o755)
    cp=subprocess.run(['bash','-c',shell],cwd=tmp_path,
         env={**os.environ,'PATH':str(bin_dir)+os.pathsep+os.environ['PATH'],'MARKER':str(marker)},
         capture_output=True,timeout=15)
    assert cp.returncode!=0 and not marker.exists()
