from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class Surface(str, Enum):
    GITHUB_BOOTSTRAP = "GITHUB_BOOTSTRAP"
    REPO_EVENT = "REPO_EVENT"
    RUNTIME_EVENTSTORE = "RUNTIME_EVENTSTORE"


@dataclass(frozen=True, slots=True)
class SessionIdentity:
    project_id: str
    agent_id: str
    session_id: str
    workstream_id: str
    correlation_id: str

    def __post_init__(self) -> None:
        if not self.project_id.startswith("motion://project/"):
            raise ValueError("project_id must be canonical")
        if not self.agent_id.startswith("motion://agent/"):
            raise ValueError("agent_id must be canonical")
        if not self.session_id.startswith("motion://session/"):
            raise ValueError("session_id must be canonical")
        if not self.workstream_id.startswith("motion://workstream/"):
            raise ValueError("workstream_id must be canonical")
        if not self.correlation_id:
            raise ValueError("correlation_id required")


@dataclass(frozen=True, slots=True)
class SurfaceEvent:
    surface: Surface
    logical_id: str
    payload_hash: str
    event: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.logical_id:
            raise ValueError("logical_id required")
        if len(self.payload_hash) != 64 or any(c not in "0123456789abcdef" for c in self.payload_hash):
            raise ValueError("payload_hash must be lowercase sha256")


@dataclass(frozen=True, slots=True, order=True)
class SessionGraphNode:
    node_id: str
    node_type: str
    properties_json: str = "{}"


@dataclass(frozen=True, slots=True, order=True)
class SessionGraphEdge:
    source: str
    relation: str
    target: str
    properties_json: str = "{}"


@dataclass(frozen=True, slots=True)
class SessionGraphSnapshot:
    session_id: str
    live_main_sha: str
    event_watermark: int
    nodes: tuple[SessionGraphNode, ...]
    edges: tuple[SessionGraphEdge, ...]
    projection_hash: str

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "live_main_sha": self.live_main_sha,
            "event_watermark": self.event_watermark,
            "nodes": [asdict(x) for x in self.nodes],
            "edges": [asdict(x) for x in self.edges],
        }

    def verify_hash(self) -> bool:
        expected = hashlib.sha256(_canonical_json(self.canonical_payload()).encode()).hexdigest()
        return expected == self.projection_hash


class EventSurfaceConflict(ValueError):
    pass


def deduplicate_surface_events(events: Iterable[SurfaceEvent]) -> tuple[SurfaceEvent, ...]:
    chosen: dict[str, SurfaceEvent] = {}
    for item in events:
        existing = chosen.get(item.logical_id)
        if existing is None:
            chosen[item.logical_id] = item
            continue
        if existing.payload_hash != item.payload_hash:
            raise EventSurfaceConflict(f"conflicting payload for logical event {item.logical_id}")
        if item.surface.value < existing.surface.value:
            chosen[item.logical_id] = item
    return tuple(sorted(chosen.values(), key=lambda x: x.logical_id))


def reconcile_github_lifecycle(projected: Mapping[str, str], live: Mapping[str, str]) -> dict[str, str]:
    """Live GitHub executable lifecycle overrides stale historical projection."""
    result = dict(projected)
    for key, value in live.items():
        if not key.startswith(("pr:", "branch:", "commit:", "ci:", "main:")):
            raise ValueError(f"unsupported live GitHub lifecycle key: {key}")
        result[key] = value
    return dict(sorted(result.items()))


class SessionGraphCompiler:
    def compile(
        self,
        *,
        identity: SessionIdentity,
        live_main_sha: str,
        event_watermark: int,
        events: Sequence[Mapping[str, Any]],
        resources: Iterable[str] = (),
        live_lifecycle: Mapping[str, str] | None = None,
    ) -> SessionGraphSnapshot:
        if len(live_main_sha) < 7:
            raise ValueError("live_main_sha required")
        if event_watermark < 0:
            raise ValueError("event_watermark must be >= 0")

        nodes: dict[tuple[str, str], SessionGraphNode] = {}
        edges: dict[tuple[str, str, str, str], SessionGraphEdge] = {}

        def add_node(node_id: str, node_type: str, properties: Mapping[str, Any] | None = None) -> None:
            key = (node_id, node_type)
            props = _canonical_json(properties or {})
            candidate = SessionGraphNode(node_id, node_type, props)
            existing = nodes.get(key)
            if existing is not None and existing.properties_json != props:
                raise ValueError(f"contradictory session graph node {node_id}")
            nodes[key] = candidate

        def add_edge(source: str, relation: str, target: str, properties: Mapping[str, Any] | None = None) -> None:
            props = _canonical_json(properties or {})
            edges[(source, relation, target, props)] = SessionGraphEdge(source, relation, target, props)

        add_node(identity.project_id, "Project")
        add_node(identity.agent_id, "Agent")
        add_node(identity.session_id, "Session", {"correlation_id": identity.correlation_id})
        add_node(identity.workstream_id, "Workstream")
        add_edge(identity.agent_id, "AGENT_OPENED_SESSION", identity.session_id)
        add_edge(identity.session_id, "SESSION_WORKS_ON", identity.workstream_id)
        add_edge(identity.workstream_id, "BELONGS_TO", identity.project_id)

        for resource in sorted(set(resources)):
            resource_id = f"motion://resource/{hashlib.sha256(resource.encode()).hexdigest()[:24]}"
            add_node(resource_id, "Resource", {"scope": resource})
            add_edge(identity.session_id, "SESSION_TOUCHES", resource_id)

        seen_event_ids: set[str] = set()
        for index, event in enumerate(events):
            event_id = str(event.get("event_id", ""))
            if not event_id:
                raise ValueError("event_id missing")
            if event_id in seen_event_ids:
                raise ValueError("duplicate event_id in session projection")
            seen_event_ids.add(event_id)
            if event.get("session_id") != identity.session_id:
                raise ValueError("cross-session event passed to session compiler")
            event_uri = f"motion://event/{event_id}"
            add_node(event_uri, "Event", {
                "event_type": event.get("event_type"),
                "correlation_id": event.get("correlation_id"),
                "index": index,
            })
            add_edge(identity.session_id, "SESSION_EMITTED", event_uri, {"index": index})
            causation = event.get("causation_id")
            if causation:
                add_edge(event_uri, "EVENT_CAUSED_BY", f"motion://event/{causation}")
            parents = tuple(event.get("parent_event_ids", ()) or ())
            if len(set(parents)) != len(parents):
                raise ValueError("duplicate parent_event_ids")
            for parent in parents:
                add_edge(event_uri, "EVENT_PARENT", f"motion://event/{parent}")

        lifecycle = reconcile_github_lifecycle({}, live_lifecycle or {})
        for key, value in lifecycle.items():
            node_id = f"motion://live/{hashlib.sha256(key.encode()).hexdigest()[:24]}"
            add_node(node_id, "LiveGitHubFact", {"key": key, "value": value})
            add_edge(identity.session_id, "RECONCILED_WITH", node_id)

        sorted_nodes = tuple(sorted(nodes.values()))
        sorted_edges = tuple(sorted(edges.values()))
        payload = {
            "session_id": identity.session_id,
            "live_main_sha": live_main_sha,
            "event_watermark": event_watermark,
            "nodes": [asdict(x) for x in sorted_nodes],
            "edges": [asdict(x) for x in sorted_edges],
        }
        digest = hashlib.sha256(_canonical_json(payload).encode()).hexdigest()
        return SessionGraphSnapshot(
            session_id=identity.session_id,
            live_main_sha=live_main_sha,
            event_watermark=event_watermark,
            nodes=sorted_nodes,
            edges=sorted_edges,
            projection_hash=digest,
        )
