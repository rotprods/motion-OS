from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from src.benchmarks.authority import BenchmarkBriefEvidence, BenchmarkEvidenceError, BriefStatus


MECHANICAL_EVIDENCE_CLASS = "MECHANICAL_RENDER_ONLY"


@dataclass(frozen=True)
class MechanicalBenchmarkEvidence:
    brief_id: str
    style_family: str
    brief_sha256: str
    runtime_spec_sha256: str
    artifact_sha256: str
    test_run_id: str
    source_commit: str
    frame_count: int
    fps: float
    visual_duration_seconds: float
    mechanical_pass: bool
    creative_authority: str
    style_fidelity_authority: str
    evidence_class: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "MechanicalBenchmarkEvidence":
        if not isinstance(payload, dict):
            raise BenchmarkEvidenceError("mechanical evidence payload must be an object")
        required = {
            "brief_id", "style_family", "brief_sha256", "runtime_spec_sha256",
            "artifact_sha256", "test_run_id", "source_commit", "frame_count", "fps",
            "visual_duration_seconds", "mechanical_pass", "creative_authority",
            "style_fidelity_authority", "evidence_class",
        }
        missing = sorted(required - payload.keys())
        if missing:
            raise BenchmarkEvidenceError(f"mechanical evidence missing fields: {missing}")
        evidence = cls(**{key: payload[key] for key in required})
        evidence._validate()
        return evidence

    def _validate(self) -> None:
        for name, value in (("brief_id", self.brief_id), ("style_family", self.style_family), ("test_run_id", self.test_run_id)):
            if not isinstance(value, str) or not value.strip() or len(value) > 160:
                raise BenchmarkEvidenceError(f"{name} must be bounded non-empty text")
        for name, value in (("brief_sha256", self.brief_sha256), ("runtime_spec_sha256", self.runtime_spec_sha256), ("artifact_sha256", self.artifact_sha256)):
            if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
                raise BenchmarkEvidenceError(f"{name} must be SHA256")
        if not isinstance(self.mechanical_pass, bool):
            raise BenchmarkEvidenceError("mechanical_pass must be literal boolean")
        if self.mechanical_pass is not True:
            raise BenchmarkEvidenceError("mechanical evidence adapter accepts only mechanically passing artifacts")
        if isinstance(self.frame_count, bool) or not isinstance(self.frame_count, int) or self.frame_count <= 0:
            raise BenchmarkEvidenceError("frame_count must be positive integer")
        if isinstance(self.fps, bool) or not isinstance(self.fps, (int, float)) or not math.isfinite(float(self.fps)) or self.fps <= 0:
            raise BenchmarkEvidenceError("fps must be finite positive number")
        if isinstance(self.visual_duration_seconds, bool) or not isinstance(self.visual_duration_seconds, (int, float)) or not math.isfinite(float(self.visual_duration_seconds)) or self.visual_duration_seconds <= 0:
            raise BenchmarkEvidenceError("visual_duration_seconds must be finite positive number")
        expected = self.frame_count / float(self.fps)
        if abs(expected - float(self.visual_duration_seconds)) > 1e-9:
            raise BenchmarkEvidenceError("visual duration must equal frame_count/fps")
        if self.evidence_class != MECHANICAL_EVIDENCE_CLASS:
            raise BenchmarkEvidenceError("mechanical evidence class mismatch")
        if self.creative_authority != "BLOCKED" or self.style_fidelity_authority != "BLOCKED":
            raise BenchmarkEvidenceError("mechanical render may not claim creative or style-fidelity authority")

    def to_blocked_ledger_entry(self) -> BenchmarkBriefEvidence:
        # Mechanical output proves renderer/artifact mechanics only. It must never become an
        # APSR/GSR PASS until a separate, authoritative creative/style review is bound.
        return BenchmarkBriefEvidence(
            evidence_id=f"mechanical:{self.test_run_id}:{self.brief_id}",
            brief_id=self.brief_id,
            style_family=self.style_family,
            brief_sha256=self.brief_sha256,
            artifact_sha256=self.artifact_sha256,
            test_run_id=self.test_run_id,
            status=BriefStatus.BLOCKED,
            quality_score=None,
            findings=(
                "creative_review_missing",
                "style_fidelity_review_missing",
                "mechanical_render_only",
            ),
            assertions=(
                "artifact_hash_bound",
                "frame_count_fps_duration_bound",
            ),
        )
