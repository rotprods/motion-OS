from __future__ import annotations

from src.semantic_index.core import SemanticConfig
from src.semantic_index.engine import SemanticKnowledgePlane


class FakeOllama:
    def health(self):
        return {"models": [{"name": "bge-m3:latest"}]}

    def embed(self, inputs):
        return [[1.0] + [0.0] * 1023 for _ in inputs]


class FakeQdrant:
    def __init__(self):
        self.events: list[str] = []
        self.payloads: list[dict] = []
        self.scroll_kwargs: dict | None = None
        self.prefetch_kwargs: dict | None = None

    def ensure_collection(self):
        return {"created": False}

    def scroll(self, **kwargs):
        self.scroll_kwargs = kwargs
        return [{"id": "source", "payload": {"repo": "rotprods/ave", "path": "a.js"}}]

    def query_prefetch_rerank_by_ids_batch(self, point_ids, **kwargs):
        self.events.append("query_prefetch_rerank_by_ids_batch")
        self.prefetch_kwargs = {"point_ids": list(point_ids), **kwargs}
        return [[
            {"id": "source", "score": 1.0, "payload": {"repo": "rotprods/ave", "path": "a.js"}},
            {"id": "neighbor", "score": 0.8, "payload": {"repo": "rotprods/motion-OS", "path": "b.py", "start_line": 1, "end_line": 4}},
        ] for _ in point_ids]

    def set_payload_batch(self, updates):
        self.events.append("set_payload_batch")
        self.payloads.extend(payload for _, payload in updates)
        return {"result": True}


def test_graphify_uses_qdrant_point_id_prefetch_rerank_without_vector_transfer() -> None:
    qdrant = FakeQdrant()
    plane = SemanticKnowledgePlane(SemanticConfig(), ollama=FakeOllama(), qdrant=qdrant)
    report = plane.graphify(neighbors=1, query_batch_size=32)
    assert report["graphify_version"] == "graphify-v4-qdrant-prefetch-rerank"
    assert report["query_batches"] == 1
    assert report["write_batches"] == 1
    assert report["cross_repo_edges"] == 1
    assert report["vector_payload_transfer"] == "none"
    assert qdrant.events == ["query_prefetch_rerank_by_ids_batch", "set_payload_batch"]
    assert qdrant.scroll_kwargs is not None and qdrant.scroll_kwargs["with_vectors"] is False
    assert qdrant.prefetch_kwargs is not None
    assert qdrant.prefetch_kwargs["point_ids"] == ["source"]
    assert qdrant.prefetch_kwargs["candidate_limit"] >= qdrant.prefetch_kwargs["limit"]
    edge = qdrant.payloads[0]["graph_neighbors"][0]
    assert edge["edge_type"] == "semantic_neighbor"
    assert edge["semantic_score"] == 0.8
    assert "route_score" not in edge
