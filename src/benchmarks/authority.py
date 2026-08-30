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
class BenchmarkCaseSpec:
    brief_id: str
    style_family: str
    brief_sha256: str

    def __post_init__(self) -> None:
        for name, value in (("brief_id", self.brief_id), ("style_family", self.style_family)):
            if not isinstance(value, str) or not value.strip() or len(value) > 160:
                raise BenchmarkEvidenceError(f"{name} must be bounded non-empty text")
        _require_sha(self.brief_sha256, "brief_sha256")

    def content_hash(self) -> str:
        return _hash({"brief_id": self.brief_id, "style_family": self.style_family, "brief_sha256": self.brief_sha256})


@dataclass(frozen=True)
class BenchmarkSuiteManifest:
    suite_id: str
    cases: tuple[BenchmarkCaseSpec, ...]
    release_quality: float = 9.0

    def __post_init__(self) -> None:
        if not isinstance(self.suite_id, str) or not self.suite_id.strip() or len(self.suite_id) > 160:
            raise BenchmarkEvidenceError("suite_id must be bounded non-empty text")
        if not isinstance(self.cases, tuple) or not self.cases:
            raise BenchmarkEvidenceError("suite cases must be a non-empty tuple")
        if any(not isinstance(case, BenchmarkCaseSpec) for case in self.cases):
            raise BenchmarkEvidenceError("suite cases must be BenchmarkCaseSpec")
        ids = [case.brief_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise BenchmarkEvidenceError("suite brief IDs must be unique")
        if not isinstance(self.release_quality, (int, float)) or isinstance(self.release_quality, bool) or not math.isfinite(float(self.release_quality)) or not 0 <= float(self.release_quality) <= 10:
            raise BenchmarkEvidenceError("release_quality must be finite and in [0,10]")

    @property
    def required_style_counts(self) -> Counter[str]:
        return Counter(case.style_family for case in self.cases)

    def content_hash(self) -> str:
        return _hash({
            "suite_id": self.suite_id,
            "release_quality": float(self.release_quality),
            "cases": [
                {"brief_id": case.brief_id, "style_family": case.style_family, "brief_sha256": case.brief_sha256}
                for case in sorted(self.cases, key=lambda item: item.brief_id)
            ],
        })


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
    suite_id: str | None
    suite_hash: str | None
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
        suite: BenchmarkSuiteManifest | None = None,
        required_briefs: int = 25,
        required_styles: int = 5,
        release_quality: float = 9.0,
        min_passes_per_style: int | None = None,
    ) -> BenchmarkMetrics:
        """Compute benchmark metrics.

        Without an exact suite manifest this function is observational only: APSR/GSR can be
        inspected, but `authoritative` is always False. Product authority requires binding the
        evidence to an explicit suite of brief IDs, style mapping and brief hashes.
        """
        if suite is not None and not isinstance(suite, BenchmarkSuiteManifest):
            raise BenchmarkEvidenceError("suite must be BenchmarkSuiteManifest")

        if suite is not None:
            required_briefs = len(suite.cases)
            required_styles = len(suite.required_style_counts)
            release_quality = float(suite.release_quality)
            expected_cases = {case.brief_id: case for case in suite.cases}
            expected_style_counts = suite.required_style_counts
        else:
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
            expected_cases = None
            expected_style_counts = None

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

        blockers: list[str] = []
        if suite is None:
            blockers.append("benchmark_suite_unbound")

        if expected_cases is not None:
            expected_ids = set(expected_cases)
            observed_ids = {item.brief_id for item in effective} | set(ambiguous)
            missing_ids = sorted(expected_ids - observed_ids)
            unexpected_ids = sorted(observed_ids - expected_ids)
            if missing_ids:
                blockers.append(f"missing_briefs:{','.join(missing_ids)}")
            if unexpected_ids:
                blockers.append(f"unexpected_briefs:{','.join(unexpected_ids)}")
            filtered: list[BenchmarkBriefEvidence] = []
            for item in effective:
                spec = expected_cases.get(item.brief_id)
                if spec is None:
                    continue
                if item.style_family != spec.style_family or item.brief_sha256 != spec.brief_sha256:
                    blockers.append(f"suite_binding_mismatch:{item.brief_id}")
                    continue
                filtered.append(item)
            effective = filtered
            ambiguous = [brief_id for brief_id in ambiguous if brief_id in expected_ids]

        passed = [item for item in effective if item.status is BriefStatus.PASS]
        failed = [item for item in effective if item.status is BriefStatus.FAIL]
        blocked = [item for item in effective if item.status is BriefStatus.BLOCKED]
        style_counts = Counter(item.style_family for item in passed)
        styles = tuple(sorted(style_counts))
        style_pass_counts = tuple(sorted(style_counts.items()))
        total = len(effective) + len(ambiguous)
        apsr = min(len(passed) / required_briefs, 1.0)

        if expected_style_counts is not None:
            qualifying_styles = sum(
                1 for style, required_count in expected_style_counts.items()
                if style_counts.get(style, 0) >= required_count
            )
            gsr = qualifying_styles / required_styles
            if qualifying_styles < required_styles:
                blockers.append(f"style_balance:{qualifying_styles}/{required_styles}@suite")
        else:
            assert min_passes_per_style is not None
            qualifying_styles = sum(1 for count in style_counts.values() if count >= min_passes_per_style)
            gsr = min(qualifying_styles / required_styles, 1.0)
            if len(styles) < required_styles:
                blockers.append(f"style_families:{len(styles)}/{required_styles}")
            if qualifying_styles < required_styles:
                blockers.append(f"style_balance:{qualifying_styles}/{required_styles}@{min_passes_per_style}")

        scores = [float(item.quality_score) for item in passed if item.quality_score is not None]
        mean_quality = sum(scores) / len(scores) if scores else None
        minimum_quality = min(scores) if scores else None
        if ambiguous:
            blockers.append(f"ambiguous_brief_revisions:{','.join(sorted(ambiguous))}")
        if len(passed) < required_briefs:
            blockers.append(f"passed_briefs:{len(passed)}/{required_briefs}")
        if failed:
            blockers.append(f"failed_briefs:{len(failed)}")
        if blocked:
            blockers.append(f"blocked_briefs:{len(blocked)}")
        if mean_quality is None or mean_quality < float(release_quality):
            blockers.append(f"mean_quality:{mean_quality if mean_quality is not None else 'NONE'}/{release_quality}")
        if minimum_quality is None or minimum_quality < float(release_quality):
            blockers.append(f"minimum_quality:{minimum_quality if minimum_quality is not None else 'NONE'}/{release_quality}")

        authoritative = bool(suite is not None and not blockers and len(passed) == required_briefs)
        evidence_hash = _hash({
            "evidence": sorted(item.content_hash() for item in self._evidence.values()),
            "suite_hash": suite.content_hash() if suite is not None else None,
            "required_briefs": required_briefs,
            "required_styles": required_styles,
            "release_quality": float(release_quality),
            "min_passes_per_style": min_passes_per_style,
        })
        return BenchmarkMetrics(
            suite_id=suite.suite_id if suite is not None else None,
            suite_hash=suite.content_hash() if suite is not None else None,
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
            blockers=tuple(dict.fromkeys(blockers)),
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
