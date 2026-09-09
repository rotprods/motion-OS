from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
import zipfile

import pytest

from scripts.build_remotion_runtime_fixture import build_phase06_studio_fixture
from src.studio.content_bridge import prepare_studio_execution
from src.studio.replay import (
    ProductReplayError,
    safe_extract_product_evidence,
    seal_replay_report,
    verify_product_evidence_directory,
    verify_replay_report_hash,
)
from src.studio.run_manifest import build_product_run_manifest


ROOT = Path(__file__).resolve().parents[1]
GIT_SHA = "a" * 40
ARTIFACT_REF = "durable://fixture/product-e2e/runtime-local.mp4"
ARTIFACT_BYTES = b"offline-replay-contract-media"


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _build_evidence_tree(root: Path) -> dict:
    sealed, handoff = build_phase06_studio_fixture()
    bundle = prepare_studio_execution(sealed, handoff, fps=30, width=640, height=360)

    spec_path = root / "runtime/remotion/src/runtimeSpec.json"
    _write_json(spec_path, bundle["runtime_spec"])
    spec_sha = hashlib.sha256(spec_path.read_bytes()).hexdigest()

    artifact_path = root / "runtime/remotion/out/runtime-local.mp4"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(ARTIFACT_BYTES)
    artifact_sha = hashlib.sha256(ARTIFACT_BYTES).hexdigest()

    spec = bundle["runtime_spec"]
    runtime_evidence = {
        "schema": "motion-os.remotion-runtime-evidence/v3",
        "runtime": "Remotion/Chromium",
        "video_sha256": artifact_sha,
        "video_bytes": len(ARTIFACT_BYTES),
        "spec_sha256": spec_sha,
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
    evidence_path = root / "runtime/remotion/render_evidence.local.json"
    _write_json(evidence_path, runtime_evidence)

    bundle_path = root / "runtime/remotion/studio_execution_bundle.json"
    _write_json(bundle_path, bundle)

    manifest = build_product_run_manifest(
        bundle,
        runtime_evidence,
        bundle["runtime_spec"],
        git_sha=GIT_SHA,
        artifact_ref=ARTIFACT_REF,
        artifact_sha256=artifact_sha,
        artifact_bytes=len(ARTIFACT_BYTES),
        runtime_spec_file_sha256=spec_sha,
    )
    manifest_path = root / ".artifacts/product-run-manifest.json"
    _write_json(manifest_path, manifest)
    return manifest


def _make_valid_zip(tmp_path: Path) -> tuple[Path, dict]:
    source = tmp_path / "source"
    manifest = _build_evidence_tree(source)
    archive = tmp_path / "product-evidence.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            handle.write(path, path.relative_to(source).as_posix())
    return archive, manifest


def test_offline_logical_replay_rebuilds_exact_persisted_manifest(tmp_path):
    archive, manifest = _make_valid_zip(tmp_path)
    extracted = tmp_path / "fresh"
    extraction = safe_extract_product_evidence(archive, extracted)
    replay = verify_product_evidence_directory(extracted)
    assert replay["status"] == "OFFLINE_LOGICAL_REPLAY_VERIFIED"
    assert replay["manifest_hash"] == manifest["manifest_hash"]
    assert replay["artifact_sha256"] == manifest["physical_artifact"]["sha256"]
    assert replay["recovery_ready"] is True
    assert extraction["files_extracted"] == 5


def test_archive_path_traversal_is_rejected(tmp_path):
    archive, _ = _make_valid_zip(tmp_path)
    with zipfile.ZipFile(archive, "a") as handle:
        handle.writestr("../escape.txt", "escape")
    with pytest.raises(ProductReplayError, match="unsafe archive member"):
        safe_extract_product_evidence(archive, tmp_path / "extract")
    assert not (tmp_path / "escape.txt").exists()


def test_absolute_archive_path_is_rejected(tmp_path):
    archive, _ = _make_valid_zip(tmp_path)
    with zipfile.ZipFile(archive, "a") as handle:
        handle.writestr("/absolute.txt", "escape")
    with pytest.raises(ProductReplayError, match="absolute archive member"):
        safe_extract_product_evidence(archive, tmp_path / "extract")


def test_symlink_archive_member_is_rejected(tmp_path):
    archive, _ = _make_valid_zip(tmp_path)
    info = zipfile.ZipInfo("runtime/remotion/out/link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "a") as handle:
        handle.writestr(info, "runtime-local.mp4")
    with pytest.raises(ProductReplayError, match="symlink archive member"):
        safe_extract_product_evidence(archive, tmp_path / "extract")


def test_duplicate_archive_member_is_rejected(tmp_path):
    archive, _ = _make_valid_zip(tmp_path)
    with zipfile.ZipFile(archive, "a") as handle:
        with pytest.warns(UserWarning):
            handle.writestr("runtime/remotion/out/runtime-local.mp4", b"duplicate")
    with pytest.raises(ProductReplayError, match="duplicate archive member"):
        safe_extract_product_evidence(archive, tmp_path / "extract")


def test_archive_limits_fail_closed(tmp_path):
    archive, _ = _make_valid_zip(tmp_path)
    with pytest.raises(ProductReplayError, match="too many files"):
        safe_extract_product_evidence(archive, tmp_path / "extract-files", max_files=4)
    with pytest.raises(ProductReplayError, match="uncompressed size exceeds"):
        safe_extract_product_evidence(archive, tmp_path / "extract-bytes", max_total_bytes=32)


def test_missing_required_member_is_rejected(tmp_path):
    source = tmp_path / "source"
    _build_evidence_tree(source)
    archive = tmp_path / "missing.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            rel = path.relative_to(source).as_posix()
            if rel != "runtime/remotion/src/runtimeSpec.json":
                handle.write(path, rel)
    with pytest.raises(ProductReplayError, match="missing required product evidence"):
        safe_extract_product_evidence(archive, tmp_path / "extract")


def test_substituted_mp4_is_rejected_after_extraction(tmp_path):
    archive, _ = _make_valid_zip(tmp_path)
    extracted = tmp_path / "fresh"
    safe_extract_product_evidence(archive, extracted)
    (extracted / "runtime/remotion/out/runtime-local.mp4").write_bytes(b"substituted")
    with pytest.raises(ProductReplayError, match="persisted MP4 SHA differs"):
        verify_product_evidence_directory(extracted)


def test_bundle_tamper_is_rejected_after_extraction(tmp_path):
    archive, _ = _make_valid_zip(tmp_path)
    extracted = tmp_path / "fresh"
    safe_extract_product_evidence(archive, extracted)
    path = extracted / "runtime/remotion/studio_execution_bundle.json"
    bundle = json.loads(path.read_text(encoding="utf-8"))
    bundle["content_id"] = "tampered"
    _write_json(path, bundle)
    with pytest.raises(ProductReplayError):
        verify_product_evidence_directory(extracted)


def test_persisted_manifest_tamper_is_rejected(tmp_path):
    archive, _ = _make_valid_zip(tmp_path)
    extracted = tmp_path / "fresh"
    safe_extract_product_evidence(archive, extracted)
    path = extracted / ".artifacts/product-run-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["project_done"] = True
    _write_json(path, manifest)
    with pytest.raises(ProductReplayError):
        verify_product_evidence_directory(extracted)


def test_replay_report_hash_seals_final_physical_fields(tmp_path):
    archive, _ = _make_valid_zip(tmp_path)
    extracted = tmp_path / "fresh"
    extraction = safe_extract_product_evidence(archive, extracted)
    replay = verify_product_evidence_directory(extracted)
    physical = {
        "technical_runtime_gate": "PASS",
        "errors": [],
        "video_sha256": replay["artifact_sha256"],
        "video_bytes": replay["artifact_bytes"],
        "spec_sha256": replay["runtime_spec_file_sha256"],
    }
    report = seal_replay_report(
        replay,
        archive_sha256=extraction["archive_sha256"],
        archive_bytes=extraction["archive_bytes"],
        physical_probe=physical,
    )
    verify_replay_report_hash(report)
    assert report["status"] == "OFFLINE_REPLAY_VERIFIED"
    assert report["physical_authority"] is True
    mutated = deepcopy(report)
    mutated["physical_reprobe"]["video_sha256"] = "0" * 64
    with pytest.raises(ProductReplayError, match="report hash mismatch"):
        verify_replay_report_hash(mutated)


def test_mismatched_fresh_physical_probe_is_rejected(tmp_path):
    archive, _ = _make_valid_zip(tmp_path)
    extracted = tmp_path / "fresh"
    extraction = safe_extract_product_evidence(archive, extracted)
    replay = verify_product_evidence_directory(extracted)
    physical = {
        "technical_runtime_gate": "PASS",
        "errors": [],
        "video_sha256": "0" * 64,
        "video_bytes": replay["artifact_bytes"],
        "spec_sha256": replay["runtime_spec_file_sha256"],
    }
    with pytest.raises(ProductReplayError, match="MP4 SHA differs"):
        seal_replay_report(
            replay,
            archive_sha256=extraction["archive_sha256"],
            archive_bytes=extraction["archive_bytes"],
            physical_probe=physical,
        )


def test_logical_only_report_cannot_claim_physical_authority(tmp_path):
    archive, _ = _make_valid_zip(tmp_path)
    extracted = tmp_path / "fresh"
    extraction = safe_extract_product_evidence(archive, extracted)
    replay = verify_product_evidence_directory(extracted)
    report = seal_replay_report(
        replay,
        archive_sha256=extraction["archive_sha256"],
        archive_bytes=extraction["archive_bytes"],
        physical_probe=None,
    )
    verify_replay_report_hash(report)
    assert report["status"] == "OFFLINE_LOGICAL_REPLAY_VERIFIED"
    assert report["physical_authority"] is False


def test_offline_replay_cli_is_directly_executable():
    completed = subprocess.run(
        [sys.executable, "scripts/studio_replay_verify.py", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--package" in completed.stdout
    assert "--skip-physical-probe" in completed.stdout
