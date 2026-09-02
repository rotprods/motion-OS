from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


class QualificationError(ValueError):
    """Raised when a qualification/provenance claim would overstate authority."""


class FidelityDimension(str, Enum):
    TEMPORAL = "temporal"
    MOTION = "motion"
    CAMERA = "camera"
    TYPOGRAPHY = "typography"
    DEPTH = "depth"
    COLOR = "color"
    FX = "fx"
    AUDIO = "audio"
    RETENTION = "retention"


class ClaimStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    NOT_MEASURED = "NOT_MEASURED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EvidenceAuthority(str, Enum):
    PHYSICALLY_MEASURED = "PHYSICALLY_MEASURED"
    DETERMINISTIC_HEURISTIC = "DETERMINISTIC_HEURISTIC"
    EVIDENCE_BOUND_INFERENCE = "EVIDENCE_BOUND_INFERENCE"
    EXPLICIT_ASSUMPTION = "EXPLICIT_ASSUMPTION"
    UNKNOWN = "UNKNOWN"


_AUTHORITY_RANK = {
    EvidenceAuthority.UNKNOWN: 0,
    EvidenceAuthority.EXPLICIT_ASSUMPTION: 1,
    EvidenceAuthority.EVIDENCE_BOUND_INFERENCE: 2,
    EvidenceAuthority.DETERMINISTIC_HEURISTIC: 3,
    EvidenceAuthority.PHYSICALLY_MEASURED: 4,
}


@dataclass(frozen=True)
class SceneEvidence:
    evidence_id: str
    scene_id: str
    kind: str
    authority: EvidenceAuthority
    revision: str | None = None
    uri: str | None = None
    digest: str | None = None
    equivalence_proof_id: str | None = None
    notes: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SceneEvidence":
        return cls(
            evidence_id=str(data["evidence_id"]),
            scene_id=str(data["scene_id"]),
            kind=str(data["kind"]),
            authority=EvidenceAuthority(str(data["authority"])),
            revision=_optional_str(data.get("revision")),
            uri=_optional_str(data.get("uri")),
            digest=_optional_str(data.get("digest")),
            equivalence_proof_id=_optional_str(data.get("equivalence_proof_id")),
            notes=_optional_str(data.get("notes")),
        )


@dataclass(frozen=True)
class QualificationClaim:
    """Observable-output claim that may participate in OUTPUT_FIDELITY_9D promotion."""

    claim_id: str
    scene_id: str
    dimension: FidelityDimension
    semantic_target: str
    claim_kind: str
    required: bool
    status: ClaimStatus
    authority: EvidenceAuthority
    evidence_ids: tuple[str, ...]
    scope: str
    severity_if_unqualified: str
    blocked_reason: str | None = None
    proxy_for: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "QualificationClaim":
        return cls(
            claim_id=str(data["claim_id"]),
            scene_id=str(data["scene_id"]),
            dimension=FidelityDimension(str(data["dimension"])),
            semantic_target=str(data["semantic_target"]),
            claim_kind=str(data["claim_kind"]),
            required=bool(data.get("required", True)),
            status=ClaimStatus(str(data["status"])),
            authority=EvidenceAuthority(str(data["authority"])),
            evidence_ids=tuple(str(value) for value in data.get("evidence_ids", ())),
            scope=str(data.get("scope", "")),
            severity_if_unqualified=str(data.get("severity_if_unqualified", "P1")),
            blocked_reason=_optional_str(data.get("blocked_reason")),
            proxy_for=_optional_str(data.get("proxy_for")),
        )

    def validate(self, evidence: Mapping[str, SceneEvidence]) -> None:
        _validate_common_claim(
            claim_id=self.claim_id,
            scene_id=self.scene_id,
            status=self.status,
            authority=self.authority,
            evidence_ids=self.evidence_ids,
            blocked_reason=self.blocked_reason,
            evidence=evidence,
        )
        if self.required and self.status is ClaimStatus.NOT_APPLICABLE:
            raise QualificationError(
                f"required claim {self.claim_id} cannot be NOT_APPLICABLE"
            )


@dataclass(frozen=True)
class AuthoringProvenanceClaim:
    """Question about hidden source-authoring identity.

    These claims are durable/queryable but explicitly outside the output-fidelity
    promotion DAG. They may remain UNKNOWN forever without preventing an
    output-equivalent reconstruction.
    """

    claim_id: str
    scene_id: str
    target: str
    provenance_kind: str
    status: ClaimStatus
    authority: EvidenceAuthority
    evidence_ids: tuple[str, ...]
    notes: str
    blocked_reason: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "AuthoringProvenanceClaim":
        return cls(
            claim_id=str(data["claim_id"]),
            scene_id=str(data["scene_id"]),
            target=str(data["target"]),
            provenance_kind=str(data["provenance_kind"]),
            status=ClaimStatus(str(data["status"])),
            authority=EvidenceAuthority(str(data["authority"])),
            evidence_ids=tuple(str(value) for value in data.get("evidence_ids", ())),
            notes=str(data.get("notes", "")),
            blocked_reason=_optional_str(data.get("blocked_reason")),
        )

    def validate(self, evidence: Mapping[str, SceneEvidence]) -> None:
        _validate_common_claim(
            claim_id=self.claim_id,
            scene_id=self.scene_id,
            status=self.status,
            authority=self.authority,
            evidence_ids=self.evidence_ids,
            blocked_reason=self.blocked_reason,
            evidence=evidence,
        )


def _validate_common_claim(
    *,
    claim_id: str,
    scene_id: str,
    status: ClaimStatus,
    authority: EvidenceAuthority,
    evidence_ids: tuple[str, ...],
    blocked_reason: str | None,
    evidence: Mapping[str, SceneEvidence],
) -> None:
    if not claim_id:
        raise QualificationError("claim_id must not be empty")
    if status is ClaimStatus.QUALIFIED:
        if authority is not EvidenceAuthority.PHYSICALLY_MEASURED:
            raise QualificationError(
                f"qualified claim {claim_id} requires PHYSICALLY_MEASURED authority"
            )
        if not evidence_ids:
            raise QualificationError(
                f"qualified claim {claim_id} requires durable evidence"
            )
    if status is ClaimStatus.BLOCKED and not blocked_reason:
        raise QualificationError(f"blocked claim {claim_id} requires blocked_reason")
    for evidence_id in evidence_ids:
        if evidence_id not in evidence:
            raise QualificationError(
                f"claim {claim_id} references unknown evidence {evidence_id}"
            )
        ref = evidence[evidence_id]
        # Scene claims may consume evidence from themselves plus PROGRAM-wide
        # evidence. PROGRAM claims are aggregators and may intentionally consume
        # evidence from any registered scene; otherwise cross-scene qualification
        # would require laundering scene evidence into fake PROGRAM duplicates.
        if scene_id != "PROGRAM" and ref.scene_id not in {scene_id, "PROGRAM"}:
            raise QualificationError(
                f"claim {claim_id} cannot consume evidence for {ref.scene_id}"
            )
        if status is ClaimStatus.QUALIFIED and _AUTHORITY_RANK[ref.authority] < _AUTHORITY_RANK[EvidenceAuthority.DETERMINISTIC_HEURISTIC]:
            raise QualificationError(
                f"qualified claim {claim_id} depends on low-authority evidence {evidence_id}"
            )


def validate_evidence_revision(
    evidence: SceneEvidence,
    scene_head: str,
    known_evidence: Mapping[str, SceneEvidence],
) -> None:
    """Reject stale-head evidence unless an explicit physical output-equivalence proof bridges revisions."""

    if evidence.revision is None or evidence.revision == scene_head:
        return
    proof_id = evidence.equivalence_proof_id
    if not proof_id:
        raise QualificationError(
            f"evidence {evidence.evidence_id} revision {evidence.revision} != scene head {scene_head} without equivalence proof"
        )
    proof = known_evidence.get(proof_id)
    if proof is None:
        raise QualificationError(
            f"evidence {evidence.evidence_id} references missing equivalence proof {proof_id}"
        )
    if proof.kind != "output_equivalence_proof":
        raise QualificationError(
            f"equivalence evidence {proof_id} must have kind output_equivalence_proof"
        )
    if proof.authority is not EvidenceAuthority.PHYSICALLY_MEASURED:
        raise QualificationError(
            f"equivalence proof {proof_id} must be physically measured"
        )


def validate_proxy_semantics(claim: QualificationClaim) -> None:
    """Prevent a weaker proxy from silently satisfying a stronger visible-output target."""

    strong_markers = (
        "glyph_morphology",
        "source_pixels",
        "rendered_effect_signature",
        "audio_output_signature",
        "rendered_color_field",
    )
    if claim.proxy_for and any(marker in claim.semantic_target for marker in strong_markers):
        if claim.status is ClaimStatus.QUALIFIED:
            raise QualificationError(
                f"proxy claim {claim.claim_id} cannot qualify stronger target {claim.semantic_target}"
            )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def require_all_dimensions(dimensions: Sequence[FidelityDimension]) -> None:
    missing = set(FidelityDimension) - set(dimensions)
    if missing:
        values = ", ".join(sorted(item.value for item in missing))
        raise QualificationError(f"9D program is missing dimensions: {values}")
