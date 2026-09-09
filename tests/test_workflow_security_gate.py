from __future__ import annotations

from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "workflow_security_gate.py"
spec = importlib.util.spec_from_file_location("workflow_security_gate", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

PIN_CHECKOUT = "11d5960a326750d5838078e36cf38b85af677262"
PIN_PYTHON = "a26af69be951a213d495a4c3e4e4022e16d87065"
PIN_UPLOAD = "ea165f8d65b6e75b540449e92b4886f43607fa02"


def safe_workflow(extra_steps: str = "") -> str:
    return f"""name: safe
on:\n  pull_request:\npermissions:\n  contents: read\njobs:\n  test:\n    runs-on: ubuntu-24.04\n    timeout-minutes: 10\n    steps:\n      - uses: actions/checkout@{PIN_CHECKOUT}\n        with:\n          persist-credentials: false\n      - uses: actions/setup-python@{PIN_PYTHON}\n        with:\n          python-version: '3.12.14'\n      - run: python -V\n{extra_steps}"""


def codes(text: str) -> set[str]:
    return {finding.code for finding in mod.audit_text(".github/workflows/test.yml", text)}


def test_safe_workflow_has_no_blocking_findings():
    findings = mod.audit_text(".github/workflows/test.yml", safe_workflow())
    assert not [finding for finding in findings if finding.severity in {"P0", "P1"}]


def test_unpinned_action_fails():
    assert "UNPINNED_ACTION" in codes(safe_workflow().replace(f"actions/checkout@{PIN_CHECKOUT}", "actions/checkout@v4"))


def test_checkout_must_disable_persistent_credentials():
    assert "CHECKOUT_PERSISTS_CREDENTIALS" in codes(safe_workflow().replace("          persist-credentials: false\n", ""))


def test_workflow_requires_explicit_permissions():
    assert "MISSING_EXPLICIT_PERMISSIONS" in codes(safe_workflow().replace("permissions:\n  contents: read\n", ""))


def test_write_token_permission_fails():
    assert "WRITE_TOKEN_PERMISSION" in codes(safe_workflow().replace("contents: read", "contents: write"))


def test_pull_request_target_fails():
    assert "PRIVILEGED_UNTRUSTED_TRIGGER" in codes(safe_workflow().replace("  pull_request:", "  pull_request_target:"))


def test_latest_runner_fails():
    assert "FLOATING_RUNNER_IMAGE" in codes(safe_workflow().replace("ubuntu-24.04", "ubuntu-latest"))


def test_python_minor_only_fails():
    assert "FLOATING_PYTHON_VERSION" in codes(safe_workflow().replace("3.12.14", "3.12"))


def test_node_major_only_fails():
    text = safe_workflow("      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020\n        with:\n          node-version: '22'\n")
    assert "FLOATING_NODE_VERSION" in codes(text)


def test_latest_pip_upgrade_fails():
    assert "FLOATING_PIP_UPGRADE" in codes(safe_workflow("      - run: python -m pip install --upgrade pip\n"))


def test_editable_project_install_bypasses_frozen_contract():
    assert "BYPASS_FROZEN_PYTHON_ENV" in codes(safe_workflow("      - run: pip install -e '.[dev]'\n"))


def test_unpinned_pip_audit_install_bypasses_frozen_contract():
    assert "BYPASS_FROZEN_PYTHON_ENV" in codes(safe_workflow("      - run: pip install pip-audit\n"))


def test_continue_on_error_fails():
    assert "CONTINUE_ON_ERROR" in codes(safe_workflow("      - run: false\n        continue-on-error: true\n"))


def test_job_without_timeout_fails():
    assert "JOB_TIMEOUT_MISSING" in codes(safe_workflow().replace("    timeout-minutes: 10\n", ""))


def test_direct_untrusted_event_context_in_shell_fails():
    text = safe_workflow("      - run: echo '${{ github.event.pull_request.title }}'\n")
    assert "UNTRUSTED_CONTEXT_IN_SHELL" in codes(text)


def test_untrusted_context_via_env_is_not_source_interpolation_in_run():
    text = safe_workflow("      - name: env-safe\n        env:\n          TITLE: ${{ github.event.pull_request.title }}\n        run: printf '%s\\n' \"$TITLE\"\n")
    assert "UNTRUSTED_CONTEXT_IN_SHELL" not in codes(text)


def test_artifact_upload_must_fail_closed_and_include_hidden_files():
    text = safe_workflow(
        f"      - uses: actions/upload-artifact@{PIN_UPLOAD}\n"
        "        if: always()\n"
        "        with:\n"
        "          name: evidence\n"
        "          path: .artifacts/report.json\n"
        "          if-no-files-found: warn\n"
        "          retention-days: 7\n"
    )
    found = codes(text)
    assert "EVIDENCE_UPLOAD_WARN" in found
    assert "EVIDENCE_UPLOAD_NOT_FAIL_CLOSED" in found
    assert "HIDDEN_EVIDENCE_EXCLUDED" in found


def test_safe_evidence_upload_passes_policy():
    text = safe_workflow(
        f"      - uses: actions/upload-artifact@{PIN_UPLOAD}\n"
        "        if: always()\n"
        "        with:\n"
        "          name: evidence\n"
        "          path: .artifacts/report.json\n"
        "          if-no-files-found: error\n"
        "          include-hidden-files: true\n"
        "          retention-days: 7\n"
    )
    found = codes(text)
    assert "EVIDENCE_UPLOAD_NOT_FAIL_CLOSED" not in found
    assert "HIDDEN_EVIDENCE_EXCLUDED" not in found


def test_unpinned_apt_package_is_visible_residual_not_p1():
    findings = mod.audit_text(".github/workflows/test.yml", safe_workflow("      - run: sudo apt-get install -y ffmpeg\n"))
    apt = [finding for finding in findings if finding.code == "UNPINNED_OS_PACKAGE"]
    assert len(apt) == 1
    assert apt[0].severity == "P2"
