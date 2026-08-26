from pathlib import Path

from scripts.build_remotion_runtime_fixture import build_doc
from src.compilers.remotion import compile_remotion_scene_spec, validate_scene_coverage


def test_runtime_fixture_is_compiler_derived_and_exact_coverage():
    doc = build_doc()
    spec = compile_remotion_scene_spec(doc)
    assert validate_scene_coverage(spec) == []
    assert spec["project"] == {"fps": 30, "width": 640, "height": 360, "duration_frames": 90}
    assert [s["id"] for s in spec["scenes"]] == ["S01", "S02", "S03"]
    assert [s["from"] for s in spec["scenes"]] == [0, 30, 60]
    assert sum(s["durationInFrames"] for s in spec["scenes"]) == 90
    assert sum(len(s["events"]) for s in spec["scenes"]) == 3
    assert spec["scenes"][1]["camera"]["motion"] == "linear_slide"
    assert spec["scenes"][2]["transition"]["type"] == "match_move"
