from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, Sequence
import hashlib
import json
import math


class TemporalEvidenceError(ValueError):
    """Raised when full-video evidence is incomplete, inconsistent, or unbound."""


@dataclass(frozen=True)
class TemporalSample:
    frame_index: int
    timestamp_ms: int
    sha256: str
    observations: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if self.frame_index < 0 or self.timestamp_ms < 0:
            raise TemporalEvidenceError("sample position must be non-negative")
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256.lower()):
            raise TemporalEvidenceError("sample sha256 must be a 64-character hex digest")


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
        if self.frame_count <= 0 or not math.isfinite(self.fps) or self.fps <= 0 or self.duration_ms <= 0:
            raise TemporalEvidenceError("frame_count, fps and duration_ms must be positive")
        if len(self.media_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.media_sha256.lower()):
            raise TemporalEvidenceError("media_sha256 must be a 64-character hex digest")
        if not self.samples:
            raise TemporalEvidenceError("full-video evidence requires samples")
        indices = [sample.frame_index for sample in self.samples]
        if indices != sorted(set(indices)):
            raise TemporalEvidenceError("samples must be unique and sorted by frame_index")
        if indices[0] != 0 or indices[-1] != self.frame_count - 1:
            raise TemporalEvidenceError("sampling must bind both first and last frame")
        if any(index >= self.frame_count for index in indices):
            raise TemporalEvidenceError("sample frame exceeds media frame_count")
        visual_duration_ms = self.frame_count / self.fps * 1000.0
        if abs(visual_duration_ms - self.duration_ms) > max(1000.0 / self.fps, 1.0):
            raise TemporalEvidenceError("duration must agree with frame_count/fps authority")
        for sample in self.samples:
            expected_ms = round(sample.frame_index / self.fps * 1000.0)
            if abs(sample.timestamp_ms - expected_ms) > 1:
                raise TemporalEvidenceError(
                    f"sample timestamp must agree with decoded frame clock: frame={sample.frame_index} "
                    f"expected_ms={expected_ms} actual_ms={sample.timestamp_ms}"
                )
        if self.provider_run_id is not None and not str(self.provider_run_id).strip():
            raise TemporalEvidenceError("provider_run_id must be non-empty when supplied")

    @property
    def coverage_ratio(self) -> float:
        return len(self.samples) / self.frame_count

    @property
    def authoritative_provider_evidence(self) -> bool:
        return bool(self.provider_attested_full_video and self.provider_run_id and self.provider != "unbound")

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
class TemporalDefect:
    code: str
    severity: str
    start_ms: int
    end_ms: int
    evidence_frame_indices: tuple[int, ...]
    description: str

    def __post_init__(self) -> None:
        if self.severity not in {"P0", "P1", "P2", "P3"}:
            raise TemporalEvidenceError("unsupported defect severity")
        if self.start_ms < 0 or self.end_ms < self.start_ms:
            raise TemporalEvidenceError("invalid temporal defect interval")
        if not self.evidence_frame_indices:
            raise TemporalEvidenceError("temporal defect requires frame evidence")


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


class TemporalInferenceProvider(Protocol):
    name: str

    def evaluate_full_video(self, media_path: Path, context: dict[str, Any], evidence: FullVideoEvidence) -> dict[str, Any]: ...


def uniform_sample_indices(frame_count: int, *, target_samples: int = 24) -> tuple[int, ...]:
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
    indices = uniform_sample_indices(frame_count, target_samples=target_samples)
    missing = [index for index in indices if index not in frame_hashes]
    if missing:
        raise TemporalEvidenceError(f"missing required sampled frame hashes: {missing}")
    samples = tuple(
        TemporalSample(
            frame_index=index,
            timestamp_ms=round(index / fps * 1000),
            sha256=frame_hashes[index],
            observations=tuple((observations or {}).get(index, ())),
        )
        for index in indices
    )
    return FullVideoEvidence(
        media_sha256=media_sha256,
        frame_count=frame_count,
        fps=fps,
        duration_ms=round(frame_count / fps * 1000),
        samples=samples,
        provider=provider,
        provider_run_id=provider_run_id,
        provider_attested_full_video=provider_attested_full_video,
    )


def critique_from_provider_payload(evidence: FullVideoEvidence, payload: dict[str, Any]) -> TemporalCritique:
    if not isinstance(payload, dict):
        raise TemporalEvidenceError("provider critique payload must be an object")
    provider = str(payload.get("provider", evidence.provider))
    payload_run_id = payload.get("provider_run_id")
    payload_run_id = None if payload_run_id is None else str(payload_run_id).strip()
    if evidence.authoritative_provider_evidence:
        if provider != evidence.provider:
            raise TemporalEvidenceError("provider identity does not match bound full-video evidence")
        if payload_run_id != evidence.provider_run_id:
            raise TemporalEvidenceError("provider_run_id does not match bound full-video evidence")

    score = float(payload.get("score", 0.0))
    dimensions = {str(k): float(v) for k, v in dict(payload.get("dimensions", {})).items()}
    if not math.isfinite(score) or any(not math.isfinite(v) for v in dimensions.values()):
        raise TemporalEvidenceError("critic scores must be finite")
    if not 0.0 <= score <= 10.0 or any(not 0.0 <= value <= 10.0 for value in dimensions.values()):
        raise TemporalEvidenceError("critic scores must be in [0, 10]")
    defects = tuple(
        TemporalDefect(
            code=str(item["code"]),
            severity=str(item["severity"]),
            start_ms=int(item["start_ms"]),
            end_ms=int(item["end_ms"]),
            evidence_frame_indices=tuple(int(v) for v in item["evidence_frame_indices"]),
            description=str(item.get("description", "")),
        )
        for item in payload.get("defects", ())
    )
    samples_by_index = {sample.frame_index: sample for sample in evidence.samples}
    sampled = set(samples_by_index)
    for defect in defects:
        if not set(defect.evidence_frame_indices).issubset(sampled):
            raise TemporalEvidenceError("defect references frames outside bound evidence")
        if defect.end_ms > evidence.duration_ms:
            raise TemporalEvidenceError("defect interval exceeds video duration")
        outside_interval = [
            frame_index for frame_index in defect.evidence_frame_indices
            if not (defect.start_ms <= samples_by_index[frame_index].timestamp_ms <= defect.end_ms)
        ]
        if outside_interval:
            raise TemporalEvidenceError(
                f"defect evidence frames fall outside defect interval: {outside_interval}"
            )

    requested_authority = payload.get("authoritative", False) is True
    authoritative = bool(
        requested_authority
        and evidence.authoritative_provider_evidence
        and provider == evidence.provider
        and payload_run_id == evidence.provider_run_id
    )
    recommendation = str(payload.get("recommendation", "ITERATE"))
    if recommendation == "RELEASE" and (not authoritative or any(d.severity in {"P0", "P1"} for d in defects)):
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
    )


def release_eligible(critique: TemporalCritique, *, minimum_score: float = 9.0) -> bool:
    return bool(
        critique.authoritative
        and critique.score >= minimum_score
        and critique.recommendation == "RELEASE"
        and not any(defect.severity in {"P0", "P1"} for defect in critique.defects)
    )
