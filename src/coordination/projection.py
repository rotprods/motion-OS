from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping, Protocol

from .events import CoordinationEvent


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True, slots=True, order=True)
class GraphNode:
    node_id: str
    node_type: str
    properties_json: str = "{}"

    @classmethod
    def create(cls, node_id: str, node_type: str, properties: Mapping[str, Any] | None = None) -> "GraphNode":
        return cls(node_id=node_id, node_type=node_type, properties_json=_canonical_json(properties or {}))


@dataclass(frozen=True, slots=True, order=True)
class GraphEdge:
    source: str
    relation: str
    target: str
    properties_json: str = "{}"

    @classmethod
    def create(cls, source: str, relation: str, target: str, properties: Mapping[str, Any] | None = None) -> "GraphEdge":
        return cls(source=source, relation=relation, target=target, properties_json=_canonical_json(properties or {}))


@dataclass(frozen=True, slots=True)
class ProjectionSnapshot:
    projection_version: int
    source_event_count: int
    last_event_id: str | None
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    projection_hash: str

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "projection_version": self.projection_version,
            "source_event_count": self.source_event_count,
            "last_event_id": self.last_event_id,
            "nodes": [asdict(x) for x in self.nodes],
            "edges": [asdict(x) for x in self.edges],
        }

    def verify_hash(self) -> bool:
        digest = hashlib.sha256(_canonical_json(self.canonical_payload()).encode("utf-8")).hexdigest()
        return digest == self.projection_hash


class CosProjectionSink(Protocol):
    """Narrow adapter boundary for loading a verified snapshot into COS.

    Implementations must not write back to coordination authority as a side effect.
    """

    def replace_projection(self, snapshot: ProjectionSnapshot) -> str: ...


def aggregate_uri(event: CoordinationEvent) -> str:
    raw = event.aggregate_id
    if raw.startswith("motion://"):
        return raw
    return f"motion://{event.aggregate_type}/{raw}"


class CoordinationGraphProjector:
    """Pure deterministic event→graph projection compiler."""

    def build(self, events: Iterable[CoordinationEvent], *, projection_version: int) -> ProjectionSnapshot:
        if projection_version < 1:
            raise ValueError("projection_version must be >= 1")

        nodes: dict[tuple[str, str], GraphNode] = {}
        edges: dict[tuple[str, str, str, str], GraphEdge] = {}
        event_count = 0
        last_event_id: str | None = None

        def add_node(node: GraphNode) -> None:
            nodes[(node.node_id, node.node_type)] = node

        def add_edge(edge: GraphEdge) -> None:
            edges[(edge.source, edge.relation, edge.target, edge.properties_json)] = edge

        for event in events:
            event_count += 1
            last_event_id = event.event_id
            event_uri = f"motion://event/{event.event_id}"
            session_uri = event.session_id
            agent_uri = event.agent_id
            project_uri = event.project_id
            target_uri = aggregate_uri(event)

            add_node(GraphNode.create(project_uri, "Project"))
            add_node(GraphNode.create(agent_uri, "Agent"))
            add_node(GraphNode.create(session_uri, "Session"))
            add_node(GraphNode.create(target_uri, event.aggregate_type.title()))
            add_node(GraphNode.create(event_uri, "Event", {
                "event_type": event.event_type,
                "aggregate_revision": event.aggregate_revision,
                "expected_revision": event.expected_revision,
                "occurred_at": event.occurred_at,
                "recorded_at": event.recorded_at,
                "payload_hash": event.payload_hash,
                "provenance_hash": event.provenance_hash,
                "sensitivity": event.sensitivity,
            }))

            add_edge(GraphEdge.create(session_uri, "RUN_BY", agent_uri))
            add_edge(GraphEdge.create(session_uri, "IN_PROJECT", project_uri))
            add_edge(GraphEdge.create(agent_uri, "EMITTED", event_uri))
            add_edge(GraphEdge.create(event_uri, "AFFECTS", target_uri))

            if event.workstream_id:
                add_node(GraphNode.create(event.workstream_id, "Workstream"))
                add_edge(GraphEdge.create(session_uri, "WORKS_IN", event.workstream_id))
                add_edge(GraphEdge.create(event_uri, "IN_WORKSTREAM", event.workstream_id))

            causal_parents = list(event.parent_event_ids)
            if event.causation_id and event.causation_id not in causal_parents:
                causal_parents.append(event.causation_id)
            for parent_id in causal_parents:
                cause_uri = f"motion://event/{parent_id}"
                add_node(GraphNode.create(cause_uri, "Event"))
                add_edge(GraphEdge.create(event_uri, "CAUSED_BY", cause_uri))

            correlation_uri = f"motion://correlation/{event.correlation_id}"
            add_node(GraphNode.create(correlation_uri, "Correlation"))
            add_edge(GraphEdge.create(event_uri, "CORRELATED_WITH", correlation_uri))

            for resource_uri in event.resource_scope:
                add_node(GraphNode.create(resource_uri, "Resource"))
                add_edge(GraphEdge.create(event_uri, "TOUCHES", resource_uri))

            if event.git:
                repo = event.git.get("repository")
                branch = event.git.get("branch")
                pr_number = event.git.get("pr_number")
                sha = event.git.get("sha")
                if repo:
                    repo_uri = f"motion://repo/{repo}"
                    add_node(GraphNode.create(repo_uri, "Repository"))
                    add_edge(GraphEdge.create(event_uri, "IN_REPOSITORY", repo_uri))
                if repo and branch:
                    branch_uri = f"motion://repo/{repo}/branch/{branch}"
                    add_node(GraphNode.create(branch_uri, "Branch"))
                    add_edge(GraphEdge.create(event_uri, "ON_BRANCH", branch_uri))
                if repo and pr_number is not None:
                    pr_uri = f"motion://repo/{repo}/pr/{pr_number}"
                    add_node(GraphNode.create(pr_uri, "PullRequest"))
                    add_edge(GraphEdge.create(event_uri, "IN_PR", pr_uri))
                if repo and sha:
                    commit_uri = f"motion://repo/{repo}/commit/{sha}"
                    add_node(GraphNode.create(commit_uri, "Commit"))
                    add_edge(GraphEdge.create(event_uri, "AT_COMMIT", commit_uri))

            payload = dict(event.payload)
            resource_uri = payload.get("resource_uri")
            if isinstance(resource_uri, str):
                add_node(GraphNode.create(resource_uri, "Resource"))
                add_edge(GraphEdge.create(event_uri, "TOUCHES", resource_uri))
                if event.event_type == "WORK_CLAIMED":
                    add_edge(GraphEdge.create(agent_uri, "OWNS_LEASE", resource_uri, {
                        "fencing_token": payload.get("fencing_token"),
                        "lease_id": payload.get("lease_id"),
                    }))

            task_uri = payload.get("task_uri")
            if isinstance(task_uri, str):
                add_node(GraphNode.create(task_uri, "Task"))
                if event.event_type.startswith("TASK_"):
                    add_edge(GraphEdge.create(agent_uri, "EXECUTES", task_uri, {"state": event.event_type.removeprefix("TASK_")}))

            governs_uri = payload.get("governs_uri")
            if isinstance(governs_uri, str) and event.event_type.startswith("DECISION_"):
                add_node(GraphNode.create(governs_uri, "Resource"))
                add_edge(GraphEdge.create(target_uri, "GOVERNS", governs_uri, {"state": event.event_type.removeprefix("DECISION_")}))

        sorted_nodes = tuple(sorted(nodes.values()))
        sorted_edges = tuple(sorted(edges.values()))
        payload = {
            "projection_version": projection_version,
            "source_event_count": event_count,
            "last_event_id": last_event_id,
            "nodes": [asdict(x) for x in sorted_nodes],
            "edges": [asdict(x) for x in sorted_edges],
        }
        projection_hash = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
        return ProjectionSnapshot(
            projection_version=projection_version,
            source_event_count=event_count,
            last_event_id=last_event_id,
            nodes=sorted_nodes,
            edges=sorted_edges,
            projection_hash=projection_hash,
        )
