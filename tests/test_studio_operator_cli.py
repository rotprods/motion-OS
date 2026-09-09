from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

import scripts.studio_execute as studio_execute
import scripts.studio_prepare as studio_prepare


ROOT = Path(__file__).resolve().parents[1]


def _run_isolated_help(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-S", script, "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_prepare_cli_bootstraps_repo_without_site_packages():
    completed = _run_isolated_help("scripts/studio_prepare.py")
    assert completed.returncode == 0, completed.stderr
    assert "--manifest" in completed.stdout
    assert "--runtime-spec-out" in completed.stdout


def test_execute_cli_bootstraps_repo_without_site_packages():
    completed = _run_isolated_help("scripts/studio_execute.py")
    assert completed.returncode == 0, completed.stderr
    assert "--manifest" in completed.stdout
    assert "--handoff" in completed.stdout


def test_prepare_publishes_authoritative_bundle_last(monkeypatch, tmp_path: Path):
    out = tmp_path / "bundle.json"
    runtime_spec = tmp_path / "runtimeSpec.json"
    graph = tmp_path / "graph.json"
    out.write_text("stale", encoding="utf-8")
    calls: list[Path] = []

    def record_write(path: Path, value: object) -> None:
        assert not out.exists(), "stale authoritative bundle must be invalidated before persistence"
        calls.append(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    monkeypatch.setattr(studio_prepare, "_write_atomic", record_write)
    studio_prepare._persist_outputs(
        {"runtime_spec": {"fps": 30}, "graph": {"nodes": []}},
        out=out,
        runtime_spec_out=runtime_spec,
        graph_out=graph,
    )

    assert calls == [runtime_spec, graph, out]
    assert out.is_file()


def test_prepare_sidecar_failure_cannot_leave_authoritative_bundle(monkeypatch, tmp_path: Path):
    out = tmp_path / "bundle.json"
    runtime_spec = tmp_path / "runtimeSpec.json"
    out.write_text("stale", encoding="utf-8")

    def fail_sidecar(path: Path, value: object) -> None:
        raise OSError("simulated sidecar failure")

    monkeypatch.setattr(studio_prepare, "_write_atomic", fail_sidecar)
    with pytest.raises(OSError, match="simulated sidecar failure"):
        studio_prepare._persist_outputs(
            {"runtime_spec": {}, "graph": {}},
            out=out,
            runtime_spec_out=runtime_spec,
            graph_out=None,
        )

    assert not out.exists()


def test_prepare_invalidates_stale_bundle_before_input_failure(monkeypatch, tmp_path: Path):
    out = tmp_path / "bundle.json"
    out.write_text("stale", encoding="utf-8")
    missing_manifest = tmp_path / "missing-manifest.json"
    missing_handoff = tmp_path / "missing-handoff.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "studio_prepare.py",
            "--manifest",
            str(missing_manifest),
            "--handoff",
            str(missing_handoff),
            "--out",
            str(out),
        ],
    )

    with pytest.raises(FileNotFoundError):
        studio_prepare.main()
    assert not out.exists()


def test_execute_invalidates_stale_report_before_input_failure(monkeypatch, tmp_path: Path):
    out = tmp_path / "authorization.json"
    out.write_text("stale", encoding="utf-8")
    missing_manifest = tmp_path / "missing-manifest.json"
    missing_handoff = tmp_path / "missing-handoff.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "studio_execute.py",
            "--manifest",
            str(missing_manifest),
            "--handoff",
            str(missing_handoff),
            "--out",
            str(out),
        ],
    )

    with pytest.raises(FileNotFoundError):
        studio_execute.main()
    assert not out.exists()


def test_atomic_writes_leave_no_temp_files(tmp_path: Path):
    prepare_out = tmp_path / "prepare.json"
    execute_out = tmp_path / "execute.json"

    studio_prepare._write_atomic(prepare_out, {"ok": True})
    studio_execute._write_atomic(execute_out, '{"ok": true}\n')

    assert json.loads(prepare_out.read_text(encoding="utf-8")) == {"ok": True}
    assert json.loads(execute_out.read_text(encoding="utf-8")) == {"ok": True}
    assert list(tmp_path.glob("*.tmp")) == []
    assert list(tmp_path.glob(".*.tmp")) == []
