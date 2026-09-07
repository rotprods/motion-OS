from __future__ import annotations

from copy import deepcopy
from itertools import product
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from scripts.merge_safe_gate import FLAGS, JOBS, MAX_INPUT_CHARS, evaluate_gate

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/merge_safe_gate.py"
WORKFLOW = ROOT / ".github/workflows/merge-gate.yml"


def sample(*, full: bool = False) -> dict:
    needs = {job: {"result": "success"} for job in JOBS}
    needs["classify"]["outputs"] = {flag: str(full).lower() for flag in FLAGS}
    if not full:
        for job in JOBS[2:]:
            needs[job]["result"] = "skipped"
    return needs


def run_cli(raw: str, event: str = "pull_request") -> subprocess.CompletedProcess:
    env = {**os.environ, "MERGE_SAFE_NEEDS_JSON": raw, "MERGE_SAFE_EVENT_NAME": event}
    return subprocess.run(
        [sys.executable, str(SCRIPT)], env=env, cwd=ROOT,
        text=True, capture_output=True, timeout=10,
    )


@pytest.mark.parametrize("event", ["pull_request", "merge_group", "workflow_dispatch"])
def test_full_success_is_accepted(event):
    assert evaluate_gate(sample(full=True), event)["status"] == "PASS"


def test_selective_pr_accepts_only_justified_skips():
    assert evaluate_gate(sample(), "pull_request")["status"] == "PASS"


@pytest.mark.parametrize("job", JOBS)
@pytest.mark.parametrize("result", ["skipped", "failure", "cancelled"])
def test_required_job_must_succeed(job, result):
    needs = sample(full=True)
    needs[job]["result"] = result
    assert f"required_job_not_success:{job}" in evaluate_gate(needs, "pull_request")["errors"]


@pytest.mark.parametrize("flag,job", [("full", "compat311"), ("analysis", "analysis"),
                                     ("remotion", "remotion"), ("security", "security")])
def test_selected_job_cannot_disappear(flag, job):
    needs = sample()
    needs["classify"]["outputs"][flag] = "true"
    assert f"required_job_not_success:{job}" in evaluate_gate(needs, "pull_request")["errors"]


@pytest.mark.parametrize("flag", FLAGS)
@pytest.mark.parametrize("value", [None, True, False, 0, 1, [], {}, "", "TRUE", "false ", "yes"])
def test_outputs_require_exact_boolean_strings(flag, value):
    needs = sample(full=True)
    needs["classify"]["outputs"][flag] = value
    assert f"classification_flag_invalid:{flag}" in evaluate_gate(needs, "pull_request")["errors"]


@pytest.mark.parametrize("flag", FLAGS)
def test_missing_output_is_not_an_implicit_false(flag):
    needs = sample(full=True)
    del needs["classify"]["outputs"][flag]
    assert evaluate_gate(needs, "pull_request")["status"] == "FAIL"


@pytest.mark.parametrize("outputs", [None, [], True, "true"])
def test_invalid_outputs_object(outputs):
    needs = sample(full=True)
    needs["classify"]["outputs"] = outputs
    assert "classification_outputs_missing_or_invalid" in evaluate_gate(needs, "pull_request")["errors"]


@pytest.mark.parametrize("job", JOBS)
def test_missing_job_fails_even_when_not_selected(job):
    needs = sample()
    del needs[job]
    assert "needs_job_set_mismatch" in evaluate_gate(needs, "pull_request")["errors"]


def test_new_dependency_requires_explicit_policy_review():
    needs = sample(full=True)
    needs["unreviewed"] = {"result": "success"}
    assert "needs_job_set_mismatch" in evaluate_gate(needs, "pull_request")["errors"]


@pytest.mark.parametrize("value", [None, [], True, "success"])
def test_invalid_job_nodes(value):
    needs = sample(full=True)
    needs["quick"] = value
    assert "job_missing_or_invalid:quick" in evaluate_gate(needs, "pull_request")["errors"]


@pytest.mark.parametrize("value", [None, [], {}, True, 1, "neutral", "SUCCESS", "success "])
def test_invalid_result_values(value):
    needs = sample(full=True)
    needs["quick"]["result"] = value
    assert "job_result_invalid:quick" in evaluate_gate(needs, "pull_request")["errors"]


@pytest.mark.parametrize("value", [None, [], True, "{}"])
def test_invalid_needs_top_level(value):
    assert "needs_must_be_object" in evaluate_gate(value, "pull_request")["errors"]


@pytest.mark.parametrize("event", [None, [], True, "", "push", "pull_request_target"])
def test_unknown_event_cannot_authorize_success(event):
    assert "event_not_supported" in evaluate_gate(sample(full=True), event)["errors"]


@pytest.mark.parametrize("event", ["merge_group", "workflow_dispatch"])
def test_full_event_cannot_be_downgraded_to_selective(event):
    assert "event_requires_full_verification" in evaluate_gate(sample(), event)["errors"]


def test_full_output_requires_all_expensive_flags():
    needs = sample(full=True)
    needs["classify"]["outputs"]["analysis"] = "false"
    assert "full_classification_inconsistent" in evaluate_gate(needs, "pull_request")["errors"]


def test_optional_job_failure_never_gets_hidden():
    needs = sample()
    needs["security"]["result"] = "failure"
    assert "optional_job_not_success_or_skipped:security" in evaluate_gate(needs, "pull_request")["errors"]


def test_deterministic_pure_verdict():
    needs = sample()
    before = deepcopy(needs)
    assert evaluate_gate(needs, "pull_request") == evaluate_gate(needs, "pull_request")
    assert needs == before


def test_complete_result_flag_event_truth_table():
    # 4**6 result combinations * 2**4 flag combinations * 3 event types.
    # The oracle is an independent logical formula, not a copy of the implementation.
    checked = 0
    for bits in product([False, True], repeat=4):
        full, analysis, remotion, security = bits
        required = (True, True, full, analysis, remotion, security)
        coherent = not full or (analysis and remotion and security)
        for states in product(["success", "skipped", "failure", "cancelled"], repeat=6):
            needs = {job: {"result": state} for job, state in zip(JOBS, states)}
            needs["classify"]["outputs"] = dict(zip(FLAGS, [str(bit).lower() for bit in bits]))
            jobs_ok = all(state == "success" if needed else state in ("success", "skipped")
                          for state, needed in zip(states, required))
            for event in ("pull_request", "merge_group", "workflow_dispatch"):
                expected = coherent and jobs_ok and (event == "pull_request" or all(bits))
                assert (evaluate_gate(needs, event)["status"] == "PASS") == expected
                checked += 1
    assert checked == 196_608


@pytest.mark.parametrize("raw", ["", "{", "null", "[]", '{"x":NaN}', '{"x":Infinity}',
                                  '{"x":1,"x":2}', "[" * 2000 + "]" * 2000])
def test_cli_rejects_malformed_or_non_object_payload(raw):
    result = run_cli(raw)
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "FAIL"
    assert "Traceback" not in result.stderr


def test_cli_rejects_duplicate_key_even_when_final_value_would_pass():
    needs = sample(full=True)
    raw = json.dumps(needs).replace('"quick": {"result": "success"}',
                                    '"quick": {"result": "skipped", "result": "success"}')
    result = run_cli(raw)
    assert result.returncode == 1
    assert json.loads(result.stdout)["errors"] == ["needs_json_invalid"]


def test_cli_never_reflects_untrusted_text():
    needs = sample(full=True)
    marker = "DO_NOT_LOG_PRIVATE_PAYLOAD_42\n::error::forged"
    needs["quick"]["result"] = marker
    result = run_cli(json.dumps(needs))
    assert result.returncode == 1
    assert marker not in result.stdout + result.stderr
    assert "DO_NOT_LOG_PRIVATE_PAYLOAD_42" not in result.stdout + result.stderr


def test_cli_rejects_oversized_input_without_logging_it():
    result = run_cli(" " * (MAX_INPUT_CHARS + 1))
    assert result.returncode == 1
    assert json.loads(result.stdout)["errors"] == ["needs_json_invalid"]


def test_cli_green_and_red_exit_codes():
    good = run_cli(json.dumps(sample(full=True)), "merge_group")
    bad_needs = sample(full=True)
    bad_needs["quick"]["result"] = "skipped"
    bad = run_cli(json.dumps(bad_needs), "merge_group")
    assert good.returncode == 0
    assert json.loads(good.stdout)["status"] == "PASS"
    assert bad.returncode == 1
    assert json.loads(bad.stdout)["status"] == "FAIL"


def test_workflow_uses_one_gate_and_actual_needs_as_data():
    # Bounded wiring regression, not a replacement for an Actions YAML linter.
    text = WORKFLOW.read_text(encoding="utf-8")
    gate = text.split("\n  merge-safe:\n", 1)[1]
    assert "    if: always()" in gate
    declared = re.search(r"^    needs: \[([^\]]+)\]$", gate, re.MULTILINE)
    assert declared is not None
    assert tuple(item.strip() for item in declared[1].split(",")) == JOBS
    assert "MERGE_SAFE_NEEDS_JSON: ${{ toJSON(needs) }}" in gate
    assert "MERGE_SAFE_EVENT_NAME: ${{ github.event_name }}" in gate
    assert "python3 scripts/merge_safe_gate.py | tee .artifacts/merge-safe-verdict.json" in gate
    assert "set -euo pipefail" in gate
    assert "if-no-files-found: error" in gate
    assert "persist-credentials: false" in gate
    assert "continue-on-error" not in gate
    assert "python - <<" not in gate
    assert "'success','skipped'" not in gate


@pytest.mark.parametrize("path", ["scripts/merge_safe_gate.py", "tests/test_merge_safe_gate.py",
                                  ".github/workflows/merge-gate.yml"])
def test_policy_changes_force_all_existing_gates(path):
    from scripts.change_impact import classify
    assert classify([path]) == {"analysis": True, "remotion": True, "security": True, "full": True}


def test_classifier_outputs_round_trip_into_verdict(tmp_path):
    output = tmp_path / "github-output"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/change_impact.py"), "scripts/merge_safe_gate.py",
         "--github-output", str(output)],
        text=True, capture_output=True, check=True, timeout=10,
    )
    flags = dict(line.split("=", 1) for line in output.read_text().splitlines())
    needs = sample(full=True)
    needs["classify"]["outputs"] = flags
    assert evaluate_gate(needs, "pull_request")["status"] == "PASS"
    needs["security"]["result"] = "skipped"
    assert evaluate_gate(needs, "pull_request")["status"] == "FAIL"


@pytest.mark.parametrize("case", ["valid_selective", "classify_skipped", "quick_skipped",
                                  "required_security_skipped", "full_optional_skipped",
                                  "missing_outputs"])
def test_actual_workflow_shell_preserves_verdict_and_exit(case, tmp_path):
    import shutil
    import textwrap
    gate = WORKFLOW.read_text().split("\n  merge-safe:\n", 1)[1]
    shell = textwrap.dedent(gate.split("        run: |\n", 1)[1].split("\n      - uses:", 1)[0])
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(SCRIPT, tmp_path / "scripts/merge_safe_gate.py")
    needs = sample(full=case != "valid_selective")
    if case == "classify_skipped":
        needs["classify"]["result"] = "skipped"
    elif case == "quick_skipped":
        needs["quick"]["result"] = "skipped"
    elif case == "required_security_skipped":
        needs["security"]["result"] = "skipped"
    elif case == "full_optional_skipped":
        for job in JOBS[2:]:
            needs[job]["result"] = "skipped"
    elif case == "missing_outputs":
        del needs["classify"]["outputs"]
    env = {**os.environ, "MERGE_SAFE_NEEDS_JSON": json.dumps(needs),
           "MERGE_SAFE_EVENT_NAME": "pull_request"}
    result = subprocess.run(["bash", "-c", shell], cwd=tmp_path, env=env,
                            text=True, capture_output=True, timeout=10)
    should_pass = case == "valid_selective"
    assert result.returncode == (0 if should_pass else 1)
    evidence = json.loads((tmp_path / ".artifacts/merge-safe-verdict.json").read_text())
    assert evidence["status"] == ("PASS" if should_pass else "FAIL")
