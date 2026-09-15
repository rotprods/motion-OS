from __future__ import annotations

from pathlib import Path
import json

from src.qa.temporal_multimodal import uniform_sample_indices
from src.qa.creative_tournament import REQUIRED_DIMENSIONS, THRESHOLDS


ROOT = Path(__file__).resolve().parents[1]
JOB = ROOT / "evidence" / "p4_rc06_provider_job_v1_1_2026-09-11.json"
LEGACY_JOB = ROOT / "evidence" / "p4_rc06_provider_job_2026-08-31.json"


def load_job():
    return json.loads(JOB.read_text(encoding="utf-8"))


def test_provider_job_v1_1_preserves_historical_v1_0_instead_of_rewriting_it():
    job = load_job()
    supersedes = job["supersedes"]
    assert LEGACY_JOB.exists()
    assert job["schema_version"] == "1.1"
    assert supersedes["path"] == "evidence/p4_rc06_provider_job_2026-08-31.json"
    assert supersedes["source_commit_sha"] == "a319b853246d579fc0879e9e0edf9e0f11126a3e"
    assert supersedes["source_blob_sha"] == "9eec83bc500cfd0a02178767e20077d92b838f29"
    assert supersedes["disposition"] == "SUPERSEDED_CONTRACT_PRESERVED_AS_HISTORICAL_EVIDENCE"


def test_provider_job_binds_exact_master_and_sampling_authority():
    job = load_job()
    master = job["master"]
    sampling = job["sampling_authority"]

    assert job["status"] == "READY_FOR_EXTERNAL_PROVIDER"
    assert job["authority"] == "PREPARED_NOT_EXECUTED"
    assert master["media_sha256"] == "fbfd4fda97b1e4d07b8477018324210324c8115c0f5b9a3515eb27ae255f0f1f"
    assert master["frame_count"] == 300
    assert master["fps"] == 30.0
    assert master["duration_ms"] == 10000
    assert sampling["policy"] == "uniform_plus_boundaries_v1"
    assert sampling["target_samples"] == 24
    indices = uniform_sample_indices(master["frame_count"], target_samples=sampling["target_samples"])
    assert indices[0] == sampling["first_frame_index"] == 0
    assert indices[-1] == sampling["last_frame_index"] == 299
    assert sampling["source_blob_sha"] == "9eec83bc500cfd0a02178767e20077d92b838f29"


def test_temporal_provider_contract_requires_exact_external_authority_binding():
    job = load_job()
    contract = job["temporal_payload_contract"]
    requirements = job["provider_requirements"]
    required = set(contract["required_fields_for_authority"])

    assert {
        "provider",
        "provider_run_id",
        "media_sha256",
        "full_video_scope",
        "provider_attestation_id",
        "authoritative",
        "score",
        "dimensions",
        "defects",
        "recommendation",
    } <= required
    assert set(contract["exact_match_fields"]) == {"provider", "provider_run_id", "media_sha256"}
    assert set(contract["literal_boolean_fields"]) == {"authoritative", "full_video_scope"}
    assert requirements["must_return_literal_full_video_scope_true"] is True
    assert requirements["must_return_nonempty_provider_attestation_id"] is True
    assert requirements["caller_local_boolean_is_authority"] is False


def test_provider_job_matches_live_creative_contract_constants_and_binding_family():
    job = load_job()
    creative = job["creative_payload_contract"]
    required = set(creative["required_fields_for_authority"])

    assert set(creative["required_dimensions"]) == REQUIRED_DIMENSIONS
    assert creative["hard_thresholds"] == THRESHOLDS
    assert creative["mean_gate"] == 9.0
    assert {
        "provider",
        "provider_run_id",
        "media_sha256",
        "full_video_scope",
        "provider_attestation_id",
        "authoritative",
        "dimensions",
    } <= required
    assert set(creative["exact_match_fields"]) == {"provider", "provider_run_id", "media_sha256"}


def test_provider_job_untrusted_input_policy_covers_p1_failure_family():
    policy = load_job()["untrusted_input_policy"]
    assert policy == {
        "provider_payload": "UNTRUSTED_DATA",
        "reject_truthy_string_booleans": True,
        "reject_bool_as_numeric": True,
        "reject_nan_and_infinity": True,
        "reject_cross_media_replay": True,
        "reject_cross_candidate_replay": True,
        "reject_unbounded_identity_fields": True,
        "fail_closed_on_missing_authority_binding": True,
    }


def test_provider_job_cannot_self_promote_without_real_provider_identity():
    job = load_job()
    execution = job["execution"]
    assert execution["provider"] is None
    assert execution["provider_run_id"] is None
    assert execution["provider_attestation_id"] is None
    assert execution["full_video_scope"] is False
    assert execution["executed"] is False
    assert execution["authoritative"] is False
    assert job["known_non_authoritative_delivery_facts"]["authority"] == "NONE"
