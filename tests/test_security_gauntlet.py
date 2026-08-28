from pathlib import Path

from scripts.security_gauntlet import run_gauntlet


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_clean_repo_passes(tmp_path: Path):
    _write(tmp_path, "src/ok.py", "def add(a, b):\n    return a + b\n")
    _write(tmp_path, ".github/workflows/ci.yml", "steps:\n  - uses: actions/checkout@" + "a" * 40 + "\n")
    report = run_gauntlet(tmp_path)
    assert report["status"] == "PASS"
    assert report["blocker_count"] == 0


def test_eval_exec_and_os_system_fail_closed(tmp_path: Path):
    _write(tmp_path, "src/bad.py", "import os\neval('1+1')\nexec('x=1')\nos.system('echo nope')\n")
    report = run_gauntlet(tmp_path)
    ids = {item["rule_id"] for item in report["findings"]}
    assert report["status"] == "FAIL"
    assert {"PY-EVAL", "PY-EXEC", "PY-OS-SYSTEM"} <= ids


def test_subprocess_shell_true_fails_but_argv_run_is_allowed(tmp_path: Path):
    _write(tmp_path, "src/bad.py", "import subprocess\nsubprocess.run(['echo', 'ok'])\nsubprocess.run('echo bad', shell=True)\n")
    report = run_gauntlet(tmp_path)
    assert report["status"] == "FAIL"
    assert any(item["rule_id"] == "PY-SUBPROCESS-SHELL" for item in report["findings"])


def test_dynamic_shell_flag_requires_review(tmp_path: Path):
    _write(tmp_path, "src/review.py", "import subprocess\ndef f(flag):\n    subprocess.run(['echo'], shell=flag)\n")
    report = run_gauntlet(tmp_path)
    assert report["status"] == "PASS"
    assert any(item["rule_id"] == "PY-SUBPROCESS-SHELL-DYNAMIC" and item["severity"] == "MEDIUM" for item in report["findings"])


def test_mutable_github_action_ref_fails(tmp_path: Path):
    _write(tmp_path, ".github/workflows/ci.yml", "steps:\n  - uses: actions/checkout@v4\n")
    report = run_gauntlet(tmp_path)
    assert report["status"] == "FAIL"
    assert any(item["rule_id"] == "GH-ACTION-MUTABLE-REF" for item in report["findings"])


def test_local_and_docker_actions_are_not_forced_to_git_sha(tmp_path: Path):
    _write(tmp_path, ".github/workflows/ci.yml", "steps:\n  - uses: ./local-action\n  - uses: docker://alpine:3.20\n")
    assert run_gauntlet(tmp_path)["status"] == "PASS"


def test_credential_like_material_fails(tmp_path: Path):
    token = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz123456"
    _write(tmp_path, "docs/leak.md", f"token = {token}\n")
    report = run_gauntlet(tmp_path)
    assert report["status"] == "FAIL"
    assert any(item["rule_id"] == "SECRET-GITHUB" for item in report["findings"])


def test_pickle_and_unsafe_yaml_fail(tmp_path: Path):
    _write(tmp_path, "src/bad.py", "import pickle\nimport yaml\npickle.loads(b'abc')\nyaml.load('x')\n")
    report = run_gauntlet(tmp_path)
    ids = {item["rule_id"] for item in report["findings"]}
    assert report["status"] == "FAIL"
    assert {"PY-PICKLE", "PY-YAML-LOAD"} <= ids
