from pathlib import Path

from scripts.security_static import scan_repository


def _scan(tmp_path: Path, name: str, content: str):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return scan_repository((path,), root=tmp_path)


def test_detects_subprocess_shell_true(tmp_path):
    findings = _scan(
        tmp_path,
        "bad.py",
        "import subprocess\nsubprocess.run('echo hi', shell=True)\n",
    )
    assert [item.rule for item in findings] == ["PY_SUBPROCESS_SHELL_TRUE"]


def test_detects_dynamic_eval(tmp_path):
    findings = _scan(tmp_path, "bad.py", "value = eval(user_input)\n")
    assert [item.rule for item in findings] == ["PY_DYNAMIC_EVAL"]


def test_detects_high_confidence_secret(tmp_path):
    token = "ghp_" + "A" * 32
    findings = _scan(tmp_path, "config.txt", f"TOKEN={token}\n")
    assert [item.rule for item in findings] == ["SECRET_GITHUB_TOKEN"]


def test_allows_argv_subprocess_without_shell(tmp_path):
    findings = _scan(
        tmp_path,
        "safe.py",
        "import subprocess\nsubprocess.run(['ffprobe', '--version'], check=True)\n",
    )
    assert findings == ()


def test_findings_are_deterministic_and_sorted(tmp_path):
    _scan(tmp_path, "b.py", "exec(code)\n")
    _scan(tmp_path, "a.py", "eval(code)\n")
    first = scan_repository((tmp_path,), root=tmp_path)
    second = scan_repository((tmp_path,), root=tmp_path)
    assert first == second
    assert [item.path for item in first] == sorted(item.path for item in first)


def test_current_repo_high_signal_baseline_is_clean():
    findings = scan_repository((Path("src"), Path("scripts"), Path("config"), Path(".github"), Path("runtime")))
    assert findings == (), "high-signal security findings must be resolved or explicitly redesigned before promotion"
