from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Literal
import hashlib
import json
import math
import os
import stat
import struct
import zipfile
import zlib

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
RECOVERY_LIMIT_EXCEEDED = "RECOVERY_LIMIT_EXCEEDED"

# Availability/security ceilings for already-materialized recovery candidates.
# They are deliberately generous for production video masters while preventing
# unbounded hashing/decompression and high-ratio ZIP bomb payloads.
MAX_RECOVERY_CONTAINER_BYTES = 16 * 1024 * 1024 * 1024
MAX_RECOVERY_MEMBER_BYTES = 8 * 1024 * 1024 * 1024
MAX_RECOVERY_COMPRESSION_RATIO = 200.0
MAX_RECOVERY_ZIP_ENTRIES = 10_000
MAX_RECOVERY_DIRECTORY_BYTES = 16 * 1024 * 1024


class RecoveryLimitExceeded(ValueError):
    """A recovery candidate exceeded a bounded resource-safety contract."""


class RecoveryInputError(ValueError):
    """A bounded diagnostic for malformed or concurrently changed local input."""


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
        if self.expected_bytes is not None:
            _positive_int(self.expected_bytes, "expected_bytes")
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
    if not isinstance(value, str):
        raise ValueError(f"invalid_{field}")
    token = value.lower()
    if len(token) != 64 or any(char not in "0123456789abcdef" for char in token):
        raise ValueError(f"invalid_{field}")


def _positive_int(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")


def _zip_limits(member_bytes: int, ratio: float, entries: int, directory_bytes: int) -> None:
    _positive_int(member_bytes, "max_member_bytes")
    _positive_int(entries, "max_zip_entries")
    _positive_int(directory_bytes, "max_directory_bytes")
    try:
        valid = (not isinstance(ratio, bool) and isinstance(ratio, (int, float))
                 and math.isfinite(ratio) and ratio > 0)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("max_compression_ratio must be finite and positive")


def _validate_zip_member(member: str) -> None:
    # Refuse names whose interpretation changes under pathlib, Windows, or ZIP's
    # NUL truncation. This verifier never extracts archive members to disk.
    if (not isinstance(member, str) or not member.strip() or "\\" in member
            or ":" in member or any(ord(c) < 32 or ord(c) == 127 for c in member)):
        raise ValueError("unsafe_container_member")
    pure = PurePosixPath(member)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in member.split("/")):
        raise ValueError("unsafe_container_member")


def _file_revision(value: os.stat_result) -> tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


@contextmanager
def _open_candidate(path: Path):
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise RecoveryInputError("candidate_not_regular_file")
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as handle:
        opened = os.fstat(handle.fileno())
        if not stat.S_ISREG(opened.st_mode) or _file_revision(opened) != _file_revision(before):
            raise RecoveryInputError("candidate_changed_during_open")
        yield handle
        if _file_revision(os.fstat(handle.fileno())) != _file_revision(opened):
            raise RecoveryInputError("candidate_changed_during_verification")


def _sha256_stream(handle: BinaryIO, max_bytes: int, label: str) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    while True:
        # At most limit + 1 bytes are consumed, even if the file grows mid-read.
        chunk = handle.read(min(1024 * 1024, max_bytes - size + 1))
        if not chunk:
            break
        size += len(chunk)
        if size > max_bytes:
            raise RecoveryLimitExceeded(f"{label}_bytes_exceeded:limit={max_bytes}:observed={size}")
        digest.update(chunk)
    return digest.hexdigest(), size


def _sha256_container(handle: BinaryIO, max_bytes: int) -> tuple[str, int]:
    size = os.fstat(handle.fileno()).st_size
    if size > max_bytes:
        raise RecoveryLimitExceeded(f"container_bytes_exceeded:limit={max_bytes}:declared={size}")
    handle.seek(0)
    return _sha256_stream(handle, max_bytes, "container")


def sha256_path(path: Path, *, max_bytes: int = MAX_RECOVERY_CONTAINER_BYTES) -> tuple[str, int]:
    _positive_int(max_bytes, "max_bytes")
    with _open_candidate(path) as handle:
        return _sha256_container(handle, max_bytes)


def _read_at(handle: BinaryIO, offset: int, size: int, file_size: int) -> bytes:
    if offset < 0 or size < 0 or offset + size > file_size:
        raise RecoveryInputError("invalid_zip_metadata_bounds")
    handle.seek(offset)
    data = handle.read(size)
    if len(data) != size:
        raise RecoveryInputError("truncated_zip_metadata")
    return data


def _preflight_zip(handle: BinaryIO, max_entries: int, max_directory_bytes: int) -> int:
    """Bound metadata BEFORE ZipFile allocates its central directory / ZipInfo list.

    Accept single-disk ZIP and fixed-footer ZIP64 bundles. Reject prepended
    data with inconsistent offsets, trailing junk, split disks and ZIP64 extensible footers.
    Only fixed-size headers are read here; zipfile still validates/decompresses data.
    """
    size = os.fstat(handle.fileno()).st_size
    tail_size = min(size, 22 + 65535)
    tail = _read_at(handle, size - tail_size, tail_size, size)
    pos = tail.rfind(b"PK\x05\x06")
    if pos < 0 or pos + 22 > len(tail):
        raise RecoveryInputError("missing_zip_footer")
    footer = struct.unpack("<4s4H2LH", tail[pos:pos + 22])
    _, disk, cd_disk, disk_entries, entries, cd_size, cd_offset, comment_size = footer
    footer_offset = size - tail_size + pos
    if pos + 22 + comment_size != len(tail) or disk or cd_disk:
        raise RecoveryInputError("unsupported_zip_layout")
    directory_end = footer_offset
    locator = (_read_at(handle, footer_offset - 20, 20, size)
               if footer_offset >= 20 else b"")
    if locator.startswith(b"PK\x06\x07"):
        _, disk64, offset64, disks = struct.unpack("<4sLQL", locator)
        if disk64 or disks != 1:
            raise RecoveryInputError("unsupported_split_zip64")
        end64 = struct.unpack("<4sQ2H2L4Q", _read_at(handle, offset64, 56, size))
        if end64[0] != b"PK\x06\x06" or end64[1] != 44 or offset64 + 56 != footer_offset - 20:
            raise RecoveryInputError("unsupported_zip64_footer")
        if end64[4] or end64[5]:
            raise RecoveryInputError("unsupported_split_zip64")
        actual = end64[6:10]
        for legacy, resolved, sentinel in zip((disk_entries, entries, cd_size, cd_offset),
                                               actual, (65535, 65535, 0xffffffff, 0xffffffff)):
            if legacy not in (resolved, sentinel):
                raise RecoveryInputError("inconsistent_zip64_footer")
        disk_entries, entries, cd_size, cd_offset = actual
        directory_end = offset64
    elif entries == 65535 or cd_size == 0xffffffff or cd_offset == 0xffffffff:
        raise RecoveryInputError("missing_zip64_footer")
    if entries > max_entries:
        raise RecoveryLimitExceeded(f"zip_entry_count_exceeded:limit={max_entries}:declared={entries}")
    if cd_size > max_directory_bytes:
        raise RecoveryLimitExceeded(f"zip_directory_bytes_exceeded:limit={max_directory_bytes}:declared={cd_size}")
    if disk_entries != entries or cd_offset + cd_size != directory_end:
        raise RecoveryInputError("inconsistent_zip_directory")
    # Count the physical records as well: a forged EOCD entry count is not a limit.
    cursor, count = cd_offset, 0
    while cursor < directory_end:
        header = _read_at(handle, cursor, 46, directory_end)
        if header[:4] != b"PK\x01\x02":
            raise RecoveryInputError("invalid_zip_directory_record")
        name_size, extra_size, note_size = struct.unpack_from("<3H", header, 28)
        cursor += 46 + name_size + extra_size + note_size
        if cursor > directory_end:
            raise RecoveryInputError("truncated_zip_directory_record")
        count += 1
        if count > max_entries:
            raise RecoveryLimitExceeded(f"zip_entry_count_exceeded:limit={max_entries}:observed={count}")
    if count != entries:
        raise RecoveryInputError("inconsistent_zip_entry_count")
    handle.seek(0)
    return count


class _MetadataReader:
    """Also cap constructor reads if an external writer races the preflight."""
    def __init__(self, handle: BinaryIO, budget: int):
        self.handle = handle
        self.budget: int | None = budget

    def __getattr__(self, name):
        return getattr(self.handle, name)

    def read(self, size: int = -1) -> bytes:
        if self.budget is not None:
            if size < 0:
                size = max(0, os.fstat(self.handle.fileno()).st_size - self.handle.tell())
            if size > self.budget:
                raise RecoveryLimitExceeded("zip_metadata_read_budget_exceeded")
            self.budget -= size
        return self.handle.read(size)


def _sha256_zip_handle(handle: BinaryIO, member: str, max_member_bytes: int,
                       max_compression_ratio: float, max_zip_entries: int,
                       max_directory_bytes: int) -> tuple[str, int]:
    entries = _preflight_zip(handle, max_zip_entries, max_directory_bytes)
    reader = _MetadataReader(handle, max_directory_bytes + 2 * (65535 + 22) + 128)
    with zipfile.ZipFile(reader, "r") as archive:
        reader.budget = None  # Member reads have their own uncompressed-byte ceiling.
        infos = archive.infolist()
        if len(infos) != entries:
            raise RecoveryInputError("zip_metadata_changed_after_preflight")
        names = [item.filename for item in infos]
        if len(names) != len(set(names)):
            raise RecoveryInputError("duplicate_container_member")
        info = archive.getinfo(member)
        if info.orig_filename != member or info.volume != 0:
            raise RecoveryInputError("ambiguous_container_member")
        mode = stat.S_IFMT(info.external_attr >> 16)
        if info.is_dir() or mode not in (0, stat.S_IFREG):
            raise RecoveryInputError("container_member_not_regular_file")
        if info.flag_bits & 0x1:
            raise RecoveryInputError("encrypted_container_member")
        # Bound decompressor memory as well as output size. Production bundles use
        # STORED/DEFLATED; dictionary-sized LZMA and other codecs are not accepted.
        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise RecoveryInputError("unsupported_container_compression")
        if info.file_size > max_member_bytes:
            raise RecoveryLimitExceeded(f"container_member_bytes_exceeded:limit={max_member_bytes}:declared={info.file_size}")
        if info.file_size and (info.compress_size <= 0 or
                              info.file_size / info.compress_size > max_compression_ratio):
            raise RecoveryLimitExceeded("container_member_compression_ratio_exceeded:policy")
        with archive.open(info, "r") as stream:
            observed = _sha256_stream(stream, max_member_bytes, "container_member")
        if observed[1] != info.file_size:
            raise RecoveryInputError("container_member_declared_size_mismatch")
        return observed


def sha256_zip_member(path: Path, member: str, *,
                      max_member_bytes: int = MAX_RECOVERY_MEMBER_BYTES,
                      max_compression_ratio: float = MAX_RECOVERY_COMPRESSION_RATIO,
                      max_zip_entries: int = MAX_RECOVERY_ZIP_ENTRIES,
                      max_directory_bytes: int = MAX_RECOVERY_DIRECTORY_BYTES) -> tuple[str, int]:
    _validate_zip_member(member)
    _zip_limits(max_member_bytes, max_compression_ratio, max_zip_entries, max_directory_bytes)
    with _open_candidate(path) as handle:
        if os.fstat(handle.fileno()).st_size > MAX_RECOVERY_CONTAINER_BYTES:
            raise RecoveryLimitExceeded("container_bytes_exceeded")
        return _sha256_zip_handle(handle, member, max_member_bytes,
                                  max_compression_ratio, max_zip_entries, max_directory_bytes)


def _input_reason(exc: Exception) -> str:
    # External ZIP exceptions may contain attacker-supplied names or byte strings.
    return str(exc) if isinstance(exc, RecoveryInputError) else type(exc).__name__


def _limit_result(
    contract: RecoveryContract,
    *,
    container_sha: str | None,
    evidence: list[str],
    exc: RecoveryLimitExceeded,
) -> RecoveryResult:
    return RecoveryResult(
        contract.identity.identity_id,
        contract.candidate.candidate_id,
        RECOVERY_LIMIT_EXCEEDED,
        "NONE",
        None,
        None,
        container_sha,
        (str(exc),),
        tuple(evidence),
    )


def verify_recovery(contract: RecoveryContract, materialized_path: Path) -> RecoveryResult:
    """Hash container and member through ONE regular-file descriptor, with no fetch.

    Identity authority requires expected SHA256, supported ZIP layout, bounded
    metadata/decompression and an unchanged file revision. File replacement cannot
    splice one container's hash onto another container's member. A writer with
    control of the OS/filesystem is outside this local verifier's trust boundary.
    """
    contract.validate()
    evidence = [f"source_kind:{contract.candidate.source_kind}",
                f"locator:{contract.candidate.locator}",
                f"contract_sha256:{contract.content_hash()}"]
    try:
        with _open_candidate(materialized_path) as handle:
            return _verify_recovery_handle(contract, handle, evidence)
    except (OSError, ValueError) as exc:
        status = CANDIDATE_UNAVAILABLE if isinstance(exc, OSError) else INVALID_CONTAINER
        return RecoveryResult(contract.identity.identity_id, contract.candidate.candidate_id,
                              status, "NONE", None, None, None,
                              (f"candidate_read_failed:{_input_reason(exc)}",), tuple(evidence))


def _verify_recovery_handle(contract: RecoveryContract, handle: BinaryIO,
                            evidence: list[str]) -> RecoveryResult:
    identity, candidate = contract.identity, contract.candidate
    try:
        container_sha, container_bytes = _sha256_container(handle, MAX_RECOVERY_CONTAINER_BYTES)
    except RecoveryLimitExceeded as exc:
        return _limit_result(
            contract,
            container_sha=None,
            evidence=evidence,
            exc=exc,
        )
    except OSError as exc:
        return RecoveryResult(
            identity.identity_id,
            candidate.candidate_id,
            CANDIDATE_UNAVAILABLE,
            "NONE",
            None,
            None,
            None,
            (f"candidate_read_failed:{_input_reason(exc)}",),
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
            observed_sha, observed_bytes = _sha256_zip_handle(
                handle, candidate.container_member, MAX_RECOVERY_MEMBER_BYTES,
                MAX_RECOVERY_COMPRESSION_RATIO, MAX_RECOVERY_ZIP_ENTRIES,
                MAX_RECOVERY_DIRECTORY_BYTES,
            )
            evidence.append(f"container_member:{candidate.container_member}")
    except RecoveryLimitExceeded as exc:
        return _limit_result(
            contract,
            container_sha=container_sha,
            evidence=evidence,
            exc=exc,
        )
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, EOFError,
            NotImplementedError, RuntimeError, zlib.error) as exc:
        return RecoveryResult(
            identity.identity_id,
            candidate.candidate_id,
            INVALID_CONTAINER,
            "NONE",
            None,
            None,
            container_sha,
            (f"container_member_unavailable:{_input_reason(exc)}",),
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
