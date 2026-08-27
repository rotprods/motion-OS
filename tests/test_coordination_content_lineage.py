from copy import deepcopy

import pytest

from src.coordination.content_lineage import ContentLineageError, Phase06ContentLineageBridge


def manifest():
    return {
        "content_id": "CNT_001",
        "core_thesis": "Systems beat tool lists.",
        "hook": "This changes how creators build.",
        "viral_driver": "MONEY",
        "provenance_chain": {"root": "PRV_abc123"},
        "integrity": {"replay_fingerprint": "MNF_def456", "sealed_fields": ["provenance_chain"]},
        "semantic_beats": [
            {"id": "B01_HOOK", "function": "hook", "text": "This changes how creators build."},
            {"id": "B02_PROOF", "function": "proof", "text": "Here is the system."},
            {"id": "B03_PAYOFF", "function": "payoff", "text": "Now the workflow compounds."},
        ],
    }


def handoff():
    return {
        "content_id": "CNT_001",
        "provenance_root": "PRV_abc123",
        "replay_fingerprint": "MNF_def456",
        "semantic_beat_ids": ["B01_HOOK", "B02_PROOF", "B03_PAYOFF"],
        "render_job_id": "job-1",
    }


def opportunity():
    return {
        "opportunity_id": "OPP_001",
        "signal_id": "SIG_001",
        "account_id": "rot.prods",
        "goal": "REACH",
        "audience_id": "ai-creators",
        "score": 87.5,
        "decision": "PRODUCE",
    }


def publications():
    return [{
        "publication_id": "PUB_001",
        "content_id": "CNT_001",
        "platform": "instagram",
        "account_id": "rot.prods",
        "published_at": "2026-08-27T10:00:00Z",
        "master_hash": "a" * 64,
    }]


def performance():
    return [{
        "metric_snapshot_id": "MET_001",
        "content_id": "CNT_001",
        "platform": "instagram",
        "views": 100000,
        "completion_rate": 0.42,
        "shares": 1800,
        "saves": 900,
        "cta_conversions": 40,
        "causal_status": "OBSERVED_CORRELATION",
    }]


def experiments():
    return [{
        "experiment_id": "EXP_001",
        "hypothesis": "proof-first improves completion",
        "primary_metric": "completion_rate",
        "manipulated_variable": "PROOF_ORDER",
        "status": "COMPLETED",
        "supporting_content_ids": ["CNT_001"],
        "effect_estimate": 0.08,
        "confidence": 0.91,
        "causal_claim_allowed": True,
    }]


def test_full_content_to_publication_performance_experiment_lineage_is_deterministic():
    bridge = Phase06ContentLineageBridge()
    first = bridge.compile(
        manifest=manifest(),
        handoff=handoff(),
        opportunity=opportunity(),
        publications=publications(),
        performance_records=performance(),
        experiments=experiments(),
    )
    second = bridge.compile(
        manifest=manifest(),
        handoff=handoff(),
        opportunity=opportunity(),
        publications=publications(),
        performance_records=performance(),
        experiments=experiments(),
    )
    assert first.snapshot_hash == second.snapshot_hash
    assert first.verify_hash()
    relations = {(edge.source, edge.relation, edge.target) for edge in first.edges}
    content = "motion://content/CNT_001"
    assert ("motion://opportunity/OPP_001", "PRODUCED_CONTENT", content) in relations
    assert (content, "AUTHORIZED_HANDOFF", "motion://content/CNT_001/studio-handoff/MNF_def456") in relations
    assert (content, "PUBLISHED_AS", "motion://publication/PUB_001") in relations
    assert (content, "OBSERVED_BY", "motion://metric/MET_001") in relations
    assert (content, "IN_EXPERIMENT", "motion://experiment/EXP_001") in relations


@pytest.mark.parametrize("field,value", [
    ("provenance_root", "PRV_tampered"),
    ("replay_fingerprint", "MNF_tampered"),
    ("semantic_beat_ids", ["B01_HOOK", "B03_PAYOFF", "B02_PROOF"]),
])
def test_handoff_identity_tampering_is_rejected(field, value):
    altered = handoff()
    altered[field] = value
    with pytest.raises(ContentLineageError):
        Phase06ContentLineageBridge().compile(manifest=manifest(), handoff=altered)


def test_performance_remains_observational_without_controlled_experiment():
    snapshot = Phase06ContentLineageBridge().compile(
        manifest=manifest(),
        handoff=handoff(),
        performance_records=performance(),
    )
    metric = next(node for node in snapshot.nodes if node.node_type == "PerformanceSnapshot")
    assert '"causal_status":"OBSERVED_CORRELATION"' in metric.properties_json


def test_causal_claim_before_experiment_completion_fails_closed():
    exp = deepcopy(experiments()[0])
    exp["status"] = "RUNNING"
    with pytest.raises(ContentLineageError, match="before completed experiment"):
        Phase06ContentLineageBridge().compile(
            manifest=manifest(),
            handoff=handoff(),
            experiments=[exp],
        )


def test_cross_content_performance_or_publication_is_rejected():
    wrong_perf = deepcopy(performance()[0])
    wrong_perf["content_id"] = "CNT_OTHER"
    with pytest.raises(ContentLineageError, match="performance content_id mismatch"):
        Phase06ContentLineageBridge().compile(
            manifest=manifest(), handoff=handoff(), performance_records=[wrong_perf]
        )
