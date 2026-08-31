from __future__ import annotations

from pathlib import Path
import json

from src.qa.temporal_multimodal import uniform_sample_indices
from src.qa.creative_tournament import REQUIRED_DIMENSIONS, THRESHOLDS


ROOT = Path(__file__).resolve().parents[1]
JOB = ROOT / "evidence" / "p4_rc06_provider_job_2026-08-31.json"


def test_provider_job_binds_exact_master_and_sampling_contract():
    job = json.loads(JOB.read_text(encoding="utf-8"))
    master = job["master"]
    sampling = job["sampling"]
    samples = sampling["samples"]

    assert job["status"] == "READY_FOR_EXTERNAL_PROVIDER"
    assert job["authority"] == "PREPARED_NOT_EXECUTED"
    assert master["media_sha256"] == "fbfd4fda97b1e4d07b8477018324210324c8115c0f5b9a3515eb27ae255f0f1f"
    assert [item["frame_index"] for item in samples] == list(uniform_sample_indices(300, target_samples=24))
    assert samples[0]["frame_index"] == 0
    assert samples[-1]["frame_index"] == 299
    assert all(len(item["sha256"]) == 64 for item in samples)
    assert all(item["timestamp_ms"] == round(item["frame_index"] / 30.0 * 1000) for item in samples)


def test_provider_job_matches_live_creative_contract_constants():
    job = json.loads(JOB.read_text(encoding="utf-8"))
    creative = job["creative_payload_contract"]
    assert set(creative["required_dimensions"]) == REQUIRED_DIMENSIONS
    assert creative["hard_thresholds"] == THRESHOLDS
    assert creative["mean_gate"] == 9.0


def test_provider_job_cannot_self_promote_without_real_provider_identity():
    job = json.loads(JOB.read_text(encoding="utf-8"))
    execution = job["execution"]
    requirements = job["provider_requirements"]
    assert requirements["must_review_entire_video_not_only_samples"] is True
    assert execution["provider"] is None
    assert execution["provider_run_id"] is None
    assert execution["executed"] is False
    assert execution["authoritative"] is False
    assert job["known_non_authoritative_preflight"]["authority"] == "NONE"
