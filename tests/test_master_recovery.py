from __future__ import annotations

from pathlib import Path
import hashlib
import zipfile

import pytest

from src.qa.master_recovery import (
    CANDIDATE_UNAVAILABLE,
    CONTAINER_HASH_MISMATCH,
    IDENTITY_UNQUALIFIED,
    MASTER_HASH_MISMATCH,
    RECOVERED_EXACT,
    RECOVERY_LIMIT_EXCEEDED,
    MasterIdentity,
    RecoveryCandidate,
    RecoveryContract,
    RecoveryLimitExceeded,
    sha256_path,
    sha256_zip_member,
    verify_recovery,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_exact_local_master_is_authoritative(tmp_path: Path):
    data = b"canonical-master-bytes"
    path = tmp_path / "master.mp4"
    path.write_bytes(data)
    result = verify_recovery(
        RecoveryContract(
            MasterIdentity("master", digest(data), len(data)),
            RecoveryCandidate("local", "local_file", "local:test"),
        ),
        path,
    )
    assert result.status == RECOVERED_EXACT
    assert result.exact
    assert result.authority == "EXACT_IDENTITY_VERIFIED"
    assert result.observed_sha256 == digest(data)


def test_unknown_historical_sha_can_never_be_promoted_to_recovered(tmp_path: Path):
    path = tmp_path / "rc09e.mp4"
    path.write_bytes(b"looks-like-rc09e")
    result = verify_recovery(
        RecoveryContract(
            MasterIdentity("RC09E", None, media_role="historical_working_master"),
            RecoveryCandidate("drive-candidate", "google_drive", "drive:file-id"),
        ),
        path,
    )
    assert result.status == IDENTITY_UNQUALIFIED
    assert not result.exact
    assert result.authority == "NONE"
    assert "exact_historical_sha256_unknown" in result.errors


def test_same_metadata_or_name_does_not_substitute_for_identity(tmp_path: Path):
    expected = b"real-master"
    imposter = b"different-master"
    path = tmp_path / "same-name.mp4"
    path.write_bytes(imposter)
    result = verify_recovery(
        RecoveryContract(
            MasterIdentity("canonical", digest(expected), len(expected)),
            RecoveryCandidate("candidate", "local_file", "same dimensions/duration/name"),
        ),
        path,
    )
    assert result.status == MASTER_HASH_MISMATCH
    assert result.observed_sha256 == digest(imposter)
    assert result.authority == "NONE"


def test_exact_master_inside_sha_bound_zip_is_recoverable(tmp_path: Path):
    master = b"verified-master-in-bundle"
    bundle = tmp_path / "proof.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr(".artifacts/final/master.mp4", master)
        archive.writestr("evidence.json", "{}")
    bundle_sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
    result = verify_recovery(
        RecoveryContract(
            MasterIdentity("p3-seed", digest(master), len(master)),
            RecoveryCandidate(
                "drive-proof",
                "google_drive",
                "drive:proof.zip",
                container_member=".artifacts/final/master.mp4",
                expected_container_sha256=bundle_sha,
            ),
        ),
        bundle,
    )
    assert result.status == RECOVERED_EXACT
    assert result.exact
    assert result.observed_container_sha256 == bundle_sha
    assert result.observed_sha256 == digest(master)


def test_tampered_bundle_fails_before_member_identity(tmp_path: Path):
    master = b"verified-master"
    bundle = tmp_path / "proof.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("master.mp4", master)
    result = verify_recovery(
        RecoveryContract(
            MasterIdentity("master", digest(master)),
            RecoveryCandidate(
                "bundle",
                "google_drive",
                "drive:bundle",
                container_member="master.mp4",
                expected_container_sha256="0" * 64,
            ),
        ),
        bundle,
    )
    assert result.status == CONTAINER_HASH_MISMATCH
    assert result.observed_sha256 is None
    assert result.authority == "NONE"


def test_missing_candidate_is_explicitly_unavailable(tmp_path: Path):
    result = verify_recovery(
        RecoveryContract(
            MasterIdentity("master", "1" * 64),
            RecoveryCandidate("missing", "local_file", "local:missing"),
        ),
        tmp_path / "missing.mp4",
    )
    assert result.status == CANDIDATE_UNAVAILABLE
    assert not result.exact


def test_zip_member_path_traversal_is_rejected():
    contract = RecoveryContract(
        MasterIdentity("master", "1" * 64),
        RecoveryCandidate(
            "unsafe",
            "google_drive",
            "drive:x",
            container_member="../master.mp4",
        ),
    )
    with pytest.raises(ValueError, match="unsafe_container_member"):
        contract.validate()


def test_container_hashing_limit_is_enforced_before_streaming(tmp_path: Path):
    path = tmp_path / "oversized.bin"
    path.write_bytes(b"x" * 64)
    with pytest.raises(RecoveryLimitExceeded, match="container_bytes_exceeded"):
        sha256_path(path, max_bytes=32)


def test_member_size_limit_is_enforced_before_streaming(tmp_path: Path):
    bundle = tmp_path / "oversized-member.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("master.mp4", b"x" * 64)
    with pytest.raises(RecoveryLimitExceeded, match="container_member_bytes_exceeded"):
        sha256_zip_member(bundle, "master.mp4", max_member_bytes=32)


def test_zip_entry_count_limit_is_enforced_before_member_streaming(tmp_path: Path):
    bundle = tmp_path / "too-many-members.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("master.mp4", b"master")
        archive.writestr("one.json", b"{}")
        archive.writestr("two.json", b"{}")
    with pytest.raises(RecoveryLimitExceeded, match="zip_entry_count_exceeded"):
        sha256_zip_member(bundle, "master.mp4", max_zip_entries=2)


def test_high_ratio_zip_member_is_rejected_before_decompression(tmp_path: Path):
    master = b"\0" * (1024 * 1024)
    bundle = tmp_path / "zip-bomb-shape.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("master.mp4", master)

    result = verify_recovery(
        RecoveryContract(
            MasterIdentity("master", digest(master), len(master)),
            RecoveryCandidate(
                "compressed",
                "local_file",
                "local:zip-bomb-shape",
                container_member="master.mp4",
            ),
        ),
        bundle,
    )

    assert result.status == RECOVERY_LIMIT_EXCEEDED
    assert result.authority == "NONE"
    assert result.observed_sha256 is None
    assert result.observed_container_sha256 == digest(bundle.read_bytes())
    assert result.errors[0].startswith("container_member_compression_ratio_exceeded:")
