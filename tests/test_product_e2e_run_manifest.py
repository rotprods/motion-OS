from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from scripts.build_remotion_runtime_fixture import build_phase06_studio_fixture
from src.studio.content_bridge import prepare_studio_execution
from src.studio.run_manifest import (
    ProductRunManifestError,
    build_product_run_manifest,
    canonical_hash,
    verify_product_run_manifest,
)


GIT_SHA = "a" * 40
ARTIFACT = b"contract-only-mp4-placeholder"
ARTIFACT_SHA = hashlib.sha256(ARTIFACT).hexdigest()
SPEC_FILE_SHA = "b" * 64
ARTIFACT_REF = "github-actions://rotprods/motion-OS/run/fixture/merge-safe-remotion-evidence/runtime-local.mp4"


def _bundle() -> dict:
    sealed, handoff = build_phase06_studio_fixture()
    return prepare_studio_execution(sealed, handoff, fps=30, width=640, height=360)


def _runtime_evidence(bundle: dict) -> dict:
    spec = bundle["runtime_spec"]
    return {
        "schema": "motion-os.remotion-runtime-evidence/v3",
        "runtime": "Remotion/Chromium",
        "video_sha256": ARTIFACT_SHA,
        "video_bytes": len(ARTIFACT),
        "spec_sha256": SPEC_FILE_SHA,
        "spec_lineage": {
            "scene_ids": [scene["id"] for scene in spec["scenes"]],
            "transition_types": [
                (scene.get("transition") or {}).get("type") if isinstance(scene.get("transition"), dict) else None
                for scene in spec["scenes"]
            ],
        },
        "errors": [],
        "technical_runtime_gate": "PASS",
        "creative_authority": "none",
        "temporal_critic_authority": "none",
    }


def _build(bundle: dict | None = None, evidence: dict | None = None) -> dict:
    bundle = bundle or _bundle()
    evidence = evidence or _runtime_evidence(bundle)
    return build_product_run_manifest(
        bundle,
        evidence,
        bundle["runtime_spec"],
        git_sha=GIT_SHA,
        artifact_ref=ARTIFACT_REF,
        artifact_sha256=ARTIFACT_SHA,
        artifact_bytes=len(ARTIFACT),
        runtime_spec_file_sha256=SPEC_FILE_SHA,
    )


def test_golden_technical_product_run_is_recoverable_and_never_self_promotes():
    manifest = _build()
    verify_product_run_manifest(manifest)
    assert manifest["status"] == "TECHNICAL_PRODUCT_E2E_VERIFIED"
    assert manifest["recovery"]["recovery_ready"] is True
    assert manifest["physical_artifact"]["sha256"] == ARTIFACT_SHA
    assert manifest["production_authority"] is False
    assert manifest["creative_authority"] is False
    assert manifest["provider_authority"] is False
    assert manifest["project_done"] is False


def test_product_run_manifest_is_deterministic_for_identical_evidence():
    first = _build()
    second = _build()
    assert first == second
    assert first["run_id"] == second["run_id"]
    assert first["manifest_hash"] == second["manifest_hash"]


def test_graph_tamper_is_rejected_even_when_original_hash_is_retained():
    bundle = _bundle()
    bundle["graph"]["nodes"][0]["data"]["tampered"] = True
    with pytest.raises(ProductRunManifestError, match="graph_hash mismatch"):
        _build(bundle=bundle)


def test_asset_manifest_tamper_is_rejected():
    bundle = _bundle()
    bundle["asset_manifest"]["assets"][0]["source_ref"] = "fixture://tampered"
    with pytest.raises(ProductRunManifestError, match="asset_manifest_hash mismatch"):
        _build(bundle=bundle)


def test_render_manifest_missing_assignment_fails_recovery_even_with_resealed_hash():
    bundle = _bundle()
    bundle["render_manifest"]["assignments"] = bundle["render_manifest"]["assignments"][1:]
    unsigned = {key: value for key, value in bundle["render_manifest"].items() if key != "manifest_hash"}
    bundle["render_manifest"]["manifest_hash"] = canonical_hash(unsigned)
    with pytest.raises(ProductRunManifestError, match="recovery manifest is not ready"):
        _build(bundle=bundle)


def test_failed_physical_runtime_gate_is_rejected():
    bundle = _bundle()
    evidence = _runtime_evidence(bundle)
    evidence["technical_runtime_gate"] = "FAIL"
    evidence["errors"] = ["frames:89!=90"]
    with pytest.raises(ProductRunManifestError, match="runtime gate is not PASS"):
        _build(bundle=bundle, evidence=evidence)


def test_artifact_hash_must_match_independently_supplied_physical_hash():
    bundle = _bundle()
    evidence = _runtime_evidence(bundle)
    evidence["video_sha256"] = "c" * 64
    with pytest.raises(ProductRunManifestError, match="artifact SHA differs"):
        _build(bundle=bundle, evidence=evidence)


def test_runtime_spec_file_hash_must_match_runtime_evidence():
    bundle = _bundle()
    evidence = _runtime_evidence(bundle)
    evidence["spec_sha256"] = "c" * 64
    with pytest.raises(ProductRunManifestError, match="spec file SHA differs"):
        _build(bundle=bundle, evidence=evidence)


def test_runtime_scene_lineage_must_match_compiled_bundle():
    bundle = _bundle()
    evidence = _runtime_evidence(bundle)
    evidence["spec_lineage"]["scene_ids"][0] = "scene:TAMPERED"
    with pytest.raises(ProductRunManifestError, match="scene lineage differs"):
        _build(bundle=bundle, evidence=evidence)


def test_runtime_transition_lineage_must_match_compiled_bundle():
    bundle = _bundle()
    evidence = _runtime_evidence(bundle)
    evidence["spec_lineage"]["transition_types"][0] = "tampered"
    with pytest.raises(ProductRunManifestError, match="transition lineage differs"):
        _build(bundle=bundle, evidence=evidence)


def test_runtime_spec_document_must_equal_bundle_document():
    bundle = _bundle()
    evidence = _runtime_evidence(bundle)
    runtime_doc = deepcopy(bundle["runtime_spec"])
    runtime_doc["project"]["duration_frames"] += 1
    with pytest.raises(ProductRunManifestError, match="file content differs"):
        build_product_run_manifest(
            bundle,
            evidence,
            runtime_doc,
            git_sha=GIT_SHA,
            artifact_ref=ARTIFACT_REF,
            artifact_sha256=ARTIFACT_SHA,
            artifact_bytes=len(ARTIFACT),
            runtime_spec_file_sha256=SPEC_FILE_SHA,
        )


def test_malformed_git_sha_is_rejected():
    bundle = _bundle()
    with pytest.raises(ProductRunManifestError, match="git_sha must be 40-hex"):
        build_product_run_manifest(
            bundle,
            _runtime_evidence(bundle),
            bundle["runtime_spec"],
            git_sha="not-a-commit",
            artifact_ref=ARTIFACT_REF,
            artifact_sha256=ARTIFACT_SHA,
            artifact_bytes=len(ARTIFACT),
            runtime_spec_file_sha256=SPEC_FILE_SHA,
        )


def test_tampered_persisted_manifest_hash_is_rejected():
    manifest = _build()
    manifest["content_id"] = "tampered"
    with pytest.raises(ProductRunManifestError, match="manifest hash mismatch"):
        verify_product_run_manifest(manifest)


def test_technical_manifest_cannot_claim_production_or_project_done():
    manifest = _build()
    for field in ("production_authority", "creative_authority", "provider_authority", "project_done"):
        mutated = deepcopy(manifest)
        mutated[field] = True
        unsigned = deepcopy(mutated)
        unsigned.pop("manifest_hash", None)
        mutated["manifest_hash"] = canonical_hash(unsigned)
        with pytest.raises(ProductRunManifestError):
            verify_product_run_manifest(mutated)
