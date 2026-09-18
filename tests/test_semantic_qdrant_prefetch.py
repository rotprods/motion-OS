from __future__ import annotations

from src.semantic_index.clients import HttpResponse, QdrantClient
from src.semantic_index.core import SemanticConfig


class FakeHttp:
    def __init__(self):
        self.calls: list[tuple[str, str, dict | None]] = []

    def request(self, method: str, path: str, payload: dict | None = None, *, allow_status=()):
        self.calls.append((method, path, payload))
        return HttpResponse(
            200,
            {
                "result": [
                    {"points": [{"id": "neighbor-a", "score": 0.91, "payload": {"repo": "rotprods/ave"}}]},
                    {"points": [{"id": "neighbor-b", "score": 0.88, "payload": {"repo": "rotprods/motion-OS"}}]},
                ]
            },
        )


def test_prefetch_rerank_batch_routes_cos20_then_semantic_by_point_id() -> None:
    fake = FakeHttp()
    client = QdrantClient(SemanticConfig(qdrant_collection="test_collection"), http=fake)
    result = client.query_prefetch_rerank_by_ids_batch(
        ["source-a", "source-b"],
        candidate_limit=64,
        limit=9,
        repo_ids=["rotprods/ave", "rotprods/motion-OS"],
        score_threshold=0.15,
    )

    assert [batch[0]["id"] for batch in result] == ["neighbor-a", "neighbor-b"]
    method, path, payload = fake.calls[-1]
    assert method == "POST"
    assert path == "/collections/test_collection/points/query/batch"
    assert payload is not None
    searches = payload["searches"]
    assert len(searches) == 2
    first = searches[0]
    assert first["prefetch"]["query"] == "source-a"
    assert first["prefetch"]["using"] == "cos20"
    assert first["prefetch"]["limit"] == 64
    assert first["query"] == "source-a"
    assert first["using"] == "semantic"
    assert first["limit"] == 9
    assert first["score_threshold"] == 0.15
    assert first["with_vector"] is False
    assert first["filter"] == first["prefetch"]["filter"]


def test_prefetch_rerank_rejects_candidate_window_smaller_than_final_limit() -> None:
    client = QdrantClient(SemanticConfig(), http=FakeHttp())
    try:
        client.query_prefetch_rerank_by_ids_batch(["source"], candidate_limit=2, limit=3)
    except ValueError as exc:
        assert "candidate_limit" in str(exc)
    else:
        raise AssertionError("expected candidate window contract to fail closed")
