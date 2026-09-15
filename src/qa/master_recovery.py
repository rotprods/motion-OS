from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal
import hashlib
import json
import zipfile

RecoverySourceKind = Literal[
    "github_actions_artifact",
    "google_drive",
    "local_file",
    "other",
]

RECOVERED_EXACT = "RECOVERED_EXACT"
IDENTITY_UNQUALIFIED = "IDENTITY_UNQUALIFIED"
CANDIDATE_UNAVAILABLE = "CANDIDATE_UNAVAILABLE"
CONTAINER_HASH_MISMATCH = "CONTAINER_HASH_MISMATCH"
MASTER_HASH_MISMATCH = "MASTER_HASH_MISMATCH"
MASTER_SIZE_MISMATCH = "MASTER_SIZE_MISMATCH"
INVALID_CONTAINER = "INVALID_CONTAINER"


@dataclass(frozen=True)
class MasterIdentity:
    identity_id: str
    expected_sha256: str | None
    expected_bytes: int | None = None
    media_role: str = "master"

    def validate(self) -> None:
        if not self.identity_id.strip():
            raise ValueError("master identity requires identity_id")
        if self.expected_sha256 is not None:
            _validate_sha256(self.expected_sha256, field="expected_sha256")
        if self.expected_bytes is not None and self.expected_bytes <= 0:
            raise ValueError("expected_bytes must be positive when supplied")
        if not self.media_role.strip():
            raise ValueError("master identity requires media_role")

    @property
    def identity_qualified(self) -> bool:
        return self.expected_sha256 is not None


@dataclass(frozen=True)
class RecoveryCandidate:
    candidate_id: str
    source_kind: RecoverySourceKind
    locator: str
    container_member: str | None = None
    expected_container_sha256: str | None = None
    source_revision: str | None = None

    def validate(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("recovery candidate requires candidate_id")
        if self.source_kind not in {
            "github_actions_artifact",
            "google_drive",
            "local_file",
            "other",
        }:
            raise ValueError(f"unsupported_recovery_source_kind:{self.source_kind}")
        if not self.locator.strip():
            raise ValueError("recovery candidate requires locator")
        if self.expected_container_sha256 is not None:
            _validate_sha256(self.expected_container_sha256, field="expected_container_sha256")
        if self.container_member is not None:
            _validate_zip_member(self.container_member)


@dataclass(frozen=True)
class RecoveryResult:
    identity_id: str
    candidate_id: str
    status: str
    authority: str
    observed_sha256: str | None
    observed_bytes: int | None
    observed_container_sha256: str | None
    errors: tuple[str, ...]
    evidence: tuple[str, ...]

    @property
    def exact(self) -> bool:
        return self.status == RECOVERED_EXACT and self.authority == "EXACT_IDENTITY_VERIFIED"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["errors"] = list(self.errors)
        payload["evidence"] = list(self.evidence)
        payload["exact"] = self.exact
        return payload


@dataclass(frozen=True)
class RecoveryContract:
    identity: MasterIdentity
    candidate: RecoveryCandidate

    def validate(self) -> None:
        self.identity.validate()
        self.candidate.validate()

    def content_hash(self) -> str:
        self.validate()
        payload = {
            "identity": asdict(self.identity),
            "candidate": asdict(self.candidate),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


def _validate_sha256(value: str, *, field: str) -> None:
    token = value.strip().lower()
    if len(token) != 64 or any(char not in "0123456789abcdef" for char in token):
        raise ValueError(f"invalid_{field}")


def _validate_zip_member(member: str) -> None:
    pure = PurePosixPath(member)
    if not member.strip() or pure.is_absolute() or ".." in pure.parts:
        raise ValueError("unsafe_container_member")


def sha256_path(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def sha256_zip_member(path: Path, member: str) -> tuple[str, int]:
    _validate_zip_member(member)
    digest = hashlib.sha256()
    size = 0
    with zipfile.ZipFile(path, "r") as archive:
        info = archive.getinfo(member)
        if info.is_dir():
            raise ValueError("container_member_is_directory")
        with archive.open(info, "r") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
    return digest.hexdigest(), size


def verify_recovery(contract: RecoveryContract, materialized_path: Path) -> RecoveryResult:
    """Verify a materialized recovery candidate against an immutable media identity.

    This function makes no network calls and never infers identity from dimensions,
    duration, naming, or provenance alone. Authoritative recovery requires an exact
    expected media SHA-256. Container hashes are independently verified when the
    candidate is a durable bundle such as a CI artifact ZIP mirrored to Drive.
    """
    contract.validate()
    identity = contract.identity
    candidate = contract.candidate
    evidence = [
        f"source_kind:{candidate.source_kind}",
        f"locator:{candidate.locator}",
        f"contract_sha256:{contract.content_hash()}",
    ]

    if not materialized_path.exists() or not materialized_path.is_file():
        return RecoveryResult(
            identity.identity_id,
            candidate.candidate_id,
            CANDIDATE_UNAVAILABLE,
            "NONE",
            None,
            None,
            None,
            (f"candidate_path_unavailable:{materialized_path}",),
            tuple(evidence),
        )

    try:
        container_sha, container_bytes = sha256_path(materialized_path)
    except OSError as exc:
        return RecoveryResult(
            identity.identity_id,
            candidate.candidate_id,
            CANDIDATE_UNAVAILABLE,
            "NONE",
            None,
            None,
            None,
            (f"candidate_read_failed:{type(exc).__name__}",),
            tuple(evidence),
        )

    evidence.extend(
        [
            f"materialized_container_sha256:{container_sha}",
            f"materialized_container_bytes:{container_bytes}",
        ]
    )
    if (
        candidate.expected_container_sha256 is not None
        and container_sha != candidate.expected_container_sha256.lower()
    ):
        return RecoveryResult(
            identity.identity_id,
            candidate.candidate_id,
            CONTAINER_HASH_MISMATCH,
            "NONE",
            None,
            None,
            container_sha,
            (
                "container_sha256_mismatch:"
                f"expected={candidate.expected_container_sha256}:observed={container_sha}",
            ),
            tuple(evidence),
        )

    try:
        if candidate.container_member is None:
            observed_sha, observed_bytes = container_sha, container_bytes
        else:
            observed_sha, observed_bytes = sha256_zip_member(
                materialized_path,
                candidate.container_member,
            )
            evidence.append(f"container_member:{candidate.container_member}")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        return RecoveryResult(
            identity.identity_id,
            candidate.candidate_id,
            INVALID_CONTAINER,
            "NONE",
            None,
            None,
            container_sha,
            (f"container_member_unavailable:{type(exc).__name__}",),
            tuple(evidence),
        )

    evidence.extend(
        [
            f"observed_master_sha256:{observed_sha}",
            f"observed_master_bytes:{observed_bytes}",
        ]
    )

    if not identity.identity_qualified:
        return RecoveryResult(
            identity.identity_id,
            candidate.candidate_id,
            IDENTITY_UNQUALIFIED,
            "NONE",
            observed_sha,
            observed_bytes,
            container_sha,
            ("exact_historical_sha256_unknown",),
            tuple(evidence),
        )

    if observed_sha != identity.expected_sha256.lower():
        return RecoveryResult(
            identity.identity_id,
            candidate.candidate_id,
            MASTER_HASH_MISMATCH,
            "NONE",
            observed_sha,
            observed_bytes,
            container_sha,
            (
                "master_sha256_mismatch:"
                f"expected={identity.expected_sha256}:observed={observed_sha}",
            ),
            tuple(evidence),
        )

    if identity.expected_bytes is not None and observed_bytes != identity.expected_bytes:
        return RecoveryResult(
            identity.identity_id,
            candidate.candidate_id,
            MASTER_SIZE_MISMATCH,
            "NONE",
            observed_sha,
            observed_bytes,
            container_sha,
            (
                "master_size_mismatch:"
                f"expected={identity.expected_bytes}:observed={observed_bytes}",
            ),
            tuple(evidence),
        )

    return RecoveryResult(
        identity.identity_id,
        candidate.candidate_id,
        RECOVERED_EXACT,
        "EXACT_IDENTITY_VERIFIED",
        observed_sha,
        observed_bytes,
        container_sha,
        (),
        tuple(evidence),
    )
