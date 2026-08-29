from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from scripts.validate_v2_architecture import validate_package


ROOT = Path(__file__).resolve().parents[1]


def _copy_v2(tmp_path: Path) -> Path:
    for rel in ("architecture/v2", "state/v2"):
        src = ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
    return tmp_path


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_current_v2_package_is_internally_consistent():
    result = validate_package(ROOT)
    assert result["status"] == "PASS"
    assert result["source_main_sha"] == "a8d7dbddaeb4ad9779df9883d3cf4e4f6ea4f29d"


def test_dangling_hypergraph_edge_fails_closed(tmp_path: Path):
    root = _copy_v2(tmp_path)
    path = root / "architecture/v2/hypergraph.snapshot.json"
    payload = _json(path)
    payload["edges"].append({"from": "missing:node", "type": "BLOCKS", "to": "project:motion-os"})
    _write(path, payload)
    with pytest.raises(ValueError, match="dangling edge"):
        validate_package(root)


def test_duplicate_graph_identity_fails_closed(tmp_path: Path):
    root = _copy_v2(tmp_path)
    path = root / "architecture/v2/hypergraph.snapshot.json"
    payload = _json(path)
    payload["nodes"].append(dict(payload["nodes"][0]))
    _write(path, payload)
    with pytest.raises(ValueError, match="duplicate node ids"):
        validate_package(root)


def test_task_dependency_cycle_fails_closed(tmp_path: Path):
    root = _copy_v2(tmp_path)
    path = root / "state/v2/tasks.json"
    payload = _json(path)
    payload["tasks"][0]["depends_on"] = [payload["tasks"][1]["id"]]
    payload["tasks"][1]["depends_on"] = [payload["tasks"][0]["id"]]
    _write(path, payload)
    with pytest.raises(ValueError, match="dependency cycle"):
        validate_package(root)


def test_missing_task_dependency_fails_closed(tmp_path: Path):
    root = _copy_v2(tmp_path)
    path = root / "state/v2/tasks.json"
    payload = _json(path)
    payload["tasks"][0]["depends_on"] = ["V2-DOES-NOT-EXIST"]
    _write(path, payload)
    with pytest.raises(ValueError, match="missing dependencies"):
        validate_package(root)


def test_checkpoint_set_cannot_silently_drop_production_gate(tmp_path: Path):
    root = _copy_v2(tmp_path)
    path = root / "state/v2/checkpoint.json"
    payload = _json(path)
    payload["checkpoint_states"].pop("CP14")
    _write(path, payload)
    with pytest.raises(ValueError, match="checkpoint set mismatch"):
        validate_package(root)


def test_v2_state_cannot_self_promote_release(tmp_path: Path):
    root = _copy_v2(tmp_path)
    path = root / "state/v2/project-state.json"
    payload = _json(path)
    payload["release_state"] = "VERIFIED"
    _write(path, payload)
    with pytest.raises(ValueError, match="must remain BLOCKED"):
        validate_package(root)
