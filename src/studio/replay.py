from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
from typing import Any, Mapping
import zipfile

from src.studio.run_manifest import (
    ProductRunManifestError,
    build_product_run_manifest,
    verify_product_run_manifest,
)


REQUIRED_PRODUCT_EVIDENCE_PATHS = (
    ".artifacts/product-run-manifest.json",
    "runtime/remotion/studio_execution_bundle.json",
    "runtime/remotion/render_evidence.local.json",
    "runtime/remotion/src/runtimeSpec.json",
    "runtime/remotion/out/runtime-local.mp4",
)

_DEFAULT_MAX_FILES = 128
_DEFAULT_MAX_TOTAL_BYTES = 1024 * 1024 * 1024
_DEFAULT_MAX_FILE_BYTES = 512 * 1024 * 1024
_CHUNK = 1024 * 1024


class ProductReplayError(ValueError):
    """Raised when a persisted Product E2E evidence package cannot be trusted/replayed."""


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path, *, max_bytes: int = 32 * 1024 * 1024) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ProductReplayError(f"required JSON file missing or unsafe: {path}")
    size = path.stat().st_size
    if size <= 0 or size > max_bytes:
        raise ProductReplayError(f"required JSON file size invalid: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
        raise ProductReplayError(f"required JSON file is unreadable: {path}") from exc
    if not isinstance(value, dict):
        raise ProductReplayError(f"required JSON file must contain an object: {path}")
    return value


def _safe_zip_member(name: str) -> PurePosixPath:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ProductReplayError("archive member path is invalid")
    path = PurePosixPath(name)
    if path.is_absolute():
        raise ProductReplayError(f"absolute archive member rejected: {name}")
    parts = path.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ProductReplayError(f"unsafe archive member rejected: {name}")
    return path


def _zip_entry_kind(info: zipfile.ZipInfo) -> int:
    mode = info.external_attr >> 16
    return stat.S_IFMT(mode) if mode else 0


def safe_extract_product_evidence(
    archive_path: Path,
    destination: Path,
    *,
    max_files: int = _DEFAULT_MAX_FILES,
    max_total_bytes: int = _DEFAULT_MAX_TOTAL_BYTES,
    max_file_bytes: int = _DEFAULT_MAX_FILE_BYTES,
) -> dict[str, Any]:
    archive_path = archive_path.resolve()
    if not archive_path.is_file() or archive_path.is_symlink():
        raise ProductReplayError("evidence archive missing or unsafe")
    if max_files <= 0 or max_total_bytes <= 0 or max_file_bytes <= 0:
        raise ProductReplayError("archive extraction limits must be positive")

    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    seen: set[str] = set()
    files = 0
    total = 0

    try:
        archive = zipfile.ZipFile(archive_path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ProductReplayError("evidence archive is not a readable ZIP") from exc

    with archive:
        infos = archive.infolist()
        if len(infos) > max_files * 2:
            raise ProductReplayError("archive contains too many entries")
        for info in infos:
            rel = _safe_zip_member(info.filename)
            canonical = rel.as_posix().rstrip("/")
            if canonical in seen:
                raise ProductReplayError(f"duplicate archive member rejected: {canonical}")
            seen.add(canonical)

            kind = _zip_entry_kind(info)
            if kind == stat.S_IFLNK:
                raise ProductReplayError(f"symlink archive member rejected: {canonical}")
            if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ProductReplayError(f"special archive member rejected: {canonical}")

            target = (root / Path(*rel.parts)).resolve()
            if target != root and root not in target.parents:
                raise ProductReplayError(f"archive member escapes destination: {canonical}")

            if info.is_dir() or kind == stat.S_IFDIR:
                target.mkdir(parents=True, exist_ok=True)
                continue

            files += 1
            if files > max_files:
                raise ProductReplayError("archive contains too many files")
            if info.file_size <= 0 or info.file_size > max_file_bytes:
                raise ProductReplayError(f"archive member size invalid: {canonical}")
            total += info.file_size
            if total > max_total_bytes:
                raise ProductReplayError("archive uncompressed size exceeds limit")

            target.parent.mkdir(parents=True, exist_ok=True)
            written = 0
            try:
                with archive.open(info, "r") as source, target.open("xb") as output:
                    while chunk := source.read(_CHUNK):
                        written += len(chunk)
                        if written > info.file_size or written > max_file_bytes:
                            raise ProductReplayError(f"archive member exceeded declared/allowed size: {canonical}")
                        output.write(chunk)
            except FileExistsError as exc:
                raise ProductReplayError(f"archive extraction target already exists: {canonical}") from exc
            if written != info.file_size:
                raise ProductReplayError(f"archive member size mismatch after extraction: {canonical}")

    missing = [rel for rel in REQUIRED_PRODUCT_EVIDENCE_PATHS if not (root / rel).is_file()]
    if missing:
        raise ProductReplayError(f"archive missing required product evidence: {missing}")

    return {
        "archive_sha256": _sha256_file(archive_path),
        "archive_bytes": archive_path.stat().st_size,
        "files_extracted": files,
        "uncompressed_bytes": total,
        "destination": str(root),
    }


def _required_file(root: Path, relative: str) -> Path:
    root = root.resolve()
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise ProductReplayError(f"required evidence file missing or unsafe: {relative}")
    resolved = path.resolve()
    if root not in resolved.parents:
        raise ProductReplayError(f"required evidence file escapes root: {relative}")
    return resolved


def verify_product_evidence_directory(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir() or root.is_symlink():
        raise ProductReplayError("evidence root missing or unsafe")

    manifest_path = _required_file(root, ".artifacts/product-run-manifest.json")
    bundle_path = _required_file(root, "runtime/remotion/studio_execution_bundle.json")
    evidence_path = _required_file(root, "runtime/remotion/render_evidence.local.json")
    spec_path = _required_file(root, "runtime/remotion/src/runtimeSpec.json")
    artifact_path = _required_file(root, "runtime/remotion/out/runtime-local.mp4")

    manifest = _load_json(manifest_path)
    bundle = _load_json(bundle_path)
    runtime_evidence = _load_json(evidence_path)
    runtime_spec = _load_json(spec_path)

    try:
        verify_product_run_manifest(manifest)
    except ProductRunManifestError as exc:
        raise ProductReplayError(str(exc)) from exc

    artifact = manifest.get("physical_artifact")
    if not isinstance(artifact, Mapping):
        raise ProductReplayError("product manifest physical_artifact missing")
    artifact_ref = artifact.get("ref")
    if not isinstance(artifact_ref, str) or not artifact_ref:
        raise ProductReplayError("product manifest artifact ref missing")

    actual_artifact_sha = _sha256_file(artifact_path)
    actual_artifact_bytes = artifact_path.stat().st_size
    actual_spec_sha = _sha256_file(spec_path)
    if actual_artifact_sha != artifact.get("sha256"):
        raise ProductReplayError("persisted MP4 SHA differs from product manifest")
    if actual_artifact_bytes != artifact.get("bytes"):
        raise ProductReplayError("persisted MP4 size differs from product manifest")
    if actual_spec_sha != manifest.get("runtime_spec_file_sha256"):
        raise ProductReplayError("persisted runtimeSpec SHA differs from product manifest")

    try:
        rebuilt = build_product_run_manifest(
            bundle,
            runtime_evidence,
            runtime_spec,
            git_sha=str(manifest.get("git_sha")),
            artifact_ref=artifact_ref,
            artifact_sha256=actual_artifact_sha,
            artifact_bytes=actual_artifact_bytes,
            runtime_spec_file_sha256=actual_spec_sha,
        )
    except ProductRunManifestError as exc:
        raise ProductReplayError(str(exc)) from exc

    if rebuilt != manifest:
        raise ProductReplayError("replayed product manifest differs from persisted manifest")

    recovery = manifest.get("recovery")
    if not isinstance(recovery, Mapping) or recovery.get("recovery_ready") is not True:
        raise ProductReplayError("persisted run is not recovery-ready")

    return {
        "schema": "motion-os.product-evidence-replay/v1",
        "status": "OFFLINE_LOGICAL_REPLAY_VERIFIED",
        "run_id": manifest["run_id"],
        "git_sha": manifest["git_sha"],
        "manifest_hash": manifest["manifest_hash"],
        "bundle_hash": manifest["bundle_hash"],
        "runtime_evidence_hash": manifest["runtime_evidence_hash"],
        "runtime_spec_file_sha256": actual_spec_sha,
        "artifact_sha256": actual_artifact_sha,
        "artifact_bytes": actual_artifact_bytes,
        "recovery_manifest_hash": recovery.get("manifest_hash"),
        "recovery_ready": True,
        "production_authority": False,
        "creative_authority": False,
        "provider_authority": False,
        "project_done": False,
    }


def compare_replay_to_physical_probe(replay: Mapping[str, Any], physical_probe: Mapping[str, Any]) -> None:
    if physical_probe.get("technical_runtime_gate") != "PASS" or physical_probe.get("errors") != []:
        raise ProductReplayError("fresh physical probe did not PASS")
    if physical_probe.get("video_sha256") != replay.get("artifact_sha256"):
        raise ProductReplayError("fresh physical probe MP4 SHA differs from replay")
    if physical_probe.get("video_bytes") != replay.get("artifact_bytes"):
        raise ProductReplayError("fresh physical probe MP4 size differs from replay")
    if physical_probe.get("spec_sha256") != replay.get("runtime_spec_file_sha256"):
        raise ProductReplayError("fresh physical probe runtimeSpec SHA differs from replay")


def seal_replay_report(
    report: Mapping[str, Any],
    *,
    archive_sha256: str,
    archive_bytes: int,
    physical_probe: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if report.get("status") != "OFFLINE_LOGICAL_REPLAY_VERIFIED":
        raise ProductReplayError("logical replay must pass before report sealing")
    if not isinstance(archive_sha256, str) or len(archive_sha256) != 64:
        raise ProductReplayError("archive SHA256 invalid")
    if not isinstance(archive_bytes, int) or isinstance(archive_bytes, bool) or archive_bytes <= 0:
        raise ProductReplayError("archive bytes invalid")

    out = deepcopy(dict(report))
    out["archive_sha256"] = archive_sha256
    out["archive_bytes"] = archive_bytes
    if physical_probe is None:
        out["status"] = "OFFLINE_LOGICAL_REPLAY_VERIFIED"
        out["physical_authority"] = False
        out["physical_reprobe"] = {
            "executed": False,
            "technical_runtime_gate": None,
            "video_sha256": None,
            "spec_sha256": None,
        }
    else:
        compare_replay_to_physical_probe(report, physical_probe)
        out["status"] = "OFFLINE_REPLAY_VERIFIED"
        out["physical_authority"] = True
        out["physical_reprobe"] = {
            "executed": True,
            "technical_runtime_gate": physical_probe.get("technical_runtime_gate"),
            "video_sha256": physical_probe.get("video_sha256"),
            "spec_sha256": physical_probe.get("spec_sha256"),
        }
    out["report_hash"] = _canonical_hash(out)
    return out


def verify_replay_report_hash(report: Mapping[str, Any]) -> None:
    observed = report.get("report_hash")
    if not isinstance(observed, str) or len(observed) != 64:
        raise ProductReplayError("replay report hash missing or invalid")
    unsigned = deepcopy(dict(report))
    unsigned.pop("report_hash", None)
    if _canonical_hash(unsigned) != observed:
        raise ProductReplayError("replay report hash mismatch")
