from src.assets.fitness import AssetFitness, evaluate_asset_candidate
from src.graph.editing_graph import TypedEditingGraph
from src.graph.model import Edge
from src.knowledge.memory_store import connect_memory_store, upsert_memory
from src.providers.contracts import ProviderCandidate
from src.rag.hybrid import RetrievalQuery, hybrid_retrieve


def test_hybrid_retrieval_applies_hard_filters_and_explains_ranking():
    conn = connect_memory_store()
    graph = TypedEditingGraph('rag_g', 'project_rag')
    graph.add_node(graph.typed_node('brief', 'Brief'))
    graph.add_node(graph.typed_node('style_close', 'StyleSignature'))
    graph.add_node(graph.typed_node('style_far', 'StyleSignature'))
    graph.add_edge(Edge('brief', 'style_close', 'DRIVES', {'id': 'g1'}))

    upsert_memory(
        conn,
        memory_id='close', memory_plane='style', node_id='style_close', payload={'name': 'close'},
        vector=[1.0, 0.0], semantic_score=.85, style_score=.9, motion_score=.8,
        composition_score=.8, brand_score=.9, historical_qa=.9, user_approval=.8,
        license_ok=True, asset_type='reference', aspect_ratio='16:9', renderer_support=['remotion'],
    )
    upsert_memory(
        conn,
        memory_id='far', memory_plane='style', node_id='style_far', payload={'name': 'far'},
        vector=[0.7, 0.3], semantic_score=.8, style_score=.84, motion_score=.8,
        composition_score=.8, brand_score=.8, historical_qa=.8, user_approval=.8,
        license_ok=True, asset_type='reference', aspect_ratio='16:9', renderer_support=['remotion'],
    )
    upsert_memory(
        conn,
        memory_id='unlicensed', memory_plane='reference', payload={'name': 'blocked'},
        vector=[1.0, 0.0], semantic_score=1, style_score=1, motion_score=1,
        composition_score=1, brand_score=1, historical_qa=1, user_approval=1,
        license_ok=False, asset_type='reference', aspect_ratio='16:9', renderer_support=['remotion'],
    )

    results = hybrid_retrieve(
        conn,
        RetrievalQuery(
            vector=(1.0, 0.0), renderer='remotion', asset_type='reference', aspect_ratio='16:9',
            graph_anchor_ids=('brief',),
        ),
        graph=graph,
        limit=5,
    )
    assert [result.memory_id for result in results] == ['close', 'far']
    assert results[0].graph_proximity > results[1].graph_proximity
    assert any(item.startswith('weighted_controlled=') for item in results[0].explanation)


def test_pinterest_defaults_to_reference_not_final_asset():
    candidate = ProviderCandidate(
        asset_id='pin_1', provider='pinterest', source_ref='https://example.invalid/pin',
        asset_type='reference', usage_class='reference_only', license_state='unknown',
        provenance={'discovered_at': '2026-08-26T00:00:00Z', 'discovery_method': 'provider_search'},
    )
    decision = evaluate_asset_candidate(candidate, AssetFitness(.95, .95, .8, 0, .9, .8))
    assert decision.status == 'approved_reference'
    assert 'reference_only_policy' in decision.reasons


def test_unverified_commercial_candidate_is_quarantined():
    candidate = ProviderCandidate(
        asset_id='pexels_1', provider='pexels', source_ref='https://example.invalid/stock',
        asset_type='video', usage_class='commercial_candidate', license_state='needs_review',
        provenance={'discovered_at': '2026-08-26T00:00:00Z', 'discovery_method': 'provider_search'},
        sha256='a' * 64,
    )
    decision = evaluate_asset_candidate(candidate, AssetFitness(.95, .9, .95, .4, 1, 1))
    assert decision.status == 'quarantined'
    assert 'license_not_verified' in decision.reasons


def test_owned_local_asset_with_provenance_and_hash_can_promote():
    candidate = ProviderCandidate(
        asset_id='owned_1', provider='local', source_ref='local://owned.png', asset_type='image',
        usage_class='owned', license_state='owned',
        provenance={'discovered_at': '2026-08-26T00:00:00Z', 'discovery_method': 'local_import'},
        sha256='b' * 64,
    )
    decision = evaluate_asset_candidate(candidate, AssetFitness(.95, .95, .95, 1, 1, .95))
    assert decision.status == 'approved_asset'
    assert decision.reasons == ()
