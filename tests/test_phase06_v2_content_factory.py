from src.content.content_factory import (
    AngleCandidate, HookCandidate, Beat, choose_primary_driver, rank_angles,
    rank_hooks, build_retention_beats, stable_beat_ids, estimate_duration,
    compile_tts_text, preflight_manifest,
)
from src.avatar.heygen_adapter import compile_request, ingest_render_telemetry
from src.content.performance_learning import PerformanceRecord, attach_attribution

PROFILE = {
    "look_id":"look","voice_id":"voice","aspect_ratio":"9:16","resolution":"1080p",
    "output_format":"mp4","expressiveness":"medium","speed":1.05,
    "duration_hard_min_s":30,"duration_hard_max_s":45,"initial_words_per_second":2.55,
    "pause_cost_s":{"comma":.1,"sentence":.22,"ellipsis":.32,"colon":.16}
}


def test_driver_router():
    assert choose_primary_driver({"MONEY":9.2,"PERSONAL_GROWTH":8.9}) == "MONEY"


def test_angle_and_hook_tournaments_are_ranked():
    assert rank_angles([AngleCandidate("a","x",7), AngleCandidate("b","y",9)])[0].id == "b"
    assert rank_hooks([HookCandidate("a","GAIN","x",8), HookCandidate("b","LOSS","y",9)])[0].id == "b"


def test_retention_graph_ids_are_stable():
    beats = build_retention_beats([("hook","x"),("proof","y"),("moral","z")], 9)
    assert stable_beat_ids(beats)
    assert [b.id for b in beats] == ["B00_HOOK","B01_PROOF","B02_MORAL"]


def test_tts_overrides_do_not_modify_display_source():
    display = "Conecta Claude Code con tu editor."
    tts = compile_tts_text(display, {"Claude Code":"Clod Coud"})
    assert display == "Conecta Claude Code con tu editor."
    assert "Clod Coud" in tts


def test_preflight_rejects_long_or_incomplete_manifest():
    manifest = {"source_refs":["x"],"viral_driver":"MONEY","script_display_text":"hola","script_tts_text":"hola","semantic_beats":[]}
    result = preflight_manifest(manifest, PROFILE)
    assert not result.ok
    assert any("duration" in e for e in result.errors)
    assert any("moral" in e for e in result.errors)


def test_provider_request_and_telemetry_roundtrip():
    manifest = {"script_tts_text":"hola","render":{}}
    payload = compile_request(manifest, PROFILE, title="demo")
    assert payload["avatarId"] == "look"
    out = ingest_render_telemetry(manifest, {"id":"job1","status":"completed","duration":38.2,"video_url":"https://example/video.mp4"})
    assert out["render"]["provider_job_id"] == "job1"
    assert out["render"]["actual_duration_s"] == 38.2


def test_performance_attribution_is_bound_to_strategy():
    manifest = {"content_id":"c1","viral_driver":"MONEY","hook":"h","cta":{"placement":"PRE_PAYOFF"},"semantic_beats":[{"id":"B00_HOOK"}]}
    record = PerformanceRecord(content_id="c1", platform="instagram", views=1000, retention_3s=.8)
    out = attach_attribution(manifest, record)
    assert out["attribution"]["viral_driver"] == "MONEY"
    assert out["performance"]["views"] == 1000
