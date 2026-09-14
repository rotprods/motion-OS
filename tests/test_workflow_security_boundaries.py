"""Adversarial policy and real CLI regressions; no hostile workflow is uploaded."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/workflow_security_gate.py'
spec = importlib.util.spec_from_file_location('workflow_security_boundaries_target', SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

SAFE = '''name: safe
on:
  pull_request:
permissions:
  contents: read
concurrency:
  group: safe
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          persist-credentials: false
      - run: python -V
'''


def blocking(text: str) -> list:
    return [f for f in mod.audit_text('test.yml', text) if f.severity in {'P0', 'P1'}]


@pytest.mark.parametrize('value', ['write # reason', "'write'", '"write"', '${{ \'write\' }}'])
def test_write_permission_spelling_cannot_evade_policy(value):
    assert blocking(SAFE.replace('contents: read', 'contents: ' + value))


@pytest.mark.parametrize('replacement', [
    'on: [pull_request_target]',
    'on: pull_request_target',
    'on: {pull_request_target: {}}',
    'on:\n  "pull_request_target":',
    'on:\n  pull_request_target: # note',
])
def test_equivalent_privileged_triggers_cannot_evade_policy(replacement):
    assert blocking(SAFE.replace('on:\n  pull_request:', replacement))


@pytest.mark.parametrize('replacement', [
    "'uses': actions/checkout@v4",
    '"uses": actions/checkout@v4',
    'uses: &action actions/checkout@v4',
    'uses: *action',
    'uses: ./unchecked-local-action',
    'uses: docker://tool@sha256:bad',
])
def test_unsupported_action_spellings_are_rejected(replacement):
    assert blocking(SAFE.replace('uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262', replacement))


def test_comment_cannot_disable_credential_persistence():
    assert blocking(SAFE.replace('persist-credentials: false', '# persist-credentials: false'))


def test_named_step_cannot_borrow_a_setting_from_next_step():
    text = SAFE.replace('- uses:', '- name: checkout\n        uses:')
    text = text.replace('          persist-credentials: false\n', '')
    text = text.replace('      - run: python -V', '      - run: python -V\n        env:\n          persist-credentials: false')
    assert blocking(text)


def test_script_text_cannot_impersonate_checkout_configuration():
    text = SAFE.replace('          persist-credentials: false\n', '')
    text = text.replace('      - run: python -V', "      - run: |\n          echo 'persist-credentials: false'\n")
    assert blocking(text)


def test_step_timeout_cannot_satisfy_job_timeout():
    text = SAFE.replace('    timeout-minutes: 10\n', '')
    text = text.replace('      - run: python -V', '      - run: python -V\n        timeout-minutes: 10')
    assert blocking(text)


@pytest.mark.parametrize('value', ['0', '-1', 'true', '${{ 10 }}', '9999999'])
def test_job_timeout_must_be_bounded_literal(value):
    assert blocking(SAFE.replace('timeout-minutes: 10', 'timeout-minutes: ' + value))


@pytest.mark.parametrize('value', ['true # reason', "'true'", '${{ true }}'])
def test_dynamic_or_true_continue_on_error_is_rejected(value):
    text = SAFE.replace('    steps:', '    continue-on-error: ' + value + '\n    steps:')
    assert blocking(text)


@pytest.mark.parametrize('text', [
    '',
    'permissions:\n  contents: read\nconcurrency:\n  group: fake\n',
    'on:\n  pull_request:\npermissions:\n  contents: read\nconcurrency:\n  group: x\njobs: {}\n',
    SAFE + '\n---\n' + SAFE,
    SAFE.replace('contents: read', 'contents: read\n  contents: write'),
    SAFE.replace('permissions:\n  contents: read', 'permissions: {contents: write}'),
    SAFE.replace('permissions:\n  contents: read', 'permissions: &p\n  contents: read'),
])
def test_ambiguous_missing_or_unsupported_structure_is_not_pass(text):
    assert blocking(text)


def test_harmless_comments_and_named_steps_remain_supported():
    text = SAFE.replace('contents: read', "contents: 'read' # explicit read-only")
    text = text.replace('persist-credentials: false', 'persist-credentials: false # no persistence')
    text = text.replace('- uses:', '- name: checkout\n        uses:')
    assert not blocking(text)


def test_policy_strings_inside_run_are_data_not_configuration():
    text = SAFE.replace('run: python -V', "run: |\n          printf '%s\\n' 'contents: write' 'continue-on-error: true'\n")
    assert not blocking(text)


def test_templates_nested_in_run_body_are_not_missed():
    text = SAFE.replace('run: python -V', "run: |\n          if true; then\n            echo '${{ github.event.pull_request.title }}'\n          fi\n")
    assert blocking(text)


def make_repo(root: Path) -> None:
    folder = root / '.github/workflows'
    folder.mkdir(parents=True)
    (folder / 'safe.yml').write_text(SAFE, encoding='utf-8')


def cli(root: Path, output: str = 'receipt.json'):
    return subprocess.run([sys.executable, str(SCRIPT), '--root', str(root), '--json-out', output],
                          cwd=root, capture_output=True, text=True, timeout=10)


def test_predictable_temporary_symlink_cannot_overwrite_another_file(tmp_path):
    make_repo(tmp_path)
    target = tmp_path / 'unrelated.txt'
    target.write_text('DO_NOT_CHANGE')
    (tmp_path / 'receipt.json.tmp').symlink_to(target)
    result = cli(tmp_path)
    assert target.read_text() == 'DO_NOT_CHANGE'
    assert result.returncode == 0
    assert json.loads((tmp_path / 'receipt.json').read_text())['status'] == 'PASS'


def test_invalid_utf8_cannot_leave_an_older_pass_report(tmp_path):
    make_repo(tmp_path)
    report = tmp_path / 'receipt.json'
    report.write_text('{"status":"PASS","old":true}')
    (tmp_path / '.github/workflows/safe.yml').write_bytes(b'\xff')
    result = cli(tmp_path)
    assert result.returncode != 0
    data = json.loads(report.read_text())
    assert data['status'] != 'PASS' and 'old' not in data
    assert 'Traceback' not in result.stderr


@pytest.mark.parametrize('location', ['input_file', 'input_directory', 'output_file', 'output_parent'])
def test_symlink_boundaries_fail_without_following_target(tmp_path, location):
    root = tmp_path / 'repo'; root.mkdir(); make_repo(root)
    outside = tmp_path / 'outside'; outside.mkdir()
    target = outside / 'sentinel'; target.write_text('UNCHANGED')
    output = 'receipt.json'
    if location == 'input_file':
        file = root / '.github/workflows/safe.yml'; file.unlink(); file.symlink_to(target)
    elif location == 'input_directory':
        directory = root / '.github/workflows'; (directory / 'safe.yml').unlink(); directory.rmdir(); directory.symlink_to(outside, target_is_directory=True)
    elif location == 'output_file':
        (root / output).symlink_to(target)
    else:
        (root / 'link').symlink_to(outside, target_is_directory=True); output = 'link/sentinel'
    result = cli(root, output)
    assert result.returncode != 0
    assert target.read_text() == 'UNCHANGED'


def test_output_must_not_overwrite_an_input_workflow(tmp_path):
    make_repo(tmp_path)
    target = tmp_path / '.github/workflows/safe.yml'
    before = target.read_bytes()
    assert cli(tmp_path, '.github/workflows/safe.yml').returncode != 0
    assert target.read_bytes() == before


def test_oversized_workflow_is_blocked(tmp_path):
    make_repo(tmp_path)
    (tmp_path / '.github/workflows/safe.yml').write_bytes(b'#' * 1_048_577)
    assert cli(tmp_path).returncode != 0


def test_receipt_binds_workflow_inputs_to_hashes(tmp_path):
    import hashlib
    make_repo(tmp_path)
    assert cli(tmp_path).returncode == 0
    report = json.loads((tmp_path / 'receipt.json').read_text())
    assert report['workflow_sha256']['.github/workflows/safe.yml'] == hashlib.sha256(SAFE.encode()).hexdigest()
    assert report['promotion_authorized'] is False


def test_matrix_patch_versions_are_checked_in_the_actual_job_scope():
    setup = "      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065\n        with:\n          python-version: ${{ matrix.python }}\n"
    matrix = "    strategy:\n      matrix:\n        include:\n          - python: '3.11.16'\n          - python: '3.12.14'\n"
    text = SAFE.replace('    steps:', matrix + '    steps:') + setup
    assert not blocking(text)
    assert blocking(text.replace('3.11.16', '3.11'))
    assert blocking(text.replace('matrix.python', 'inputs.python'))


def test_report_write_failure_leaves_no_previous_pass(tmp_path, monkeypatch, capsys):
    make_repo(tmp_path)
    out = tmp_path / 'receipt.json'; out.write_text('{"status":"PASS","old":true}')
    original = mod._write
    calls = []
    def fail_after_running(root, target, report):
        calls.append(report['status'])
        if len(calls) > 1:
            raise OSError('synthetic failure containing PRIVATE_DATA')
        return original(root, target, report)
    monkeypatch.setattr(mod, '_write', fail_after_running)
    assert mod.main(['--root', str(tmp_path), '--json-out', 'receipt.json']) == 2
    assert json.loads(out.read_text())['status'] == 'RUNNING'
    captured = capsys.readouterr()
    assert 'PRIVATE_DATA' not in captured.out + captured.err
    assert json.loads(captured.out)['status'] == 'BLOCKED'


def test_fifo_workflow_is_rejected_without_waiting_for_a_writer(tmp_path):
    import os
    make_repo(tmp_path)
    target = tmp_path / '.github/workflows/fifo.yml'
    os.mkfifo(target)
    assert cli(tmp_path).returncode == 2


def test_oversized_workflow_set_is_rejected(tmp_path):
    make_repo(tmp_path)
    folder = tmp_path / '.github/workflows'
    for number in range(128):
        (folder / f'item{number}.yml').write_text(SAFE)
    assert cli(tmp_path).returncode == 2


def test_block_scalar_paths_do_not_absorb_following_action_settings():
    text = SAFE + '''      - name: upload
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          path: |
            .artifacts/a.json
            .artifacts/b.json
          if-no-files-found: error
          include-hidden-files: true
          retention-days: 14
'''
    assert not blocking(text)
    assert blocking(text.replace('include-hidden-files: true', '# include-hidden-files: true'))


def test_crlf_workflows_have_equivalent_policy_results():
    assert not blocking(SAFE.replace('\n', '\r\n'))


def test_receipt_destination_is_relative_to_explicit_root_not_process_cwd(tmp_path):
    root = tmp_path / 'repo'; root.mkdir(); make_repo(root)
    result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(root), '--json-out', 'result.json'],
                            cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0
    assert (root / 'result.json').is_file()
    assert not (tmp_path / 'result.json').exists()


def test_real_workflow_policy_wiring_keeps_tests_and_source_evidence():
    path = ROOT / '.github/workflows/workflow-security.yml'
    text = path.read_text()
    assert not blocking(text)
    doc = mod._document(text)
    policy = doc.get('jobs').get('policy')
    scripts = [step.scalar('run') for step in policy.get('steps').children]
    assert any('pytest -q tests/test_workflow_security_*.py' in s for s in scripts)
    assert any('workflow_security_gate.py --json-out' in s for s in scripts)
    analyzer = doc.get('jobs').get('zizmor')
    assert analyzer is not None and not analyzer.get('if')
    assert all(step.scalar('continue-on-error') != 'true' for step in analyzer.get('steps').children)


def test_product_gauntlet_covers_the_verifiers_it_executes():
    import fnmatch
    doc = mod._document((ROOT / '.github/workflows/python-frozen-product-gauntlet.yml').read_text())
    patterns = [item.value for item in doc.get('on').get('pull_request').get('paths').children]
    for path in ['scripts/local_verify.py', 'scripts/verify_node_lock.py',
                 'scripts/workflow_security_gate.py', 'tests/test_workflow_security_boundaries.py']:
        assert any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns), path
    jobs = doc.get('jobs')
    assert {j.key for j in jobs.children} >= {'product-e2e', 'offline-replay'}
    recovery = '\n'.join(step.scalar('run') for step in jobs.get('offline-replay').get('steps').children)
    assert recovery.index('rm -f') < recovery.index('scripts/studio_replay_verify.py')
