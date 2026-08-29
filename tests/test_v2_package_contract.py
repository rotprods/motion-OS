from __future__ import annotations

import json
from pathlib import Path
import shutil

from scripts.validate_v2_package import validate

ROOT = Path(__file__).resolve().parents[1]


def _copy(tmp_path: Path) -> Path:
    for rel in ("architecture/v2", "plans/v2", "graph/v2", "state/v2", "schemas"):
        src = ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst)
    return tmp_path


def test_v2_package_is_valid():
    assert validate(ROOT) == []


def test_v2_package_fails_closed_on_task_cycle(tmp_path: Path):
    root = _copy(tmp_path)
    path = root / "state/v2/task_dag.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    a = payload["tasks"][0]
    b = payload["tasks"][1]
    a["depends_on"] = [b["id"]]
    b["depends_on"] = [a["id"]]
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert any(item.startswith("dag:cycle:") for item in validate(root))


def test_v2_package_cannot_self_promote(tmp_path: Path):
    root = _copy(tmp_path)
    path = root / "state/v2/v2_state.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["promotion"]["blocked"] = False
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert "authority:v2_state_must_remain_blocked_before_cp14" in validate(root)
