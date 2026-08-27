from src.coordination.content_lineage import Phase06ContentLineageBridge
from src.coordination.events import CoordinationEvent, ProvenanceRef
from src.coordination.projection import CoordinationGraphProjector
from src.coordination.unified_graph import UnifiedMotionGraphCompiler


def lineage():
    manifest = {
        "content_id": "CNT_001",
        "core_thesis": "systems compound",
        "hook": "Build systems, not tool lists.",
        "viral_driver": "MONEY",
        "provenance_chain": {"root": "PRV_abc"},
        "integrity": {"replay_fingerprint": "MNF_xyz", "sealed_fields": ["provenance_chain"]},
        "semantic_beats": [
            {"id": "B01_HOOK", "function": "hook", "text": "Build systems."},
            {"id": "B02_PAYOFF", "function": "payoff", "text": "They compound."},
        ],
    }
    handoff = {
        "content_id": "CNT_001",
        "provenance_root": "PRV_abc",
        "replay_fingerprint": "MNF_xyz",
        "semantic_beat_ids": ["B01_HOOK", "B02_PAYOFF"],
    }
    return Phase06ContentLineageBridge().compile(manifest=manifest, handoff=handoff)


def coordination():
    event = CoordinationEvent(
        event_type="CONTENT_LINEAGE_PROJECTED",
        aggregate_type="content",
        aggregate_id="motion://content/CNT_001",
        aggregate_revision=1,
        expected_revision=0,
        project_id="motion://project/MOTION.OS",
        agent_id="motion://agent/content-avatar",
        session_id="motion://session/content-avatar",
        workstream_id="motion://workstream/phase06-content",
        correlation_id="motion://work/CNT_001",
        idempotency_key="project:CNT_001:1",
        resource_scope=("contract:avatar-handoff",),
        payload={"content_id": "CNT_001"},
        provenance=(ProvenanceRef("phase06", "sealed-manifest:CNT_001"),),
    )
    return CoordinationGraphProjector().build([event], projection_version=1)


def test_agentic_and_content_lineage_share_same_content_identity_in_one_graph():
    unified = UnifiedMotionGraphCompiler().compile(
        coordination=coordination(),
        content_lineages=(lineage(),),
        graph_version=1,
    )
    assert unified.verify_hash()
    content_nodes = [node for node in unified.nodes if node.node_id == "motion://content/CNT_001"]
    assert len(content_nodes) == 1
    relations = {(edge.source, edge.relation, edge.target) for edge in unified.edges}
    assert any(target == "motion://content/CNT_001" and relation == "AFFECTS" for _, relation, target in relations)
    assert ("motion://content/CNT_001", "HAS_BEAT", "motion://content/CNT_001/beat/B01_HOOK") in relations


def test_same_sources_rebuild_same_unified_graph_hash():
    compiler = UnifiedMotionGraphCompiler()
    a = compiler.compile(coordination=coordination(), content_lineages=(lineage(),))
    b = compiler.compile(coordination=coordination(), content_lineages=(lineage(),))
    assert a.graph_hash == b.graph_hash
