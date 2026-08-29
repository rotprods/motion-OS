from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math


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
        if not isinstance(self.status, BriefStatus):
            raise BenchmarkEvidenceError("status must be BriefStatus")
        _require_text_tuple(self.findings, "findings")
        _require_text_tuple(self.assertions, "assertions")
        _require_sha(self.brief_sha256, "brief_sha256")
        if self.artifact_sha256 is not None:
            _require_sha(self.artifact_sha256, "artifact_sha256")
        if self.quality_score is not None and (
            not isinstance(self.quality_score, (int, float))
            or isinstance(self.quality_score, bool)
            or not math.isfinite(float(self.quality_score))
            or not 0 <= float(self.quality_score) <= 10
        ):
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
        if isinstance(self.brief_count, bool) or isinstance(self.style_count, bool):
            raise BenchmarkEvidenceError("legacy aggregate counts must be integers")
        if not isinstance(self.brief_count, int) or not isinstance(self.style_count, int):
            raise BenchmarkEvidenceError("legacy aggregate counts must be integers")
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
    style_pass_counts: tuple[tuple[str, int], ...]
    apsr: float
    gsr: float
    mean_quality: float | None
    minimum_quality: float | None
    authoritative: bool
    blockers: tuple[str, ...]
    evidence_hash: str


class BenchmarkLedger:
    def __init__(self) -> None:
        self._evidence: dict[str, BenchmarkBriefEvidence] = {}

    def append(self, evidence: BenchmarkBriefEvidence) -> None:
        if not isinstance(evidence, BenchmarkBriefEvidence):
            raise BenchmarkEvidenceError("evidence must be BenchmarkBriefEvidence")
        previous = self._evidence.get(evidence.evidence_id)
        if previous is not None:
            if previous.content_hash() == evidence.content_hash():
                return
            raise BenchmarkEvidenceError("conflicting evidence_id reuse")
        self._evidence[evidence.evidence_id] = evidence

    def metrics(
        self,
        *,
        required_briefs: int = 25,
        required_styles: int = 5,
        release_quality: float = 9.0,
        min_passes_per_style: int | None = None,
    ) -> BenchmarkMetrics:
        if isinstance(required_briefs, bool) or isinstance(required_styles, bool):
            raise BenchmarkEvidenceError("required counts must be integers")
        if not isinstance(required_briefs, int) or not isinstance(required_styles, int) or required_briefs <= 0 or required_styles <= 0:
            raise BenchmarkEvidenceError("required counts must be positive integers")
        if not isinstance(release_quality, (int, float)) or isinstance(release_quality, bool) or not math.isfinite(float(release_quality)) or not 0 <= float(release_quality) <= 10:
            raise BenchmarkEvidenceError("release_quality must be finite and in [0,10]")
        if min_passes_per_style is None:
            if required_briefs % required_styles != 0:
                raise BenchmarkEvidenceError("required_briefs must divide evenly by required_styles unless min_passes_per_style is explicit")
            min_passes_per_style = required_briefs // required_styles
        if isinstance(min_passes_per_style, bool) or not isinstance(min_passes_per_style, int) or min_passes_per_style <= 0:
            raise BenchmarkEvidenceError("min_passes_per_style must be a positive integer")

        by_brief: dict[str, list[BenchmarkBriefEvidence]] = {}
        for item in self._evidence.values():
            by_brief.setdefault(item.brief_id, []).append(item)

        effective: list[BenchmarkBriefEvidence] = []
        ambiguous: list[str] = []
        for brief_id, items in sorted(by_brief.items()):
            if len(items) > 1:
                ambiguous.append(brief_id)
                continue
            effective.append(items[0])

        passed = [item for item in effective if item.status is BriefStatus.PASS]
        failed = [item for item in effective if item.status is BriefStatus.FAIL]
        blocked = [item for item in effective if item.status is BriefStatus.BLOCKED]
        style_counts = Counter(item.style_family for item in passed)
        styles = tuple(sorted(style_counts))
        style_pass_counts = tuple(sorted(style_counts.items()))
        total = len(effective) + len(ambiguous)
        apsr = min(len(passed) / required_briefs, 1.0)
        qualifying_styles = sum(1 for count in style_counts.values() if count >= min_passes_per_style)
        gsr = min(qualifying_styles / required_styles, 1.0)
        scores = [float(item.quality_score) for item in passed if item.quality_score is not None]
        mean_quality = sum(scores) / len(scores) if scores else None
        minimum_quality = min(scores) if scores else None
        blockers: list[str] = []
        if ambiguous:
            blockers.append(f"ambiguous_brief_revisions:{','.join(ambiguous)}")
        if len(passed) < required_briefs:
            blockers.append(f"passed_briefs:{len(passed)}/{required_briefs}")
        if len(styles) < required_styles:
            blockers.append(f"style_families:{len(styles)}/{required_styles}")
        undercovered = sorted(style for style, count in style_counts.items() if count < min_passes_per_style)
        if undercovered or qualifying_styles < required_styles:
            blockers.append(f"style_balance:{qualifying_styles}/{required_styles}@{min_passes_per_style}")
        if failed:
            blockers.append(f"failed_briefs:{len(failed)}")
        if blocked:
            blockers.append(f"blocked_briefs:{len(blocked)}")
        if mean_quality is None or mean_quality < float(release_quality):
            blockers.append(f"mean_quality:{mean_quality if mean_quality is not None else 'NONE'}/{release_quality}")
        if minimum_quality is None or minimum_quality < float(release_quality):
            blockers.append(f"minimum_quality:{minimum_quality if minimum_quality is not None else 'NONE'}/{release_quality}")
        authoritative = not blockers and len(passed) >= required_briefs
        evidence_hash = _hash({
            "evidence": sorted(item.content_hash() for item in self._evidence.values()),
            "required_briefs": required_briefs,
            "required_styles": required_styles,
            "release_quality": float(release_quality),
            "min_passes_per_style": min_passes_per_style,
        })
        return BenchmarkMetrics(
            total_briefs=total,
            passed_briefs=len(passed),
            failed_briefs=len(failed),
            blocked_briefs=len(blocked),
            style_families_observed=styles,
            style_pass_counts=style_pass_counts,
            apsr=apsr,
            gsr=gsr,
            mean_quality=mean_quality,
            minimum_quality=minimum_quality,
            authoritative=authoritative,
            blockers=tuple(blockers),
            evidence_hash=evidence_hash,
        )


def _require_sha(value: str, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
        raise BenchmarkEvidenceError(f"{field_name} must be a 64-character SHA256 hex digest")


def _require_text_tuple(value: tuple[str, ...], field_name: str) -> None:
    if not isinstance(value, tuple):
        raise BenchmarkEvidenceError(f"{field_name} must be a tuple")
    for item in value:
        if not isinstance(item, str) or not item.strip() or len(item) > 240:
            raise BenchmarkEvidenceError(f"{field_name} entries must be bounded non-empty strings")


def _hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
