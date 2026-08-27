from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class ContentLineageError(ValueError):
    pass


@dataclass(frozen=True, slots=True, order=True)
class LineageNode:
    node_id: str
    node_type: str
    properties_json: str = "{}"

    @classmethod
    def create(cls, node_id: str, node_type: str, properties: Mapping[str, Any] | None = None) -> "LineageNode":
        return cls(node_id, node_type, _canonical_json(properties or {}))


@dataclass(frozen=True, slots=True, order=True)
class LineageEdge:
    source: str
    relation: str
    target: str
    properties_json: str = "{}"

    @classmethod
    def create(cls, source: str, relation: str, target: str, properties: Mapping[str, Any] | None = None) -> "LineageEdge":
        return cls(source, relation, target, _canonical_json(properties or {}))


@dataclass(frozen=True, slots=True)
class ContentLineageSnapshot:
    content_id: str
    provenance_root: str
    replay_fingerprint: str
    beat_ids: tuple[str, ...]
    nodes: tuple[LineageNode, ...]
    edges: tuple[LineageEdge, ...]
    snapshot_hash: str

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "content_id": self.content_id,
            "provenance_root": self.provenance_root,
            "replay_fingerprint": self.replay_fingerprint,
            "beat_ids": list(self.beat_ids),
            "nodes": [asdict(node) for node in self.nodes],
            "edges": [asdict(edge) for edge in self.edges],
        }

    def verify_hash(self) -> bool:
        return hashlib.sha256(_canonical_json(self.canonical_payload()).encode("utf-8")).hexdigest() == self.snapshot_hash


class Phase06ContentLineageBridge:
    """Read-only Phase06→coordination/COS projection compiler.

    Authority remains upstream in the sealed Phase06 manifest/handoff. This bridge
    validates identity continuity and projects facts; it cannot repair or replace
    PRV/MNF/semantic-beat authority.
    """

    def compile(
        self,
        *,
        manifest: Mapping[str, Any],
        handoff: Mapping[str, Any],
        opportunity: Mapping[str, Any] | None = None,
        publications: Iterable[Mapping[str, Any]] = (),
        performance_records: Iterable[Mapping[str, Any]] = (),
        experiments: Iterable[Mapping[str, Any]] = (),
    ) -> ContentLineageSnapshot:
        content_id = manifest.get("content_id")
        if not isinstance(content_id, str) or not content_id:
            raise ContentLineageError("manifest content_id missing")
        if handoff.get("content_id") != content_id:
            raise ContentLineageError("handoff content_id mismatch")

        provenance = manifest.get("provenance_chain")
        integrity = manifest.get("integrity")
        beats = manifest.get("semantic_beats")
        if not isinstance(provenance, Mapping) or not isinstance(integrity, Mapping):
            raise ContentLineageError("sealed manifest provenance/integrity missing")
        if not isinstance(beats, list) or not beats:
            raise ContentLineageError("manifest semantic beats missing")

        provenance_root = provenance.get("root")
        replay_fingerprint = integrity.get("replay_fingerprint")
        if not isinstance(provenance_root, str) or not provenance_root.startswith("PRV_"):
            raise ContentLineageError("invalid provenance root")
        if not isinstance(replay_fingerprint, str) or not replay_fingerprint.startswith("MNF_"):
            raise ContentLineageError("invalid replay fingerprint")

        beat_ids = tuple(str(beat.get("id", "")) for beat in beats if isinstance(beat, Mapping))
        if len(beat_ids) != len(beats) or any(not beat for beat in beat_ids) or len(set(beat_ids)) != len(beat_ids):
            raise ContentLineageError("invalid semantic beat identity")

        handoff_prv = handoff.get("provenance_root")
        handoff_mnf = handoff.get("replay_fingerprint")
        handoff_beats_raw = handoff.get("semantic_beat_ids", handoff.get("beat_ids"))
        if handoff_prv != provenance_root:
            raise ContentLineageError("handoff provenance root mismatch")
        if handoff_mnf != replay_fingerprint:
            raise ContentLineageError("handoff replay fingerprint mismatch")
        if tuple(handoff_beats_raw or ()) != beat_ids:
            raise ContentLineageError("handoff semantic beat IDs mismatch")

        content_uri = f"motion://content/{content_id}"
        nodes: dict[tuple[str, str], LineageNode] = {}
        edges: dict[tuple[str, str, str, str], LineageEdge] = {}

        def add_node(node: LineageNode) -> None:
            nodes[(node.node_id, node.node_type)] = node

        def add_edge(edge: LineageEdge) -> None:
            edges[(edge.source, edge.relation, edge.target, edge.properties_json)] = edge

        add_node(LineageNode.create(content_uri, "Content", {
            "core_thesis": manifest.get("core_thesis"),
            "hook": manifest.get("hook"),
            "viral_driver": manifest.get("viral_driver"),
        }))
        prv_uri = f"motion://provenance/{provenance_root}"
        mnf_uri = f"motion://manifest/{replay_fingerprint}"
        add_node(LineageNode.create(prv_uri, "ProvenanceRoot"))
        add_node(LineageNode.create(mnf_uri, "ReplayFingerprint"))
        add_edge(LineageEdge.create(content_uri, "PROVENANCE_ROOT", prv_uri))
        add_edge(LineageEdge.create(content_uri, "SEALED_BY", mnf_uri))

        for index, beat_id in enumerate(beat_ids):
            beat_uri = f"{content_uri}/beat/{beat_id}"
            beat = beats[index]
            add_node(LineageNode.create(beat_uri, "SemanticBeat", {
                "function": beat.get("function"),
                "text": beat.get("text"),
                "index": index,
            }))
            add_edge(LineageEdge.create(content_uri, "HAS_BEAT", beat_uri, {"index": index}))

        handoff_uri = f"{content_uri}/studio-handoff/{replay_fingerprint}"
        add_node(LineageNode.create(handoff_uri, "StudioHandoff", {
            "render_job_id": handoff.get("render_job_id"),
        }))
        add_edge(LineageEdge.create(content_uri, "AUTHORIZED_HANDOFF", handoff_uri))
        add_edge(LineageEdge.create(handoff_uri, "DERIVED_FROM", mnf_uri))

        if opportunity is not None:
            opportunity_id = opportunity.get("opportunity_id")
            if not isinstance(opportunity_id, str) or not opportunity_id:
                raise ContentLineageError("opportunity_id missing")
            opportunity_uri = f"motion://opportunity/{opportunity_id}"
            add_node(LineageNode.create(opportunity_uri, "Opportunity", {
                "goal": opportunity.get("goal"),
                "score": opportunity.get("score"),
                "decision": opportunity.get("decision"),
                "account_id": opportunity.get("account_id"),
                "audience_id": opportunity.get("audience_id"),
            }))
            add_edge(LineageEdge.create(opportunity_uri, "PRODUCED_CONTENT", content_uri))

        for publication in publications:
            if publication.get("content_id") != content_id:
                raise ContentLineageError("publication content_id mismatch")
            publication_id = publication.get("publication_id") or publication.get("id")
            if not isinstance(publication_id, str) or not publication_id:
                raise ContentLineageError("publication identity missing")
            publication_uri = f"motion://publication/{publication_id}"
            add_node(LineageNode.create(publication_uri, "Publication", {
                "platform": publication.get("platform"),
                "account_id": publication.get("account_id"),
                "published_at": publication.get("published_at"),
                "master_hash": publication.get("master_hash"),
            }))
            add_edge(LineageEdge.create(content_uri, "PUBLISHED_AS", publication_uri))

        for idx, performance in enumerate(performance_records):
            if performance.get("content_id") != content_id:
                raise ContentLineageError("performance content_id mismatch")
            perf_id = performance.get("metric_snapshot_id") or f"{content_id}:{performance.get('platform','unknown')}:{idx}"
            perf_uri = f"motion://metric/{perf_id}"
            causal_status = performance.get("causal_status", "OBSERVED_CORRELATION")
            if causal_status not in {"OBSERVED_CORRELATION", "CANDIDATE_HYPOTHESIS", "REPEATED_PATTERN", "CONTROLLED_TEST", "PROMOTED_RULE"}:
                raise ContentLineageError("unknown causal status")
            add_node(LineageNode.create(perf_uri, "PerformanceSnapshot", {
                "platform": performance.get("platform"),
                "views": performance.get("views"),
                "completion_rate": performance.get("completion_rate"),
                "shares": performance.get("shares"),
                "saves": performance.get("saves"),
                "cta_conversions": performance.get("cta_conversions"),
                "causal_status": causal_status,
            }))
            add_edge(LineageEdge.create(content_uri, "OBSERVED_BY", perf_uri))

        for experiment in experiments:
            experiment_id = experiment.get("experiment_id")
            if not isinstance(experiment_id, str) or not experiment_id:
                raise ContentLineageError("experiment identity missing")
            experiment_uri = f"motion://experiment/{experiment_id}"
            causal_allowed = bool(experiment.get("causal_claim_allowed", False))
            status = experiment.get("status")
            if causal_allowed and status != "COMPLETED":
                raise ContentLineageError("causal claim cannot be allowed before completed experiment")
            supporting = tuple(str(x) for x in experiment.get("supporting_content_ids", ()))
            if content_id not in supporting:
                raise ContentLineageError("experiment does not support this content_id")
            add_node(LineageNode.create(experiment_uri, "Experiment", {
                "status": status,
                "manipulated_variable": experiment.get("manipulated_variable"),
                "primary_metric": experiment.get("primary_metric"),
                "effect_estimate": experiment.get("effect_estimate"),
                "confidence": experiment.get("confidence"),
                "causal_claim_allowed": causal_allowed,
            }))
            add_edge(LineageEdge.create(content_uri, "IN_EXPERIMENT", experiment_uri))

        sorted_nodes = tuple(sorted(nodes.values()))
        sorted_edges = tuple(sorted(edges.values()))
        payload = {
            "content_id": content_id,
            "provenance_root": provenance_root,
            "replay_fingerprint": replay_fingerprint,
            "beat_ids": list(beat_ids),
            "nodes": [asdict(node) for node in sorted_nodes],
            "edges": [asdict(edge) for edge in sorted_edges],
        }
        digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
        return ContentLineageSnapshot(
            content_id=content_id,
            provenance_root=provenance_root,
            replay_fingerprint=replay_fingerprint,
            beat_ids=beat_ids,
            nodes=sorted_nodes,
            edges=sorted_edges,
            snapshot_hash=digest,
        )
