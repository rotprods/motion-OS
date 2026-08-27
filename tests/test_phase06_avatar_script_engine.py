import json
from pathlib import Path

from src.content.avatar_script_engine import (
    apply_pronunciation_overrides,
    build_avatar_request,
    deserialize_manifest,
    estimate_duration_s,
    get_profile,
    ingest_render_telemetry,
    schema_validate,
    serialize_manifest,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "phase06" / "openmontage_manifest.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_schema_validates_real_manifest_fixture():
    schema_validate(load_fixture())


def test_profile_is_configurable_and_canonical():
    profile = get_profile("heygen_rot_canonical_v1")
    assert profile["provider"] == "heygen"
    assert profile["look_id"] == "49327c09aed5418383ba330e0daf0304"
    assert profile["voice_id"] == "3fbb6707e4414df28da39b6cda40a4e3"
    assert profile["aspect_ratio"] == "9:16"
    assert profile["resolution"] == "1080p"


def test_tts_override_does_not_mutate_display_text():
    display = "Conecta Claude Code y una API REST."
    overrides = {"Claude Code": "Clod Coud", "API": "éi-pi-ái", "REST": "réest"}
    tts = apply_pronunciation_overrides(display, overrides)
    assert display == "Conecta Claude Code y una API REST."
    assert tts == "Conecta Clod Coud y una éi-pi-ái réest."


def test_known_long_scripts_are_rejected_by_duration_gate():
    profile = get_profile("heygen_rot_canonical_v1")
    long_script = " ".join(["palabra"] * 220) + "."
    manifest = load_fixture()
    manifest["script_display_text"] = long_script
    manifest["script_tts_text"] = long_script
    manifest["pronunciation_overrides"] = {}
    issues = validate_manifest(manifest, profile)
    assert any(i.code == "ESTIMATED_DURATION_OUT_OF_RANGE" for i in issues)


def test_target_duration_hard_gate():
    manifest = load_fixture()
    manifest["duration_target_s"] = 62.8245
    issues = validate_manifest(manifest, get_profile("heygen_rot_canonical_v1"))
    assert any(i.code == "TARGET_DURATION_INVALID" for i in issues)


def test_duplicate_beat_ids_rejected():
    manifest = load_fixture()
    manifest["semantic_beats"][1]["id"] = manifest["semantic_beats"][0]["id"]
    issues = validate_manifest(manifest)
    assert any(i.code == "BEAT_ID_DUPLICATE" for i in issues)


def test_cta_target_must_exist():
    manifest = load_fixture()
    manifest["cta"]["target_beat_id"] = "B99_DOES_NOT_EXIST"
    issues = validate_manifest(manifest)
    assert any(i.code == "CTA_BEAT_MISSING" for i in issues)


def test_claim_provenance_cannot_be_dropped():
    manifest = load_fixture()
    manifest["claim_notes"] = []
    issues = validate_manifest(manifest)
    assert any(i.code == "CLAIM_NOTES_MISSING" for i in issues)


def test_serialization_preserves_stable_beat_ids():
    manifest = load_fixture()
    ids_before = [b["id"] for b in manifest["semantic_beats"]]
    ids_after = [b["id"] for b in deserialize_manifest(serialize_manifest(manifest))["semantic_beats"]]
    assert ids_before == ids_after


def test_avatar_request_uses_tts_not_display_text():
    manifest = load_fixture()
    profile = get_profile("heygen_rot_canonical_v1")
    request = build_avatar_request(manifest, profile)
    assert request["script"] == manifest["script_tts_text"]
    assert request["script"] != manifest["script_display_text"]
    assert request["avatarId"] == profile["look_id"]
    assert request["voiceId"] == profile["voice_id"]


def test_render_telemetry_ingestion_is_non_destructive():
    manifest = load_fixture()
    original_duration = manifest["render"].get("actual_duration_s")
    updated = ingest_render_telemetry(
        manifest,
        provider_job_id="job-1",
        status="completed",
        actual_duration_s=38.4,
        asset_ref="provider://video/1",
        credits_used=10.2,
    )
    assert updated["render"]["actual_duration_s"] == 38.4
    assert updated["semantic_beats"] == manifest["semantic_beats"]
    assert manifest["render"]["actual_duration_s"] == original_duration


def test_estimator_accounts_for_pause_and_phonetic_expansion():
    profile = get_profile("heygen_rot_canonical_v1")
    simple = estimate_duration_s("Hola mundo", profile)
    paused = estimate_duration_s("Hola, mundo… ¿qué tal?", profile, phonetic_expansion_chars=20)
    assert paused > simple


def test_retention_density_warns_when_beats_are_too_sparse():
    manifest = load_fixture()
    manifest["semantic_beats"] = manifest["semantic_beats"][:2]
    issues = validate_manifest(manifest)
    assert any(i.code == "RETENTION_BEAT_DENSITY_LOW" and i.severity == "WARN" for i in issues)
