from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math
from typing import Iterable


class BenchmarkEvidenceError(ValueError):
    pass


class BriefStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class BenchmarkBriefEvidence:
    evidence_id: str
    brief_id: str
    style_family: str
    brief_sha256: str
    artifact_sha256: str | None
    test_run_id: str
    status: BriefStatus
    quality_score: float | None = None
    findings: tuple[str, ...] = ()
    assertions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (("evidence_id", self.evidence_id), ("brief_id", self.brief_id), ("style_family", self.style_family), ("test_run_id", self.test_run_id)):
            if not isinstance(value, str) or not value.strip() or len(value) > 160:
                raise BenchmarkEvidenceError(f"{name} must be a bounded non-empty string")
        _require_sha(self.brief_sha256, "brief_sha256")
        if self.artifact_sha256 is not None:
            _require_sha(self.artifact_sha256, "artifact_sha256")
        if self.quality_score is not None and (not isinstance(self.quality_score, (int, float)) or isinstance(self.quality_score, bool) or not math.isfinite(float(self.quality_score)) or not 0 <= float(self.quality_score) <= 10):
            raise BenchmarkEvidenceError("quality_score must be finite and in [0,10]")
        if self.status is BriefStatus.PASS:
            if self.artifact_sha256 is None:
                raise BenchmarkEvidenceError("PASS requires artifact_sha256")
            if self.quality_score is None:
                raise BenchmarkEvidenceError("PASS requires quality_score")
            if not self.assertions:
                raise BenchmarkEvidenceError("PASS requires explicit assertions")
        if self.status in {BriefStatus.FAIL, BriefStatus.BLOCKED} and not self.findings:
            raise BenchmarkEvidenceError("non-PASS evidence requires findings")

    def content_hash(self) -> str:
        return _hash({
            "evidence_id": self.evidence_id,
            "brief_id": self.brief_id,
            "style_family": self.style_family,
            "brief_sha256": self.brief_sha256,
            "artifact_sha256": self.artifact_sha256,
            "test_run_id": self.test_run_id,
            "status": self.status.value,
            "quality_score": self.quality_score,
            "findings": list(self.findings),
            "assertions": list(self.assertions),
        })


@dataclass(frozen=True)
class LegacyBenchmarkClaim:
    brief_count: int
    style_count: int
    mapped_to_brief_ids: bool = False
    authority_effect: str = "NONE"

    def __post_init__(self) -> None:
        if self.brief_count < 0 or self.style_count < 0:
            raise BenchmarkEvidenceError("legacy aggregate counts cannot be negative")
        if self.mapped_to_brief_ids or self.authority_effect != "NONE":
            raise BenchmarkEvidenceError("legacy aggregate claim cannot grant per-brief authority")


@dataclass(frozen=True)
class BenchmarkMetrics:
    total_briefs: int
    passed_briefs: int
    failed_briefs: int
    blocked_briefs: int
    style_families_observed: tuple[str, ...]
    apsr: float
    gsr: float
    mean_quality: float | None
    authoritative: bool
    blockers: tuple[str, ...]
    evidence_hash: str


class BenchmarkLedger:
    def __init__(self) -> None:
        self._evidence: dict[str, BenchmarkBriefEvidence] = {}

    def append(self, evidence: BenchmarkBriefEvidence) -> None:
        previous = self._evidence.get(evidence.evidence_id)
        if previous is not None:
            if previous.content_hash() == evidence.content_hash():
                return
            raise BenchmarkEvidenceError("conflicting evidence_id reuse")
        self._evidence[evidence.evidence_id] = evidence

    def metrics(self, *, required_briefs: int = 25, required_styles: int = 5, release_quality: float = 9.0) -> BenchmarkMetrics:
        if required_briefs <= 0 or required_styles <= 0:
            raise BenchmarkEvidenceError("required counts must be positive")
        by_brief: dict[str, list[BenchmarkBriefEvidence]] = {}
        for item in self._evidence.values():
            by_brief.setdefault(item.brief_id, []).append(item)

        effective: list[BenchmarkBriefEvidence] = []
        ambiguous: list[str] = []
        for brief_id, items in sorted(by_brief.items()):
            payloads = {item.content_hash() for item in items}
            if len(items) > 1 and len(payloads) > 1:
                ambiguous.append(brief_id)
                continue
            effective.append(items[0])

        passed = [item for item in effective if item.status is BriefStatus.PASS]
        failed = [item for item in effective if item.status is BriefStatus.FAIL]
        blocked = [item for item in effective if item.status is BriefStatus.BLOCKED]
        styles = tuple(sorted({item.style_family for item in passed}))
        total = len(effective) + len(ambiguous)
        apsr = len(passed) / required_briefs
        # GSR is generalization success: fraction of required style families with at least one passing brief.
        gsr = min(len(styles) / required_styles, 1.0)
        scores = [float(item.quality_score) for item in passed if item.quality_score is not None]
        mean_quality = sum(scores) / len(scores) if scores else None
        blockers: list[str] = []
        if ambiguous:
            blockers.append(f"ambiguous_brief_revisions:{','.join(ambiguous)}")
        if len(passed) < required_briefs:
            blockers.append(f"passed_briefs:{len(passed)}/{required_briefs}")
        if len(styles) < required_styles:
            blockers.append(f"style_families:{len(styles)}/{required_styles}")
        if failed:
            blockers.append(f"failed_briefs:{len(failed)}")
        if blocked:
            blockers.append(f"blocked_briefs:{len(blocked)}")
        if mean_quality is None or mean_quality < release_quality:
            blockers.append(f"mean_quality:{mean_quality if mean_quality is not None else 'NONE'}/{release_quality}")
        authoritative = not blockers and len(passed) == required_briefs
        evidence_hash = _hash({"evidence": sorted(item.content_hash() for item in self._evidence.values()), "required_briefs": required_briefs, "required_styles": required_styles, "release_quality": release_quality})
        return BenchmarkMetrics(
            total_briefs=total,
            passed_briefs=len(passed),
            failed_briefs=len(failed),
            blocked_briefs=len(blocked),
            style_families_observed=styles,
            apsr=apsr,
            gsr=gsr,
            mean_quality=mean_quality,
            authoritative=authoritative,
            blockers=tuple(blockers),
            evidence_hash=evidence_hash,
        )


def _require_sha(value: str, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
        raise BenchmarkEvidenceError(f"{field_name} must be a 64-character SHA256 hex digest")


def _hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
