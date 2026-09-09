from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
from typing import Any, Mapping

from src.graph.editing_graph import TypedEditingGraph
from src.studio.inspector import recovery_manifest


_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA64_RE = re.compile(r"^[0-9a-f]{64}$")


class ProductRunManifestError(ValueError):
    """Raised when technical product-run evidence is incomplete or contradictory."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProductRunManifestError(f"{field} must be an object")
    return value


def _require_nonempty_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProductRunManifestError(f"{field} must be non-empty text")
    return value.strip()


def _require_sha(value: object, field: str, *, length: int) -> str:
    text = _require_nonempty_text(value, field)
    pattern = _SHA40_RE if length == 40 else _SHA64_RE
    if not pattern.fullmatch(text):
        raise ProductRunManifestError(f"{field} must be {length}-hex")
    return text


def _verified_graph(bundle: Mapping[str, Any]) -> TypedEditingGraph:
    raw = _require_mapping(bundle.get("graph"), "bundle.graph")
    try:
        graph = TypedEditingGraph.from_contract_dict(dict(raw))
    except Exception as exc:
        raise ProductRunManifestError("bundle.graph cannot be reconstructed") from exc
    expected = _require_sha(bundle.get("graph_hash"), "bundle.graph_hash", length=64)
    if graph.content_hash() != expected:
        raise ProductRunManifestError("bundle.graph_hash mismatch")
    return graph


def _verified_render_manifest(bundle: Mapping[str, Any]) -> dict[str, Any]:
    raw = dict(_require_mapping(bundle.get("render_manifest"), "bundle.render_manifest"))
    observed = _require_sha(raw.get("manifest_hash"), "bundle.render_manifest.manifest_hash", length=64)
    unsigned = deepcopy(raw)
    unsigned.pop("manifest_hash", None)
    if canonical_hash(unsigned) != observed:
        raise ProductRunManifestError("bundle.render_manifest.manifest_hash mismatch")
    return raw


def _verified_bundle(bundle: Mapping[str, Any]) -> tuple[TypedEditingGraph, dict[str, Any]]:
    if bundle.get("schema") != "motion-os.studio-execution-bundle/v1":
        raise ProductRunManifestError("unsupported Studio execution bundle schema")
    if bundle.get("stage") != "STUDIO_COMPILED":
        raise ProductRunManifestError("Studio bundle is not compiled")
    if bundle.get("execution_started") is not True:
        raise ProductRunManifestError("Studio execution transition was not authorized")
    if bundle.get("render_started") is not False:
        raise ProductRunManifestError("Studio bundle must describe the pre-render boundary")

    _require_nonempty_text(bundle.get("content_id"), "bundle.content_id")
    prv = _require_nonempty_text(bundle.get("provenance_root"), "bundle.provenance_root")
    mnf = _require_nonempty_text(bundle.get("replay_fingerprint"), "bundle.replay_fingerprint")
    if not prv.startswith("PRV_"):
        raise ProductRunManifestError("bundle.provenance_root is invalid")
    if not mnf.startswith("MNF_"):
        raise ProductRunManifestError("bundle.replay_fingerprint is invalid")

    beat_ids = bundle.get("semantic_beat_ids")
    if not isinstance(beat_ids, list) or not beat_ids or not all(isinstance(item, str) and item for item in beat_ids):
        raise ProductRunManifestError("bundle.semantic_beat_ids must be a non-empty string list")
    if len(set(beat_ids)) != len(beat_ids):
        raise ProductRunManifestError("bundle.semantic_beat_ids must be unique")

    graph = _verified_graph(bundle)
    graph_beats = {node.id for node in graph.nodes if node.kind == "NarrativeBeat"}
    if graph_beats != set(beat_ids):
        raise ProductRunManifestError("Studio graph semantic beats differ from authorized beat identities")

    asset_manifest = _require_mapping(bundle.get("asset_manifest"), "bundle.asset_manifest")
    expected_asset_hash = _require_sha(bundle.get("asset_manifest_hash"), "bundle.asset_manifest_hash", length=64)
    if canonical_hash(asset_manifest) != expected_asset_hash:
        raise ProductRunManifestError("bundle.asset_manifest_hash mismatch")

    runtime_spec = _require_mapping(bundle.get("runtime_spec"), "bundle.runtime_spec")
    expected_runtime_hash = _require_sha(bundle.get("runtime_spec_hash"), "bundle.runtime_spec_hash", length=64)
    if canonical_hash(runtime_spec) != expected_runtime_hash:
        raise ProductRunManifestError("bundle.runtime_spec_hash mismatch")

    _require_sha(bundle.get("execution_hash"), "bundle.execution_hash", length=64)
    render_doc = _verified_render_manifest(bundle)
    return graph, render_doc


def _runtime_lineage(runtime_spec: Mapping[str, Any]) -> tuple[list[str], list[str | None]]:
    scenes = runtime_spec.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ProductRunManifestError("runtime spec must contain scenes")
    ids: list[str] = []
    transitions: list[str | None] = []
    for index, scene in enumerate(scenes):
        if not isinstance(scene, Mapping):
            raise ProductRunManifestError(f"runtime scene {index} must be an object")
        scene_id = _require_nonempty_text(scene.get("id"), f"runtime scene {index}.id")
        transition = scene.get("transition")
        if transition is None:
            transition_type = None
        elif isinstance(transition, Mapping):
            raw = transition.get("type")
            transition_type = raw if isinstance(raw, str) else None
        else:
            raise ProductRunManifestError(f"runtime scene {scene_id}.transition must be object/null")
        ids.append(scene_id)
        transitions.append(transition_type)
    if len(set(ids)) != len(ids):
        raise ProductRunManifestError("runtime scene IDs must be unique")
    return ids, transitions


def build_product_run_manifest(
    bundle: Mapping[str, Any],
    runtime_evidence: Mapping[str, Any],
    runtime_spec_document: Mapping[str, Any],
    *,
    git_sha: str,
    artifact_ref: str,
    artifact_sha256: str,
    artifact_bytes: int,
    runtime_spec_file_sha256: str,
) -> dict[str, Any]:
    git_sha = _require_sha(git_sha, "git_sha", length=40)
    artifact_ref = _require_nonempty_text(artifact_ref, "artifact_ref")
    artifact_sha256 = _require_sha(artifact_sha256, "artifact_sha256", length=64)
    runtime_spec_file_sha256 = _require_sha(runtime_spec_file_sha256, "runtime_spec_file_sha256", length=64)
    if not isinstance(artifact_bytes, int) or isinstance(artifact_bytes, bool) or artifact_bytes <= 0:
        raise ProductRunManifestError("artifact_bytes must be a positive integer")

    graph, render_doc = _verified_bundle(bundle)
    runtime_spec = _require_mapping(bundle.get("runtime_spec"), "bundle.runtime_spec")
    if dict(runtime_spec_document) != dict(runtime_spec):
        raise ProductRunManifestError("runtime spec file content differs from Studio bundle")

    evidence = _require_mapping(runtime_evidence, "runtime_evidence")
    if evidence.get("technical_runtime_gate") != "PASS":
        raise ProductRunManifestError("physical runtime gate is not PASS")
    if evidence.get("errors") != []:
        raise ProductRunManifestError("physical runtime evidence contains errors")
    if _require_sha(evidence.get("video_sha256"), "runtime_evidence.video_sha256", length=64) != artifact_sha256:
        raise ProductRunManifestError("physical artifact SHA differs from runtime evidence")
    if evidence.get("video_bytes") != artifact_bytes:
        raise ProductRunManifestError("physical artifact size differs from runtime evidence")
    if _require_sha(evidence.get("spec_sha256"), "runtime_evidence.spec_sha256", length=64) != runtime_spec_file_sha256:
        raise ProductRunManifestError("runtime spec file SHA differs from runtime evidence")

    expected_scene_ids, expected_transitions = _runtime_lineage(runtime_spec)
    lineage = _require_mapping(evidence.get("spec_lineage"), "runtime_evidence.spec_lineage")
    if lineage.get("scene_ids") != expected_scene_ids:
        raise ProductRunManifestError("physical runtime scene lineage differs from Studio runtime spec")
    if lineage.get("transition_types") != expected_transitions:
        raise ProductRunManifestError("physical runtime transition lineage differs from Studio runtime spec")

    qa_summary = {
        "technical_runtime_gate": "PASS",
        "creative_authority": evidence.get("creative_authority", "none"),
        "temporal_critic_authority": evidence.get("temporal_critic_authority", "none"),
        "runtime_evidence_schema": evidence.get("schema"),
    }
    recovery = recovery_manifest(
        graph,
        git_sha=git_sha,
        asset_manifest_hash=_require_sha(bundle.get("asset_manifest_hash"), "bundle.asset_manifest_hash", length=64),
        render_manifest=render_doc,
        qa_summary=qa_summary,
        artifact_refs=[artifact_ref],
    )
    if recovery.get("recovery_ready") is not True:
        raise ProductRunManifestError("zero-context recovery manifest is not ready")

    physical_artifact = {"ref": artifact_ref, "sha256": artifact_sha256, "bytes": artifact_bytes}
    identity_seed = {
        "git_sha": git_sha,
        "content_id": bundle["content_id"],
        "execution_hash": bundle["execution_hash"],
        "artifact_sha256": artifact_sha256,
    }
    manifest: dict[str, Any] = {
        "schema": "motion-os.product-run-manifest/v1",
        "status": "TECHNICAL_PRODUCT_E2E_VERIFIED",
        "run_id": "RUN_" + canonical_hash(identity_seed)[:20].upper(),
        "git_sha": git_sha,
        "content_id": bundle["content_id"],
        "provenance_root": bundle["provenance_root"],
        "replay_fingerprint": bundle["replay_fingerprint"],
        "semantic_beat_ids": list(bundle["semantic_beat_ids"]),
        "execution_hash": bundle["execution_hash"],
        "bundle_hash": canonical_hash(bundle),
        "graph_hash": bundle["graph_hash"],
        "asset_manifest_hash": bundle["asset_manifest_hash"],
        "render_manifest_hash": render_doc["manifest_hash"],
        "runtime_spec_hash": bundle["runtime_spec_hash"],
        "runtime_spec_file_sha256": runtime_spec_file_sha256,
        "runtime_evidence_hash": canonical_hash(runtime_evidence),
        "physical_artifact": physical_artifact,
        "qa_summary": qa_summary,
        "recovery": recovery,
        "production_authority": False,
        "creative_authority": False,
        "provider_authority": False,
        "project_done": False,
    }
    manifest["manifest_hash"] = canonical_hash(manifest)
    verify_product_run_manifest(manifest)
    return manifest


def verify_product_run_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema") != "motion-os.product-run-manifest/v1":
        raise ProductRunManifestError("unsupported product run manifest schema")
    if manifest.get("status") != "TECHNICAL_PRODUCT_E2E_VERIFIED":
        raise ProductRunManifestError("product run manifest status is not verified")
    if manifest.get("production_authority") is not False:
        raise ProductRunManifestError("technical run cannot self-promote production authority")
    if manifest.get("creative_authority") is not False:
        raise ProductRunManifestError("technical run cannot self-promote creative authority")
    if manifest.get("provider_authority") is not False:
        raise ProductRunManifestError("technical run cannot self-promote provider authority")
    if manifest.get("project_done") is not False:
        raise ProductRunManifestError("technical run cannot claim PROJECT_DONE")

    _require_sha(manifest.get("git_sha"), "manifest.git_sha", length=40)
    for field in (
        "bundle_hash",
        "graph_hash",
        "asset_manifest_hash",
        "render_manifest_hash",
        "runtime_spec_hash",
        "runtime_spec_file_sha256",
        "runtime_evidence_hash",
    ):
        _require_sha(manifest.get(field), f"manifest.{field}", length=64)

    artifact = _require_mapping(manifest.get("physical_artifact"), "manifest.physical_artifact")
    _require_nonempty_text(artifact.get("ref"), "manifest.physical_artifact.ref")
    _require_sha(artifact.get("sha256"), "manifest.physical_artifact.sha256", length=64)
    if not isinstance(artifact.get("bytes"), int) or isinstance(artifact.get("bytes"), bool) or artifact.get("bytes") <= 0:
        raise ProductRunManifestError("manifest physical artifact bytes must be positive")

    recovery = _require_mapping(manifest.get("recovery"), "manifest.recovery")
    if recovery.get("recovery_ready") is not True:
        raise ProductRunManifestError("manifest recovery is not ready")
    if recovery.get("git_sha") != manifest.get("git_sha"):
        raise ProductRunManifestError("manifest/recovery Git SHA mismatch")
    if recovery.get("graph_hash") != manifest.get("graph_hash"):
        raise ProductRunManifestError("manifest/recovery graph hash mismatch")
    refs = recovery.get("artifact_refs")
    if not isinstance(refs, list) or artifact.get("ref") not in refs:
        raise ProductRunManifestError("manifest/recovery artifact reference mismatch")

    observed_hash = _require_sha(manifest.get("manifest_hash"), "manifest.manifest_hash", length=64)
    unsigned = deepcopy(dict(manifest))
    unsigned.pop("manifest_hash", None)
    if canonical_hash(unsigned) != observed_hash:
        raise ProductRunManifestError("manifest hash mismatch")
