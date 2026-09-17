from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable

from src.primitives.registry import Primitive, build_registry


class PrimitiveQualificationError(ValueError):
    pass


QUALIFICATION_STATES = {"UNQUALIFIED", "CONTRACT_VERIFIED", "PHYSICALLY_VERIFIED", "QUARANTINED"}


def _require_nonempty_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PrimitiveQualificationError(f"{field} must be a non-empty string")
    return value.strip()


def _require_nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PrimitiveQualificationError(f"{field} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class LegacyAggregateClaim:
    source_ref: str
    registered_count: int
    verified_count: int
    quarantined_count: int

    def __post_init__(self) -> None:
        _require_nonempty_text(self.source_ref, "source_ref")
        registered = _require_nonnegative_int(self.registered_count, "registered_count")
        verified = _require_nonnegative_int(self.verified_count, "verified_count")
        quarantined = _require_nonnegative_int(self.quarantined_count, "quarantined_count")
        if verified + quarantined != registered:
            raise PrimitiveQualificationError("legacy verified + quarantined must equal registered count")


@dataclass(frozen=True)
class PrimitiveFixtureCase:
    primitive_id: str
    family: str
    renderer: str
    fixture_id: str


@dataclass(frozen=True)
class PrimitiveEvidence:
    evidence_id: str
    primitive_id: str
    renderer: str
    fixture_id: str
    test_run_id: str
    evidence_kind: str
    passed: bool
    fixture_sha256: str
    artifact_sha256: str | None = None
    frame_count: int | None = None
    fps: float | None = None
    visual_duration_ms: int | None = None
    assertions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in ("evidence_id", "primitive_id", "renderer", "fixture_id", "test_run_id"):
            _require_nonempty_text(getattr(self, field), field)
        if self.evidence_kind not in {"CONTRACT", "PHYSICAL_RENDER"}:
            raise PrimitiveQualificationError("unsupported evidence_kind")
        if type(self.passed) is not bool:
            raise PrimitiveQualificationError("passed must be a JSON boolean")
        _require_sha(self.fixture_sha256, "fixture_sha256")
        if not isinstance(self.assertions, tuple) or not self.assertions:
            raise PrimitiveQualificationError("evidence requires a non-empty tuple of explicit assertions/findings")
        for assertion in self.assertions:
            _require_nonempty_text(assertion, "assertion")

        supplied_timing = any(value is not None for value in (self.frame_count, self.fps, self.visual_duration_ms))
        if self.evidence_kind == "CONTRACT":
            if self.artifact_sha256 is not None or supplied_timing:
                raise PrimitiveQualificationError("CONTRACT evidence cannot carry physical artifact/timing authority")
            return

        if self.passed and not self.artifact_sha256:
            raise PrimitiveQualificationError("passing physical render evidence requires artifact_sha256")
        if self.passed and not supplied_timing:
            raise PrimitiveQualificationError("passing physical render evidence requires timing evidence")
        if self.artifact_sha256 is not None:
            _require_sha(self.artifact_sha256, "artifact_sha256")
        if supplied_timing:
            if isinstance(self.frame_count, bool) or not isinstance(self.frame_count, int) or self.frame_count <= 0:
                raise PrimitiveQualificationError("physical timing evidence requires positive integer frame_count")
            if isinstance(self.fps, bool) or not isinstance(self.fps, (int, float)) or not math.isfinite(float(self.fps)) or float(self.fps) <= 0:
                raise PrimitiveQualificationError("physical timing evidence requires finite positive fps")
            if isinstance(self.visual_duration_ms, bool) or not isinstance(self.visual_duration_ms, int) or self.visual_duration_ms <= 0:
                raise PrimitiveQualificationError("physical timing evidence requires positive integer visual_duration_ms")
            expected_ms = self.frame_count / float(self.fps) * 1000.0
            tolerance_ms = max(1000.0 / float(self.fps), 1.0)
            if abs(expected_ms - self.visual_duration_ms) > tolerance_ms:
                raise PrimitiveQualificationError("visual duration must agree with frame_count/fps authority")

    def content_hash(self) -> str:
        payload = {
            "evidence_id": self.evidence_id,
            "primitive_id": self.primitive_id,
            "renderer": self.renderer,
            "fixture_id": self.fixture_id,
            "test_run_id": self.test_run_id,
            "evidence_kind": self.evidence_kind,
            "passed": self.passed,
            "fixture_sha256": self.fixture_sha256,
            "artifact_sha256": self.artifact_sha256,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "visual_duration_ms": self.visual_duration_ms,
            "assertions": list(self.assertions),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _require_sha(value: object, field: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value != value.lower()
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise PrimitiveQualificationError(f"{field} must be a 64-character lowercase hex digest")


def build_fixture_matrix(registry: Iterable[Primitive] | None = None) -> tuple[PrimitiveFixtureCase, ...]:
    primitives = tuple(registry or build_registry())
    cases = [
        PrimitiveFixtureCase(
            primitive_id=primitive.id,
            family=primitive.family,
            renderer=renderer,
            fixture_id=f"primitive:{primitive.id}:renderer:{renderer}:v1",
        )
        for primitive in primitives
        for renderer in sorted(set(primitive.renderer_support))
    ]
    cases.sort(key=lambda case: (case.primitive_id, case.renderer))
    identities = [(case.primitive_id, case.renderer) for case in cases]
    if len(identities) != len(set(identities)):
        raise PrimitiveQualificationError("fixture matrix contains duplicate primitive/renderer cases")
    return tuple(cases)


class PrimitiveQualificationLedger:
    def __init__(self, registry: Iterable[Primitive] | None = None, evidence: Iterable[PrimitiveEvidence] = ()) -> None:
        self.registry = tuple(registry or build_registry())
        self._by_id = {primitive.id: primitive for primitive in self.registry}
        if len(self._by_id) != len(self.registry):
            raise PrimitiveQualificationError("primitive registry IDs must be unique")
        self.matrix = build_fixture_matrix(self.registry)
        self._evidence: dict[str, PrimitiveEvidence] = {}
        for item in evidence:
            self.add(item)

    def add(self, item: PrimitiveEvidence) -> None:
        if not isinstance(item, PrimitiveEvidence):
            raise PrimitiveQualificationError("ledger accepts only validated PrimitiveEvidence")
        primitive = self._by_id.get(item.primitive_id)
        if primitive is None:
            raise PrimitiveQualificationError(f"unknown primitive_id: {item.primitive_id}")
        if item.renderer not in primitive.renderer_support:
            raise PrimitiveQualificationError(f"renderer {item.renderer} is not declared for {item.primitive_id}")
        expected_fixture = f"primitive:{item.primitive_id}:renderer:{item.renderer}:v1"
        if item.fixture_id != expected_fixture:
            raise PrimitiveQualificationError("evidence fixture_id does not match canonical primitive/renderer fixture")
        existing = self._evidence.get(item.evidence_id)
        if existing is not None:
            if existing.content_hash() != item.content_hash():
                raise PrimitiveQualificationError("evidence_id reused with conflicting payload")
            return
        self._evidence[item.evidence_id] = item

    @property
    def evidence(self) -> tuple[PrimitiveEvidence, ...]:
        return tuple(sorted(self._evidence.values(), key=lambda item: item.evidence_id))

    def renderer_state(self, primitive_id: str, renderer: str) -> str:
        primitive = self._by_id.get(primitive_id)
        if primitive is None or renderer not in primitive.renderer_support:
            raise PrimitiveQualificationError("unknown primitive/renderer pair")
        items = [e for e in self._evidence.values() if e.primitive_id == primitive_id and e.renderer == renderer]
        if any(e.passed is False for e in items):
            return "QUARANTINED"
        if any(e.evidence_kind == "PHYSICAL_RENDER" and e.passed is True for e in items):
            return "PHYSICALLY_VERIFIED"
        if any(e.evidence_kind == "CONTRACT" and e.passed is True for e in items):
            return "CONTRACT_VERIFIED"
        return "UNQUALIFIED"

    def primitive_state(self, primitive_id: str) -> str:
        primitive = self._by_id.get(primitive_id)
        if primitive is None:
            raise PrimitiveQualificationError(f"unknown primitive_id: {primitive_id}")
        states = [self.renderer_state(primitive_id, renderer) for renderer in primitive.renderer_support]
        if states and all(state == "PHYSICALLY_VERIFIED" for state in states):
            return "PHYSICALLY_VERIFIED"
        if any(state == "QUARANTINED" for state in states):
            return "QUARANTINED"
        if any(state in {"CONTRACT_VERIFIED", "PHYSICALLY_VERIFIED"} for state in states):
            return "CONTRACT_VERIFIED"
        return "UNQUALIFIED"

    def report(self, legacy_claim: LegacyAggregateClaim | None = None) -> dict:
        states = {primitive.id: self.primitive_state(primitive.id) for primitive in self.registry}
        counts = {state: sum(value == state for value in states.values()) for state in sorted(QUALIFICATION_STATES)}
        renderer_cases = {
            "total": len(self.matrix),
            "physical_verified": sum(self.renderer_state(c.primitive_id, c.renderer) == "PHYSICALLY_VERIFIED" for c in self.matrix),
            "contract_verified": sum(self.renderer_state(c.primitive_id, c.renderer) == "CONTRACT_VERIFIED" for c in self.matrix),
            "quarantined": sum(self.renderer_state(c.primitive_id, c.renderer) == "QUARANTINED" for c in self.matrix),
        }
        renderer_cases["unqualified"] = renderer_cases["total"] - sum(renderer_cases[key] for key in ("physical_verified", "contract_verified", "quarantined"))
        report = {
            "registered_primitives": len(self.registry),
            "primitive_states": states,
            "primitive_counts": counts,
            "renderer_cases": renderer_cases,
            "evidence_count": len(self._evidence),
            "empirical_authority": counts["PHYSICALLY_VERIFIED"],
        }
        if legacy_claim:
            if legacy_claim.registered_count != len(self.registry):
                raise PrimitiveQualificationError("legacy aggregate registered_count disagrees with live registry")
            report["legacy_aggregate"] = {
                "source_ref": legacy_claim.source_ref,
                "verified_count": legacy_claim.verified_count,
                "quarantined_count": legacy_claim.quarantined_count,
                "mapped_to_primitive_ids": False,
                "authority_effect": "NONE",
            }
        return report
