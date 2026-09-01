from __future__ import annotations

import importlib.util
from pathlib import Path
import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "qualify_s04_9d.py"
spec = importlib.util.spec_from_file_location("qualify_s04_9d", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

HEAD = "0" * 64
DIGEST = "sha256:" + "1" * 64


def measurement(iou=0.95, centroid=1.0, area=2.0, onset=0.5):
    metric = {
        "mean_bbox_iou": iou,
        "mean_centroid_error_px": centroid,
        "mean_area_error_pct": area,
        "temporal_visibility_exact": True,
    }
    return {
        "source": {"sha256": "2" * 64, "fps": 30, "frame_count": 71},
        "component_metrics": {"setup": dict(metric), "hero": dict(metric), "tail": dict(metric)},
        "audio": {"absolute_error_frames": onset},
    }


def test_closes_measured_p1_but_never_self_promotes_full_fidelity():
    result = mod.build_qualification(measurement(), renderer_head=HEAD, artifact_id=7, artifact_digest=DIGEST)
    assert result["p0_p1_measured_repair_closed"] is True
    assert result["authority_state"] == "SOURCE_BOUND_PARTIAL_QUALIFICATION_P0P1_CLOSED"
    assert result["full_9d_fidelity_validated"] is False
    assert result["dimensions"]["typography"]["exact_font_identity"] == "UNKNOWN"
    assert result["dimensions"]["camera"]["state"] == "BLOCKED_SOURCE_LAYER_LIMIT"


@pytest.mark.parametrize("field,value", [("iou", 0.89), ("centroid", 3.01), ("area", 8.01), ("onset", 1.51)])
def test_any_hard_measured_gate_prevents_p1_closure(field, value):
    kwargs = {"iou": 0.95, "centroid": 1.0, "area": 2.0, "onset": 0.5}
    kwargs[field] = value
    result = mod.build_qualification(measurement(**kwargs), renderer_head=HEAD, artifact_id=7, artifact_digest=DIGEST)
    assert result["p0_p1_measured_repair_closed"] is False
    assert result["authority_state"] == "SOURCE_BOUND_DEFECTS_REMAIN"


def test_rejects_ambiguous_identity_inputs():
    with pytest.raises(ValueError):
        mod.build_qualification(measurement(), renderer_head="abc", artifact_id=7, artifact_digest=DIGEST)
    with pytest.raises(ValueError):
        mod.build_qualification(measurement(), renderer_head=HEAD, artifact_id=True, artifact_digest=DIGEST)
    with pytest.raises(ValueError):
        mod.build_qualification(measurement(), renderer_head=HEAD, artifact_id=7, artifact_digest="sha256:nope")
