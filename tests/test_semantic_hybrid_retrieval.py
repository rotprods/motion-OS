from __future__ import annotations

from src.semantic_index.core import SemanticConfig
from src.semantic_index.engine import SemanticKnowledgePlane


def _unit(index: int, dims: int = 1024) -> list[float]:
    vector = [0.0] * dims
    vector[index] = 1.0
    return vector


class FakeOllama:
    def __init__(self, vector: list[float]):
        self.vector = vector

    def embed(self, inputs):
        return [self.vector for _ in inputs]


class SplitCandidateQdrant:
    def __init__(self, *, route_results: list[dict], semantic_results: list[dict]):
        self.route_results = route_results
        self.semantic_results = semantic_results
        self.calls: list[tuple[str, int]] = []

    def query(self, vector, *, using, limit, repo_ids=None, with_vectors=False):
        self.calls.append((using, limit))
        if using == "cos20":
            return list(self.route_results)
        if using == "semantic":
            return list(self.semantic_results)
        raise AssertionError(f"unexpected vector space {using!r}")


def _point(point_id: str, *, score: float, semantic: list[float], path: str) -> dict:
    return {
        "id": point_id,
        "score": score,
        "vector": {"semantic": semantic},
        "payload": {"repo": "rotprods/motion-OS", "path": path},
    }


def test_native_semantic_candidate_cannot_be_lost_by_cos20_route_projection():
    query = _unit(0)
    route_only = _point("route-only", score=0.99, semantic=_unit(1), path="docs/noise.md")
    semantic_winner = _point("semantic-winner", score=1.0, semantic=query, path="src/extraction/visual.py")
    qdrant = SplitCandidateQdrant(route_results=[route_only], semantic_results=[semantic_winner])

    plane = SemanticKnowledgePlane(
        SemanticConfig(route_multiplier=2),
        ollama=FakeOllama(query),
        qdrant=qdrant,
    )
    hits = plane.search("find the implementation", limit=1)

    assert hits[0].point_id == "semantic-winner"
    assert hits[0].semantic_score == 1.0
    assert [using for using, _ in qdrant.calls] == ["cos20", "semantic"]


def test_duplicate_candidate_keeps_real_cos20_route_score_as_tiebreaker():
    query = _unit(0)
    route_duplicate = _point("same", score=0.73, semantic=query, path="src/a.py")
    semantic_duplicate = _point("same", score=1.0, semantic=query, path="src/a.py")
    qdrant = SplitCandidateQdrant(route_results=[route_duplicate], semantic_results=[semantic_duplicate])

    plane = SemanticKnowledgePlane(SemanticConfig(), ollama=FakeOllama(query), qdrant=qdrant)
    hit = plane.search("same concept", limit=1)[0]

    assert hit.point_id == "same"
    assert hit.semantic_score == 1.0
    assert hit.route_score == 0.73


def test_semantic_only_candidate_has_neutral_route_tiebreaker_not_fake_semantic_score():
    query = _unit(0)
    semantic_only = _point("semantic-only", score=0.94, semantic=query, path="schemas/example.json")
    qdrant = SplitCandidateQdrant(route_results=[], semantic_results=[semantic_only])

    plane = SemanticKnowledgePlane(SemanticConfig(), ollama=FakeOllama(query), qdrant=qdrant)
    hit = plane.search("schema contract", limit=1)[0]

    assert hit.semantic_score == 1.0
    assert hit.route_score == 0.0
