from __future__ import annotations

from src.semantic_index.core import SemanticConfig
from src.semantic_index.engine import SemanticKnowledgePlane


def _unit(index: int, dims: int = 1024) -> list[float]:
    vector = [0.0] * dims
    vector[index] = 1.0
    return vector


class FakeOllama:
    def health(self):
        return {"models": [{"name": "bge-m3:latest"}]}

    def embed(self, inputs):
        return [_unit(0) for _ in inputs]


class FakeQdrant:
    def __init__(self):
        self.events: list[str] = []
        self.payloads: list[dict] = []
        self.source = _unit(0)

    def ensure_collection(self):
        return {"created": False}

    def scroll(self, **kwargs):
        return [{"id": "source", "vector": {"semantic": self.source, "cos20": [1.0] + [0.0] * 19}, "payload": {"repo": "rotprods/ave", "path": "a.js"}}]

    def query_batch(self, vectors, *args, **kwargs):
        self.events.append("query_batch")
        return [[{"id": "neighbor", "score": 0.8, "vector": {"semantic": self.source}, "payload": {"repo": "rotprods/motion-OS", "path": "b.py", "start_line": 1, "end_line": 4}}] for _ in vectors]

    def set_payload_batch(self, updates):
        self.events.append("set_payload_batch")
        self.payloads.extend(payload for _, payload in updates)
        return {"result": True}


def test_graphify_batches_qdrant_reads_and_writes_and_labels_semantic_edges() -> None:
    qdrant = FakeQdrant()
    plane = SemanticKnowledgePlane(SemanticConfig(), ollama=FakeOllama(), qdrant=qdrant)
    report = plane.graphify(neighbors=1, query_batch_size=32)
    assert report["graphify_version"] == "graphify-v3-batched-io"
    assert report["query_batches"] == 1
    assert report["write_batches"] == 1
    assert report["cross_repo_edges"] == 1
    assert qdrant.events == ["query_batch", "set_payload_batch"]
    assert qdrant.payloads[0]["graph_neighbors"][0]["edge_type"] == "semantic_neighbor"
