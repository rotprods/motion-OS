from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

from .model import (
    AuthoringProvenanceClaim,
    ClaimStatus,
    FidelityDimension,
    QualificationClaim,
    QualificationError,
    SceneEvidence,
    require_all_dimensions,
    validate_evidence_revision,
    validate_proxy_semantics,
)

SCHEMA_VERSION = "motion-os.golden-output-fidelity-manifest/v2"

# Minimum observable-output semantics per dimension. Hidden original authoring
# identity belongs in provenance_claims and is forbidden from satisfying or
# blocking these requirements.
_MINIMUM_STRONG_CLAIM_KINDS: dict[FidelityDimension, frozenset[str]] = {
    FidelityDimension.TEMPORAL: frozenset({"rendered_timing"}),
    FidelityDimension.MOTION: frozenset({"rendered_kinematics"}),
    FidelityDimension.CAMERA: frozenset({"rendered_camera_motion_field"}),
    FidelityDimension.TYPOGRAPHY: frozenset({"visible_glyph_morphology"}),
    FidelityDimension.DEPTH: frozenset({"visible_depth_topology"}),
    FidelityDimension.COLOR: frozenset({"rendered_color_field"}),
    FidelityDimension.FX: frozenset({"rendered_effect_signature"}),
    FidelityDimension.AUDIO: frozenset({"audio_event_grammar"}),
    FidelityDimension.RETENTION: frozenset({"observable_retention_grammar"}),
}


def validate_qualification_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise QualificationError(
            f"unsupported manifest schema: {manifest.get('schema_version')!r}"
        )

    scenes_raw = manifest.get("scenes")
    if not isinstance(scenes_raw, list) or not scenes_raw:
        raise QualificationError("manifest requires non-empty scenes")
    scene_heads: dict[str, str] = {}
    for item in scenes_raw:
        scene_id = str(item["scene_id"])
        head_sha = str(item["head_sha"])
        if scene_id in scene_heads:
            raise QualificationError(f"duplicate scene {scene_id}")
        if len(head_sha) != 40:
            raise QualificationError(f"scene {scene_id} head must be full 40-char SHA")
        scene_heads[scene_id] = head_sha

    evidence_list = [SceneEvidence.from_mapping(item) for item in manifest.get("evidence", [])]
    evidence: dict[str, SceneEvidence] = {}
    for ref in evidence_list:
        if ref.evidence_id in evidence:
            raise QualificationError(f"duplicate evidence {ref.evidence_id}")
        if ref.scene_id != "PROGRAM" and ref.scene_id not in scene_heads:
            raise QualificationError(
                f"evidence {ref.evidence_id} references unknown scene {ref.scene_id}"
            )
        evidence[ref.evidence_id] = ref

    for ref in evidence.values():
        if ref.scene_id != "PROGRAM":
            validate_evidence_revision(ref, scene_heads[ref.scene_id], evidence)

    output_claims_list = [QualificationClaim.from_mapping(item) for item in manifest.get("output_claims", [])]
    output_claims: dict[str, QualificationClaim] = {}
    for claim in output_claims_list:
        if claim.claim_id in output_claims:
            raise QualificationError(f"duplicate output claim {claim.claim_id}")
        if claim.scene_id not in scene_heads and claim.scene_id != "PROGRAM":
            raise QualificationError(
                f"output claim {claim.claim_id} references unknown scene {claim.scene_id}"
            )
        claim.validate(evidence)
        validate_proxy_semantics(claim)
        output_claims[claim.claim_id] = claim

    provenance_list = [AuthoringProvenanceClaim.from_mapping(item) for item in manifest.get("provenance_claims", [])]
    provenance_claims: dict[str, AuthoringProvenanceClaim] = {}
    for claim in provenance_list:
        if claim.claim_id in provenance_claims or claim.claim_id in output_claims:
            raise QualificationError(f"duplicate/colliding provenance claim {claim.claim_id}")
        if claim.scene_id not in scene_heads and claim.scene_id != "PROGRAM":
            raise QualificationError(
                f"provenance claim {claim.claim_id} references unknown scene {claim.scene_id}"
            )
        claim.validate(evidence)
        provenance_claims[claim.claim_id] = claim

    requirements = manifest.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise QualificationError("manifest requires OUTPUT_FIDELITY_9D requirements")

    seen_dimensions: list[FidelityDimension] = []
    requirement_claims: set[str] = set()
    for requirement in requirements:
        dimension = FidelityDimension(str(requirement["dimension"]))
        if dimension in seen_dimensions:
            raise QualificationError(f"duplicate requirement dimension {dimension.value}")
        seen_dimensions.append(dimension)
        ids = tuple(str(value) for value in requirement.get("claim_ids", ()))
        if not ids:
            raise QualificationError(
                f"dimension {dimension.value} requires at least one explicit output claim"
            )
        dimension_claims: list[QualificationClaim] = []
        for claim_id in ids:
            if claim_id in provenance_claims:
                raise QualificationError(
                    f"authoring provenance claim {claim_id} cannot enter OUTPUT_FIDELITY_9D promotion"
                )
            claim = output_claims.get(claim_id)
            if claim is None:
                raise QualificationError(
                    f"dimension {dimension.value} references missing output claim {claim_id}"
                )
            if claim.dimension is not dimension:
                raise QualificationError(
                    f"claim {claim_id} belongs to {claim.dimension.value}, not {dimension.value}"
                )
            if not claim.required:
                raise QualificationError(
                    f"output requirement cannot depend on non-required claim {claim_id}"
                )
            dimension_claims.append(claim)
            requirement_claims.add(claim_id)

        required_kinds = _MINIMUM_STRONG_CLAIM_KINDS[dimension]
        present_kinds = {claim.claim_kind for claim in dimension_claims}
        if not (present_kinds & required_kinds):
            raise QualificationError(
                f"dimension {dimension.value} can be semantically laundered: expected at least one observable-output claim kind from {sorted(required_kinds)}, got {sorted(present_kinds)}"
            )

    require_all_dimensions(seen_dimensions)

    orphaned = sorted(
        claim.claim_id
        for claim in output_claims.values()
        if claim.required and claim.claim_id not in requirement_claims
    )
    if orphaned:
        raise QualificationError(
            "required output claims missing from promotion requirements: " + ", ".join(orphaned)
        )

    return {
        "scene_heads": scene_heads,
        "evidence": evidence,
        "output_claims": output_claims,
        "provenance_claims": provenance_claims,
        "requirements": requirements,
    }


def compile_qualification_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    validated = validate_qualification_manifest(manifest)
    claims: Mapping[str, QualificationClaim] = validated["output_claims"]
    provenance: Mapping[str, AuthoringProvenanceClaim] = validated["provenance_claims"]

    dimensions: dict[str, dict[str, Any]] = {}
    defects: list[dict[str, Any]] = []
    qualified_required_claims = 0
    total_required_claims = 0

    for requirement in validated["requirements"]:
        dimension = FidelityDimension(str(requirement["dimension"]))
        claim_ids = [str(value) for value in requirement["claim_ids"]]
        required_claims = [claims[claim_id] for claim_id in claim_ids]
        total_required_claims += len(required_claims)
        qualified = [claim for claim in required_claims if claim.status is ClaimStatus.QUALIFIED]
        qualified_required_claims += len(qualified)
        blockers = [_defect_from_claim(claim) for claim in required_claims if claim.status is not ClaimStatus.QUALIFIED]
        defects.extend(blockers)
        dimensions[dimension.value] = {
            "required_claim_ids": claim_ids,
            "qualified_claim_ids": [claim.claim_id for claim in qualified],
            "unqualified_claim_ids": [item["claim_id"] for item in blockers],
            "qualified": not blockers,
            "authority_rule": "ALL_REQUIRED_OBSERVABLE_OUTPUT_CLAIMS_QUALIFIED_NO_AVERAGING",
            "minimum_strong_claim_kinds": sorted(_MINIMUM_STRONG_CLAIM_KINDS[dimension]),
        }

    output_9d = all(item["qualified"] for item in dimensions.values())
    diagnostic_ratio = qualified_required_claims / total_required_claims if total_required_claims else 0.0

    by_severity: dict[str, int] = defaultdict(int)
    for defect in defects:
        by_severity[defect["severity"]] += 1

    scene_summary: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: {"qualified": [], "partial": [], "blocked": [], "not_measured": []}
    )
    for claim in claims.values():
        bucket = {
            ClaimStatus.QUALIFIED: "qualified",
            ClaimStatus.PARTIAL: "partial",
            ClaimStatus.BLOCKED: "blocked",
            ClaimStatus.NOT_MEASURED: "not_measured",
            ClaimStatus.NOT_APPLICABLE: "not_measured",
        }[claim.status]
        scene_summary[claim.scene_id][bucket].append(claim.claim_id)

    provenance_summary: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: {"qualified": [], "partial": [], "blocked": [], "not_measured": []}
    )
    for claim in provenance.values():
        bucket = {
            ClaimStatus.QUALIFIED: "qualified",
            ClaimStatus.PARTIAL: "partial",
            ClaimStatus.BLOCKED: "blocked",
            ClaimStatus.NOT_MEASURED: "not_measured",
            ClaimStatus.NOT_APPLICABLE: "not_measured",
        }[claim.status]
        provenance_summary[claim.scene_id][bucket].append(claim.claim_id)

    return {
        "schema_version": "motion-os.golden-output-fidelity-result/v2",
        "program_id": str(manifest.get("program_id", "golden-scenes-output-fidelity")),
        "source_manifest_schema": SCHEMA_VERSION,
        "scene_heads": validated["scene_heads"],
        "output_dimensions": dimensions,
        "output_scene_summary": dict(scene_summary),
        "output_defect_frontier": defects,
        "defects_by_severity": dict(sorted(by_severity.items())),
        "diagnostic_output_claim_coverage_ratio": diagnostic_ratio,
        "diagnostic_coverage_ratio_is_promotion_authority": False,
        "output_fidelity_9d_validated": output_9d,
        "authoring_provenance_summary": dict(provenance_summary),
        "authoring_provenance_complete": bool(provenance) and all(c.status is ClaimStatus.QUALIFIED for c in provenance.values()),
        "authoring_provenance_is_output_fidelity_gate": False,
        "canonical_template": False,
        "promotion_state": "OUTPUT_FIDELITY_9D_VALIDATED" if output_9d else "OUTPUT_FIDELITY_PARTIAL",
        "promotion_rule": "Every required observable-output claim in all nine dimensions must independently qualify. Hidden original authoring identity is recorded separately and never substitutes for or vetoes output fidelity.",
    }


def _defect_from_claim(claim: QualificationClaim) -> dict[str, Any]:
    return {
        "defect_id": f"T08-{claim.claim_id}",
        "claim_id": claim.claim_id,
        "scene_id": claim.scene_id,
        "dimension": claim.dimension.value,
        "semantic_target": claim.semantic_target,
        "claim_kind": claim.claim_kind,
        "status": claim.status.value,
        "severity": claim.severity_if_unqualified,
        "reason": claim.blocked_reason or "required observable-output claim is not qualified",
        "authority": claim.authority.value,
        "evidence_ids": list(claim.evidence_ids),
        "repair_scope": "SOURCE_OR_MEASUREMENT_TO_CANONICAL_OUTPUT_GRAPH_FIRST_NOT_RENDERER_LOCAL",
    }
