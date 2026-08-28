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


@dataclass(frozen=True)
class LegacyAggregateClaim:
    source_ref: str
    registered_count: int
    verified_count: int
    quarantined_count: int

    def __post_init__(self) -> None:
        if min(self.registered_count, self.verified_count, self.quarantined_count) < 0:
            raise PrimitiveQualificationError("legacy aggregate counts must be non-negative")
        if self.verified_count + self.quarantined_count != self.registered_count:
            raise PrimitiveQualificationError("legacy verified + quarantined must equal registered count")
        if not self.source_ref:
            raise PrimitiveQualificationError("legacy aggregate requires source_ref")


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
        if not self.evidence_id or not self.primitive_id or not self.renderer or not self.fixture_id or not self.test_run_id:
            raise PrimitiveQualificationError("evidence identity fields must be non-empty")
        if self.evidence_kind not in {"CONTRACT", "PHYSICAL_RENDER"}:
            raise PrimitiveQualificationError("unsupported evidence_kind")
        _require_sha(self.fixture_sha256, "fixture_sha256")
        if self.evidence_kind == "PHYSICAL_RENDER":
            if not self.artifact_sha256:
                raise PrimitiveQualificationError("physical render evidence requires artifact_sha256")
            _require_sha(self.artifact_sha256, "artifact_sha256")
            if self.frame_count is None or self.frame_count <= 0 or self.fps is None or not math.isfinite(self.fps) or self.fps <= 0:
                raise PrimitiveQualificationError("physical render evidence requires positive frame_count/fps")
            if self.visual_duration_ms is None or self.visual_duration_ms <= 0:
                raise PrimitiveQualificationError("physical render evidence requires visual_duration_ms")
            expected_ms = self.frame_count / self.fps * 1000.0
            tolerance_ms = max(1000.0 / self.fps, 1.0)
            if abs(expected_ms - self.visual_duration_ms) > tolerance_ms:
                raise PrimitiveQualificationError("visual duration must agree with frame_count/fps authority")
        if self.passed and not self.assertions:
            raise PrimitiveQualificationError("passing evidence requires explicit assertions")

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


def _require_sha(value: str, field: str) -> None:
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
        raise PrimitiveQualificationError(f"{field} must be a 64-character hex digest")


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
        if any(e.evidence_kind == "PHYSICAL_RENDER" and e.passed for e in items):
            return "PHYSICALLY_VERIFIED"
        if any(e.evidence_kind == "CONTRACT" and e.passed for e in items):
            return "CONTRACT_VERIFIED"
        if any(not e.passed for e in items):
            return "QUARANTINED"
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
