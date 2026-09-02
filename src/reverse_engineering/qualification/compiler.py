from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

from .model import (
    ClaimStatus,
    FidelityDimension,
    QualificationClaim,
    QualificationError,
    SceneEvidence,
    require_all_dimensions,
    validate_evidence_revision,
    validate_proxy_semantics,
)

SCHEMA_VERSION = "motion-os.golden-9d-qualification-manifest/v1"

# Each dimension must contain at least one claim whose semantic kind is strong
# enough to represent the dimension rather than a weaker rendering proxy. This
# prevents a manifest editor from replacing exact typography with layout boxes,
# or full audio fidelity with onset timing, and then declaring 9D success.
_MINIMUM_STRONG_CLAIM_KINDS: dict[FidelityDimension, frozenset[str]] = {
    FidelityDimension.TEMPORAL: frozenset(
        {"source_bound_layout_timing", "source_bound_visible_timing", "source_bound_state_timing"}
    ),
    FidelityDimension.MOTION: frozenset({"kinematic_curve", "original_easing_curve"}),
    FidelityDimension.CAMERA: frozenset({"camera_causality", "camera_or_source_ui_causality"}),
    FidelityDimension.TYPOGRAPHY: frozenset({"glyph_morphology"}),
    FidelityDimension.DEPTH: frozenset({"depth_topology", "original_z_order"}),
    FidelityDimension.COLOR: frozenset({"pre_grade_color", "color_grade", "material_color"}),
    FidelityDimension.FX: frozenset({"effect_stack"}),
    FidelityDimension.AUDIO: frozenset({"stem_identity"}),
    FidelityDimension.RETENTION: frozenset({"retention_grammar"}),
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
        if ref.scene_id == "PROGRAM":
            continue
        validate_evidence_revision(ref, scene_heads[ref.scene_id], evidence)

    claim_list = [QualificationClaim.from_mapping(item) for item in manifest.get("claims", [])]
    claims: dict[str, QualificationClaim] = {}
    for claim in claim_list:
        if claim.claim_id in claims:
            raise QualificationError(f"duplicate claim {claim.claim_id}")
        if claim.scene_id not in scene_heads and claim.scene_id != "PROGRAM":
            raise QualificationError(
                f"claim {claim.claim_id} references unknown scene {claim.scene_id}"
            )
        claim.validate(evidence)
        validate_proxy_semantics(claim)
        claims[claim.claim_id] = claim

    requirements = manifest.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise QualificationError("manifest requires 9D requirements")

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
                f"dimension {dimension.value} requires at least one explicit claim"
            )
        dimension_claims: list[QualificationClaim] = []
        for claim_id in ids:
            claim = claims.get(claim_id)
            if claim is None:
                raise QualificationError(
                    f"dimension {dimension.value} references missing claim {claim_id}"
                )
            if claim.dimension is not dimension:
                raise QualificationError(
                    f"claim {claim_id} belongs to {claim.dimension.value}, not {dimension.value}"
                )
            if not claim.required:
                raise QualificationError(
                    f"program requirement cannot depend on non-required claim {claim_id}"
                )
            dimension_claims.append(claim)
            requirement_claims.add(claim_id)

        required_kinds = _MINIMUM_STRONG_CLAIM_KINDS[dimension]
        present_kinds = {claim.claim_kind for claim in dimension_claims}
        if not (present_kinds & required_kinds):
            raise QualificationError(
                f"dimension {dimension.value} can be semantically laundered: expected at least one strong claim kind from {sorted(required_kinds)}, got {sorted(present_kinds)}"
            )

    require_all_dimensions(seen_dimensions)

    # A required claim must be visible from a 9D requirement. Orphaned required
    # claims are dangerous because they appear important but cannot veto promotion.
    orphaned = sorted(
        claim.claim_id
        for claim in claims.values()
        if claim.required and claim.claim_id not in requirement_claims
    )
    if orphaned:
        raise QualificationError(
            "required claims missing from promotion requirements: " + ", ".join(orphaned)
        )

    return {
        "scene_heads": scene_heads,
        "evidence": evidence,
        "claims": claims,
        "requirements": requirements,
    }


def compile_qualification_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    validated = validate_qualification_manifest(manifest)
    claims: Mapping[str, QualificationClaim] = validated["claims"]

    dimensions: dict[str, dict[str, Any]] = {}
    defects: list[dict[str, Any]] = []
    qualified_required_claims = 0
    total_required_claims = 0

    for requirement in validated["requirements"]:
        dimension = FidelityDimension(str(requirement["dimension"]))
        claim_ids = [str(value) for value in requirement["claim_ids"]]
        required_claims = [claims[claim_id] for claim_id in claim_ids]
        total_required_claims += len(required_claims)
        qualified = [
            claim for claim in required_claims if claim.status is ClaimStatus.QUALIFIED
        ]
        qualified_required_claims += len(qualified)
        blockers = [
            _defect_from_claim(claim)
            for claim in required_claims
            if claim.status is not ClaimStatus.QUALIFIED
        ]
        defects.extend(blockers)
        dimensions[dimension.value] = {
            "required_claim_ids": claim_ids,
            "qualified_claim_ids": [claim.claim_id for claim in qualified],
            "unqualified_claim_ids": [item["claim_id"] for item in blockers],
            "qualified": not blockers,
            "authority_rule": "ALL_REQUIRED_CLAIMS_QUALIFIED_NO_AVERAGING",
            "minimum_strong_claim_kinds": sorted(_MINIMUM_STRONG_CLAIM_KINDS[dimension]),
        }

    full_9d = all(item["qualified"] for item in dimensions.values())
    diagnostic_ratio = (
        qualified_required_claims / total_required_claims if total_required_claims else 0.0
    )

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

    return {
        "schema_version": "motion-os.golden-9d-qualification-result/v1",
        "program_id": str(manifest.get("program_id", "golden-scenes-9d")),
        "source_manifest_schema": SCHEMA_VERSION,
        "scene_heads": validated["scene_heads"],
        "dimensions": dimensions,
        "scene_summary": dict(scene_summary),
        "defect_frontier": defects,
        "defects_by_severity": dict(sorted(by_severity.items())),
        "diagnostic_coverage_ratio": diagnostic_ratio,
        "diagnostic_coverage_ratio_is_promotion_authority": False,
        "full_9d_fidelity_validated": full_9d,
        "canonical_template": False,
        "promotion_state": (
            "FULL_9D_FIDELITY_VALIDATED" if full_9d else "CROSS_SCENE_PARTIAL_QUALIFICATION"
        ),
        "promotion_rule": "Every required claim in every one of the nine dimensions must independently qualify. Aggregate similarity or mean scores cannot compensate for a failed/unknown dimension.",
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
        "reason": claim.blocked_reason or "required claim is not qualified",
        "authority": claim.authority.value,
        "evidence_ids": list(claim.evidence_ids),
        "repair_scope": "CANONICAL_GRAPH_OR_MEASUREMENT_FIRST_NOT_RENDERER_LOCAL",
    }
