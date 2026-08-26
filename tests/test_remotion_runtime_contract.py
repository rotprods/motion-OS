import pytest

from scripts.build_remotion_runtime_fixture import build_doc
from scripts.verify_remotion_render import verify_probe
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


def _probe(*, duration: float = 3.050667, frames: str | None = "90") -> dict:
    return {
        "streams": [
            {
                "codec_type": "video",
                "width": 640,
                "height": 360,
                "r_frame_rate": "30/1",
                "avg_frame_rate": "30/1",
                "nb_frames": frames,
                "nb_read_frames": frames,
            },
            {"codec_type": "audio"},
        ],
        "format": {"duration": str(duration), "size": "282119"},
    }


def test_mux_audio_padding_does_not_invalidate_exact_visual_timeline():
    spec = compile_remotion_scene_spec(build_doc())
    report = verify_probe(spec, _probe(), video_bytes=282119, video_sha256="a" * 64)
    assert report["technical_runtime_gate"] == "PASS"
    assert report["observed"]["duration_frames"] == 90
    assert report["observed"]["visual_duration_s"] == 3.0
    assert report["observed"]["container_duration_s"] == pytest.approx(3.050667)
    assert report["observed"]["mux_tail_padding_s"] == pytest.approx(0.050667)


def test_excessive_mux_tail_is_rejected_without_weakening_visual_contract():
    spec = compile_remotion_scene_spec(build_doc())
    report = verify_probe(spec, _probe(duration=3.25), video_bytes=1, video_sha256="b" * 64)
    assert report["technical_runtime_gate"] == "FAIL"
    assert any(error.startswith("mux_tail_padding:") for error in report["errors"])


def test_missing_authoritative_frame_count_is_fail_closed():
    spec = compile_remotion_scene_spec(build_doc())
    report = verify_probe(spec, _probe(frames=None), video_bytes=1, video_sha256="c" * 64)
    assert report["technical_runtime_gate"] == "FAIL"
    assert "frames:unavailable" in report["errors"]
