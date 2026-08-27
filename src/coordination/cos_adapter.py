from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from .projection import ProjectionSnapshot


COS_REPOSITORY = "rotprods/cos-graph-engine"
# Pinned integration baseline inspected during Phase07. Promotion requires an
# explicit compatibility decision when this pin changes.
COS_BASELINE_COMMIT = "3ae197ebe6024b68ea2cc33a4c54c76fbc8d1e83"
COS_CONTRACT_VERSION = 1


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class CosProjectionBundle:
    contract_version: int
    cos_repository: str
    cos_baseline_commit: str
    source_projection_hash: str
    source_projection_version: int
    level13_agent: Mapping[str, Any]
    level15_workflow: Mapping[str, Any]
    generic_graph: Mapping[str, Any]
    bundle_hash: str

    def canonical_payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["bundle_hash"] = ""
        return data

    def verify_hash(self) -> bool:
        digest = hashlib.sha256(_canonical_json(self.canonical_payload()).encode("utf-8")).hexdigest()
        return digest == self.bundle_hash


class CosShadowAdapter:
    """MOTION-owned one-way compiler into COS-compatible shadow data.

    COS Level13 AgentGraph and Level15 WorkflowGraph use generated internal IDs,
    so the authoritative MOTION URIs are preserved in names/config metadata and
    the complete typed graph remains available in `generic_graph`. This adapter
    cannot mutate MOTION coordination state.
    """

    def compile_bundle(self, snapshot: ProjectionSnapshot) -> CosProjectionBundle:
        if not snapshot.verify_hash():
            raise ValueError("source projection hash verification failed")

        nodes = [asdict(node) for node in snapshot.nodes]
        edges = [asdict(edge) for edge in snapshot.edges]
        agents = [node for node in snapshot.nodes if node.node_type == "Agent"]
        workstreams = [node for node in snapshot.nodes if node.node_type == "Workstream"]

        level13 = {
            "name": "MOTION.OS Agent Shadow",
            "source_projection_hash": snapshot.projection_hash,
            "agents": [
                {
                    "motion_uri": node.node_id,
                    "role": "coordinator",
                    "status": "executing",
                    "capabilities": [],
                    "tools": [],
                    "memoryIds": [],
                    "confidence": 1.0,
                }
                for node in agents
            ],
            "relations": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "type": "collaborates_with",
                    "motion_relation": edge.relation,
                }
                for edge in snapshot.edges
                if edge.source.startswith("motion://agent/") and edge.target.startswith("motion://agent/")
            ],
        }

        level15 = {
            "name": "MOTION.OS Workstream Shadow",
            "description": "Derived coordination/workstream projection; never execution authority.",
            "enabled": False,
            "source_projection_hash": snapshot.projection_hash,
            "workstreams": [
                {"motion_uri": node.node_id, "type": "action", "service": "motion-os"}
                for node in workstreams
            ],
            "dependencies": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "motion_relation": edge.relation,
                }
                for edge in snapshot.edges
                if edge.relation in {"DEPENDS_ON", "BLOCKS", "IN_WORKSTREAM"}
            ],
        }

        generic = {
            "projection_version": snapshot.projection_version,
            "projection_hash": snapshot.projection_hash,
            "last_event_id": snapshot.last_event_id,
            "nodes": nodes,
            "edges": edges,
        }
        draft = CosProjectionBundle(
            contract_version=COS_CONTRACT_VERSION,
            cos_repository=COS_REPOSITORY,
            cos_baseline_commit=COS_BASELINE_COMMIT,
            source_projection_hash=snapshot.projection_hash,
            source_projection_version=snapshot.projection_version,
            level13_agent=level13,
            level15_workflow=level15,
            generic_graph=generic,
            bundle_hash="",
        )
        digest = hashlib.sha256(_canonical_json(draft.canonical_payload()).encode("utf-8")).hexdigest()
        return CosProjectionBundle(**{**asdict(draft), "bundle_hash": digest})
