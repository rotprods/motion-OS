from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, Sequence
import hashlib
import json
import math


class TemporalEvidenceError(ValueError):
    """Raised when full-video evidence is incomplete, inconsistent, or unbound."""


_MAX_PROVIDER_LEN = 128
_MAX_RUN_ID_LEN = 256
_MAX_ATTESTATION_ID_LEN = 256
_MAX_DIMENSION_LEN = 128
_MAX_DEFECT_CODE_LEN = 128
_MAX_DESCRIPTION_LEN = 4096
_ALLOWED_RECOMMENDATIONS = {"RELEASE", "ITERATE", "BLOCK"}


def _strict_identity(value: Any, field_name: str, *, max_length: int) -> str:
    if not isinstance(value, str):
        raise TemporalEvidenceError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise TemporalEvidenceError(f"{field_name} must be non-empty and have no surrounding whitespace")
    if len(value) > max_length:
        raise TemporalEvidenceError(f"{field_name} exceeds maximum length {max_length}")
    return value


def _strict_sha256(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TemporalEvidenceError(f"{field_name} must be a string")
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
        raise TemporalEvidenceError(f"{field_name} must be a 64-character hex digest")
    return value


def _strict_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TemporalEvidenceError(f"{field_name} must be a finite numeric scalar, not a boolean or string")
    number = float(value)
    if not math.isfinite(number):
        raise TemporalEvidenceError(f"{field_name} must be finite")
    return number


def _strict_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TemporalEvidenceError(f"{field_name} must be an integer, not a boolean or coercible scalar")
    return value


def _strict_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TemporalEvidenceError(f"{field_name} must be a literal boolean")
    return value


@dataclass(frozen=True)
class TemporalSample:
    frame_index: int
    timestamp_ms: int
    sha256: str
    observations: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        _strict_int(self.frame_index, "sample frame_index")
        _strict_int(self.timestamp_ms, "sample timestamp_ms")
        if self.frame_index < 0 or self.timestamp_ms < 0:
            raise TemporalEvidenceError("sample position must be non-negative")
        _strict_sha256(self.sha256, "sample sha256")


@dataclass(frozen=True)
class FullVideoEvidence:
    media_sha256: str
    frame_count: int
    fps: float
    duration_ms: int
    samples: tuple[TemporalSample, ...]
    sampling_policy: str = "uniform_plus_boundaries_v1"
    provider: str = "unbound"
    provider_run_id: str | None = None
    provider_attested_full_video: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _strict_int(self.frame_count, "frame_count")
        _strict_int(self.duration_ms, "duration_ms")
        fps = _strict_number(self.fps, "fps")
        if self.frame_count <= 0 or fps <= 0 or self.duration_ms <= 0:
            raise TemporalEvidenceError("frame_count, fps and duration_ms must be positive")
        _strict_sha256(self.media_sha256, "media_sha256")
        _strict_identity(self.provider, "provider", max_length=_MAX_PROVIDER_LEN)
        if self.provider_run_id is not None:
            _strict_identity(self.provider_run_id, "provider_run_id", max_length=_MAX_RUN_ID_LEN)
        _strict_bool(self.provider_attested_full_video, "provider_attested_full_video")
        if not self.samples:
            raise TemporalEvidenceError("full-video evidence requires samples")
        indices = [sample.frame_index for sample in self.samples]
        if indices != sorted(set(indices)):
            raise TemporalEvidenceError("samples must be unique and sorted by frame_index")
        if indices[0] != 0 or indices[-1] != self.frame_count - 1:
            raise TemporalEvidenceError("sampling must bind both first and last frame")
        if any(index >= self.frame_count for index in indices):
            raise TemporalEvidenceError("sample frame exceeds media frame_count")
        visual_duration_ms = self.frame_count / fps * 1000.0
        if abs(visual_duration_ms - self.duration_ms) > max(1000.0 / fps, 1.0):
            raise TemporalEvidenceError("duration must agree with frame_count/fps authority")
        for sample in self.samples:
            expected_ms = round(sample.frame_index / fps * 1000.0)
            if abs(sample.timestamp_ms - expected_ms) > 1:
                raise TemporalEvidenceError(
                    f"sample timestamp must agree with decoded frame clock: frame={sample.frame_index} "
                    f"expected_ms={expected_ms} actual_ms={sample.timestamp_ms}"
                )

    @property
    def coverage_ratio(self) -> float:
        return len(self.samples) / self.frame_count

    @property
    def provider_binding_prepared(self) -> bool:
        return bool(self.provider != "unbound" and self.provider_run_id is not None)

    @property
    def authoritative_provider_evidence(self) -> bool:
        """Local caller state can never by itself constitute external provider authority."""
        return False

    def content_hash(self) -> str:
        payload = {
            "media_sha256": self.media_sha256,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "duration_ms": self.duration_ms,
            "sampling_policy": self.sampling_policy,
            "provider": self.provider,
            "provider_run_id": self.provider_run_id,
            "provider_attested_full_video": self.provider_attested_full_video,
            "samples": [
                {
                    "frame_index": s.frame_index,
                    "timestamp_ms": s.timestamp_ms,
                    "sha256": s.sha256,
                    "observations": list(s.observations),
                }
                for s in self.samples
            ],
            "metadata": self.metadata,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class ProviderAuthorityAttestation:
    provider: str
    provider_run_id: str
    media_sha256: str
    full_video_scope: bool
    provider_attestation_id: str

    def __post_init__(self) -> None:
        _strict_identity(self.provider, "provider", max_length=_MAX_PROVIDER_LEN)
        _strict_identity(self.provider_run_id, "provider_run_id", max_length=_MAX_RUN_ID_LEN)
        _strict_sha256(self.media_sha256, "media_sha256")
        if _strict_bool(self.full_video_scope, "full_video_scope") is not True:
            raise TemporalEvidenceError("full_video_scope must be literal true for provider authority")
        _strict_identity(
            self.provider_attestation_id,
            "provider_attestation_id",
            max_length=_MAX_ATTESTATION_ID_LEN,
        )


@dataclass(frozen=True)
class TemporalDefect:
    code: str
    severity: str
    start_ms: int
    end_ms: int
    evidence_frame_indices: tuple[int, ...]
    description: str

    def __post_init__(self) -> None:
        _strict_identity(self.code, "defect code", max_length=_MAX_DEFECT_CODE_LEN)
        if self.severity not in {"P0", "P1", "P2", "P3"}:
            raise TemporalEvidenceError("unsupported defect severity")
        _strict_int(self.start_ms, "defect start_ms")
        _strict_int(self.end_ms, "defect end_ms")
        if self.start_ms < 0 or self.end_ms < self.start_ms:
            raise TemporalEvidenceError("invalid temporal defect interval")
        if not self.evidence_frame_indices:
            raise TemporalEvidenceError("temporal defect requires frame evidence")
        if any(isinstance(v, bool) or not isinstance(v, int) for v in self.evidence_frame_indices):
            raise TemporalEvidenceError("defect evidence frame indices must be integers")
        if not isinstance(self.description, str) or len(self.description) > _MAX_DESCRIPTION_LEN:
            raise TemporalEvidenceError("defect description must be a bounded string")


@dataclass(frozen=True)
class TemporalCritique:
    provider: str
    provider_run_id: str | None
    media_sha256: str
    score: float
    dimensions: dict[str, float]
    defects: tuple[TemporalDefect, ...]
    evidence_hash: str
    authoritative: bool
    recommendation: str
    provider_attestation_id: str | None = None
    full_video_scope: bool = False


class TemporalInferenceProvider(Protocol):
    name: str

    def evaluate_full_video(self, media_path: Path, context: dict[str, Any], evidence: FullVideoEvidence) -> dict[str, Any]: ...


def uniform_sample_indices(frame_count: int, *, target_samples: int = 24) -> tuple[int, ...]:
    _strict_int(frame_count, "frame_count")
    _strict_int(target_samples, "target_samples")
    if frame_count <= 0 or target_samples < 2:
        raise TemporalEvidenceError("frame_count must be positive and target_samples >= 2")
    if frame_count <= target_samples:
        return tuple(range(frame_count))
    last = frame_count - 1
    indices = {0, last}
    for i in range(1, target_samples - 1):
        indices.add(round(i * last / (target_samples - 1)))
    return tuple(sorted(indices))


def build_temporal_evidence(
    *,
    media_sha256: str,
    frame_count: int,
    fps: float,
    frame_hashes: dict[int, str],
    observations: dict[int, Sequence[dict[str, Any]]] | None = None,
    provider: str = "unbound",
    provider_run_id: str | None = None,
    provider_attested_full_video: bool = False,
    target_samples: int = 24,
) -> FullVideoEvidence:
    fps_value = _strict_number(fps, "fps")
    if fps_value <= 0:
        raise TemporalEvidenceError("fps must be positive")
    indices = uniform_sample_indices(frame_count, target_samples=target_samples)
    missing = [index for index in indices if index not in frame_hashes]
    if missing:
        raise TemporalEvidenceError(f"missing required sampled frame hashes: {missing}")
    samples = tuple(
        TemporalSample(
            frame_index=index,
            timestamp_ms=round(index / fps_value * 1000),
            sha256=frame_hashes[index],
            observations=tuple((observations or {}).get(index, ())),
        )
        for index in indices
    )
    return FullVideoEvidence(
        media_sha256=media_sha256,
        frame_count=frame_count,
        fps=fps_value,
        duration_ms=round(frame_count / fps_value * 1000),
        samples=samples,
        provider=provider,
        provider_run_id=provider_run_id,
        provider_attested_full_video=provider_attested_full_video,
    )


def _provider_authority_attestation(
    evidence: FullVideoEvidence,
    payload: dict[str, Any],
    *,
    requested_authority: bool,
) -> ProviderAuthorityAttestation | None:
    authority_fields = (
        "provider",
        "provider_run_id",
        "media_sha256",
        "full_video_scope",
        "provider_attestation_id",
    )
    if requested_authority:
        missing = [field for field in authority_fields if field not in payload]
        if missing:
            raise TemporalEvidenceError(
                "authoritative provider payload missing required fields: " + ", ".join(missing)
            )
        if not evidence.provider_binding_prepared:
            raise TemporalEvidenceError(
                "authoritative provider payload requires locally prepared provider and provider_run_id bindings"
            )

    provider = evidence.provider
    if "provider" in payload:
        provider = _strict_identity(payload["provider"], "provider", max_length=_MAX_PROVIDER_LEN)
        if evidence.provider != "unbound" and provider != evidence.provider:
            raise TemporalEvidenceError("provider identity does not match bound full-video evidence")

    payload_run_id: str | None = None
    if "provider_run_id" in payload:
        payload_run_id = _strict_identity(
            payload["provider_run_id"], "provider_run_id", max_length=_MAX_RUN_ID_LEN
        )
        if evidence.provider_run_id is not None and payload_run_id != evidence.provider_run_id:
            raise TemporalEvidenceError("provider_run_id does not match bound full-video evidence")

    payload_media_sha256: str | None = None
    if "media_sha256" in payload:
        payload_media_sha256 = _strict_sha256(payload["media_sha256"], "media_sha256")
        if payload_media_sha256 != evidence.media_sha256:
            raise TemporalEvidenceError("media_sha256 does not match bound full-video evidence")

    full_video_scope = False
    if "full_video_scope" in payload:
        full_video_scope = _strict_bool(payload["full_video_scope"], "full_video_scope")

    provider_attestation_id: str | None = None
    if "provider_attestation_id" in payload:
        provider_attestation_id = _strict_identity(
            payload["provider_attestation_id"],
            "provider_attestation_id",
            max_length=_MAX_ATTESTATION_ID_LEN,
        )

    if not requested_authority:
        return None

    if provider != evidence.provider:
        raise TemporalEvidenceError("provider identity does not match bound full-video evidence")
    if payload_run_id != evidence.provider_run_id:
        raise TemporalEvidenceError("provider_run_id does not match bound full-video evidence")
    if payload_media_sha256 != evidence.media_sha256:
        raise TemporalEvidenceError("media_sha256 does not match bound full-video evidence")
    if full_video_scope is not True:
        raise TemporalEvidenceError("full_video_scope must be literal true for provider authority")
    if provider_attestation_id is None:
        raise TemporalEvidenceError("provider_attestation_id is required for provider authority")

    return ProviderAuthorityAttestation(
        provider=provider,
        provider_run_id=payload_run_id,
        media_sha256=payload_media_sha256,
        full_video_scope=full_video_scope,
        provider_attestation_id=provider_attestation_id,
    )


def critique_from_provider_payload(evidence: FullVideoEvidence, payload: dict[str, Any]) -> TemporalCritique:
    if not isinstance(payload, dict):
        raise TemporalEvidenceError("provider critique payload must be an object")

    raw_authoritative = payload.get("authoritative", False)
    requested_authority = _strict_bool(raw_authoritative, "authoritative")
    if requested_authority:
        required_critique_fields = ("score", "dimensions", "defects", "recommendation")
        missing = [field for field in required_critique_fields if field not in payload]
        if missing:
            raise TemporalEvidenceError(
                "authoritative provider payload missing critique fields: " + ", ".join(missing)
            )

    attestation = _provider_authority_attestation(
        evidence,
        payload,
        requested_authority=requested_authority,
    )

    provider = evidence.provider
    if "provider" in payload:
        provider = _strict_identity(payload["provider"], "provider", max_length=_MAX_PROVIDER_LEN)

    payload_run_id: str | None = None
    if "provider_run_id" in payload:
        payload_run_id = _strict_identity(
            payload["provider_run_id"], "provider_run_id", max_length=_MAX_RUN_ID_LEN
        )

    score = _strict_number(payload.get("score", 0.0), "critic score")

    raw_dimensions = payload.get("dimensions", {})
    if not isinstance(raw_dimensions, dict):
        raise TemporalEvidenceError("dimensions must be an object")
    dimensions: dict[str, float] = {}
    for key, value in raw_dimensions.items():
        dimension = _strict_identity(key, "dimension name", max_length=_MAX_DIMENSION_LEN)
        dimensions[dimension] = _strict_number(value, f"dimension {dimension}")

    if not 0.0 <= score <= 10.0 or any(not 0.0 <= value <= 10.0 for value in dimensions.values()):
        raise TemporalEvidenceError("critic scores must be in [0, 10]")

    raw_defects = payload.get("defects", ())
    if not isinstance(raw_defects, (list, tuple)):
        raise TemporalEvidenceError("defects must be an array")
    defects_list: list[TemporalDefect] = []
    for item in raw_defects:
        if not isinstance(item, dict):
            raise TemporalEvidenceError("each temporal defect must be an object")
        try:
            code = _strict_identity(item["code"], "defect code", max_length=_MAX_DEFECT_CODE_LEN)
            severity = _strict_identity(item["severity"], "defect severity", max_length=2)
            start_ms = _strict_int(item["start_ms"], "defect start_ms")
            end_ms = _strict_int(item["end_ms"], "defect end_ms")
            raw_frame_indices = item["evidence_frame_indices"]
        except KeyError as exc:
            raise TemporalEvidenceError(f"temporal defect missing required field: {exc.args[0]}") from exc

        if not isinstance(raw_frame_indices, (list, tuple)):
            raise TemporalEvidenceError("defect evidence_frame_indices must be an array")
        evidence_frame_indices = tuple(
            _strict_int(value, "defect evidence frame index") for value in raw_frame_indices
        )
        description_raw = item.get("description", "")
        if not isinstance(description_raw, str) or len(description_raw) > _MAX_DESCRIPTION_LEN:
            raise TemporalEvidenceError("defect description must be a bounded string")
        defects_list.append(
            TemporalDefect(
                code=code,
                severity=severity,
                start_ms=start_ms,
                end_ms=end_ms,
                evidence_frame_indices=evidence_frame_indices,
                description=description_raw,
            )
        )
    defects = tuple(defects_list)

    samples_by_index = {sample.frame_index: sample for sample in evidence.samples}
    sampled = set(samples_by_index)
    for defect in defects:
        if not set(defect.evidence_frame_indices).issubset(sampled):
            raise TemporalEvidenceError("defect references frames outside bound evidence")
        if defect.end_ms > evidence.duration_ms:
            raise TemporalEvidenceError("defect interval exceeds video duration")
        outside_interval = [
            frame_index
            for frame_index in defect.evidence_frame_indices
            if not (defect.start_ms <= samples_by_index[frame_index].timestamp_ms <= defect.end_ms)
        ]
        if outside_interval:
            raise TemporalEvidenceError(
                f"defect evidence frames fall outside defect interval: {outside_interval}"
            )

    raw_recommendation = payload.get("recommendation", "ITERATE")
    recommendation = _strict_identity(raw_recommendation, "recommendation", max_length=16)
    if recommendation not in _ALLOWED_RECOMMENDATIONS:
        raise TemporalEvidenceError("recommendation must be RELEASE, ITERATE, or BLOCK")

    authoritative = attestation is not None
    if recommendation == "RELEASE" and (
        not authoritative or any(d.severity in {"P0", "P1"} for d in defects)
    ):
        recommendation = "BLOCK"

    return TemporalCritique(
        provider=provider,
        provider_run_id=payload_run_id,
        media_sha256=evidence.media_sha256,
        score=score,
        dimensions=dimensions,
        defects=defects,
        evidence_hash=evidence.content_hash(),
        authoritative=authoritative,
        recommendation=recommendation,
        provider_attestation_id=(
            attestation.provider_attestation_id if attestation is not None else None
        ),
        full_video_scope=bool(attestation and attestation.full_video_scope),
    )


def release_eligible(critique: TemporalCritique, *, minimum_score: float = 9.0) -> bool:
    minimum_score_value = _strict_number(minimum_score, "minimum_score")
    return bool(
        critique.authoritative
        and critique.full_video_scope
        and critique.provider_attestation_id
        and critique.score >= minimum_score_value
        and critique.recommendation == "RELEASE"
        and not any(defect.severity in {"P0", "P1"} for defect in critique.defects)
    )
