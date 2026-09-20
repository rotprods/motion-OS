import math

import pytest

from src.compilers.remotion import emit_remotion_typescript


def _doc(camera=None):
    return {
        "compiler_targets": {
            "remotion": {
                "project": {"fps": 30, "width": 1080, "height": 1920, "duration_frames": 30},
                "z_order": ["foreground"],
                "scene_boundaries": [{"shot_id": "shot-1", "from_frame": 0, "to_frame": 29}],
            }
        },
        "shots": [
            {
                "id": "shot-1",
                "camera_plan": camera if camera is not None else {"type": "static"},
                "depth_plan": {"layers": 1},
                "transition_spec": {"type": "cut"},
                "micro_choreography": [],
            }
        ],
    }


@pytest.mark.parametrize(
    "name",
    ["x; globalThis.PWNED = true; const y", "class", "1bad", "bad-name", ""],
)
def test_remotion_typescript_rejects_injected_or_invalid_const_names(name):
    with pytest.raises(ValueError, match="TypeScript identifier"):
        emit_remotion_typescript(_doc(), const_name=name)


def test_remotion_typescript_escapes_javascript_line_separator_data():
    source = emit_remotion_typescript(_doc(camera={"note": "left\u2028right"}))
    assert "left\\u2028right" in source
    assert "left\u2028right" not in source


def test_remotion_typescript_rejects_nonfinite_json_values():
    with pytest.raises(ValueError):
        emit_remotion_typescript(_doc(camera={"zoom": math.nan}))
