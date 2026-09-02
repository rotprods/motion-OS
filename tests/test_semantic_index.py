from __future__ import annotations

import math
from pathlib import Path

from src.semantic_index.clients import HttpResponse, QdrantClient
from src.semantic_index.core import RepoManifest, SemanticConfig, DeterministicJLProjector, chunk_repository, chunk_text
from src.semantic_index.engine import SemanticKnowledgePlane
from src.semantic_index.structural import load_structural_context


def _unit(index: int, dims: int = 1024) -> list[float]:
    vector = [0.0] * dims
    vector[index] = 1.0
    return vector


def test_projection_is_deterministic_normalized_and_20d() -> None:
    projector = DeterministicJLProjector(output_dims=20)
    source = [float((i % 11) - 5) for i in range(1024)]
    first = projector.project(source)
    second = projector.project(source)
    assert first == second
    assert len(first) == 20
    assert math.isclose(math.sqrt(sum(value * value for value in first)), 1.0, rel_tol=1e-9)
    assert DeterministicJLProjector(output_dims=20, seed="other").project(source) != first


def test_chunking_is_stable_preserves_provenance_and_redacts_secret() -> None:
    text = "# Header\n\n" + "alpha beta gamma\n" * 80 + "sk-abcdefghijklmnopqrstuvwx\n"
    kwargs = dict(repo_id="rotprods/example", commit="abc123", path="src/example.py", language="python", text=text, target_chars=300, max_chars=420, overlap_chars=60)
    first = chunk_text(**kwargs)
    second = chunk_text(**kwargs)
    assert first
    assert [chunk.point_id for chunk in first] == [chunk.point_id for chunk in second]
    assert all(chunk.start_line <= chunk.end_line for chunk in first)
    assert all(chunk.repo_id == "rotprods/example" for chunk in first)
    assert any("[REDACTED_SECRET]" in chunk.text for chunk in first)
    assert all("sk-abcdefghijklmnopqrstuvwx" not in chunk.text for chunk in first)


def test_repository_policy_indexes_root_files_and_skips_sensitive_binary_vendor(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello semantic world", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=secret", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"\x89PNG\x00more")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "noise.js").write_text("vendor", encoding="utf-8")
    chunks = chunk_repository(tmp_path, RepoManifest(repo_id="rotprods/test"))
    paths = {chunk.path for chunk in chunks}
    assert "README.md" in paths
    assert ".env" not in paths
    assert "image.png" not in paths
    assert "node_modules/noise.js" not in paths


class FakeHttp:
    def __init__(self, responses: list[HttpResponse]):
        self.responses = list(responses)
        self.calls: list[tuple[str, str, dict | None]] = []

    def request(self, method: str, path: str, payload: dict | None = None, *, allow_status=()):
        self.calls.append((method, path, payload))
        if not self.responses:
            raise AssertionError(f"unexpected request {method} {path}")
        return self.responses.pop(0)


def test_qdrant_collection_contract_creates_named_1024d_and_20d_vectors() -> None:
    config = SemanticConfig()
    fake = FakeHttp([
        HttpResponse(404, {}), HttpResponse(200, {"result": True}),
        HttpResponse(200, {"result": True}), HttpResponse(200, {"result": True}),
        HttpResponse(200, {"result": True}), HttpResponse(200, {"result": True}),
    ])
    client = QdrantClient(config, http=fake)
    result = client.ensure_collection()
    assert result["created"] is True
    assert fake.calls[1][2] == {"vectors": {"semantic": {"size": 1024, "distance": "Cosine"}, "cos20": {"size": 20, "distance": "Cosine"}}}


class FakeOllama:
    def __init__(self, vectors: list[list[float]] | None = None):
        self.vectors = vectors or []

    def health(self):
        return {"models": [{"name": "bge-m3:latest"}]}

    def embed(self, inputs):
        if self.vectors:
            out = self.vectors[: len(inputs)]
            self.vectors = self.vectors[len(inputs):]
            return out
        return [_unit(i % 10) for i, _ in enumerate(inputs)]


class FakeQdrant:
    def __init__(self):
        self.events: list[str] = []
        self.points: list[dict] = []
        self.query_results: list[dict] = []

    def ensure_collection(self):
        self.events.append("ensure")
        return {"created": False}

    def health(self):
        return {"result": {"collections": []}}

    def upsert(self, points):
        self.events.append("upsert")
        self.points.extend(points)
        return {"result": True}

    def delete_stale(self, repo_id, index_run):
        self.events.append("delete_stale")
        return {"result": True}

    def query(self, *args, **kwargs):
        return list(self.query_results)

    def scroll(self, **kwargs):
        return []

    def set_payload(self, point_id, payload):
        self.events.append("set_payload")
        return {"result": True}


def test_indexing_upserts_before_stale_cleanup_and_persists_provenance() -> None:
    config = SemanticConfig(batch_size=2)
    qdrant = FakeQdrant()
    plane = SemanticKnowledgePlane(config, ollama=FakeOllama(), qdrant=qdrant)
    chunks = chunk_text(repo_id="rotprods/ave", commit="deadbeef", path="README.md", language="markdown", text=("semantic graph\n" * 120), target_chars=220, max_chars=320, overlap_chars=40)
    report = plane.index_chunks(chunks, manifest=RepoManifest(repo_id="rotprods/ave"))
    assert report["upserted"] == len(chunks)
    assert qdrant.events[0] == "ensure"
    assert qdrant.events[-1] == "delete_stale"
    assert qdrant.events.index("upsert") < qdrant.events.index("delete_stale")
    payload = qdrant.points[0]["payload"]
    assert payload["repo"] == "rotprods/ave"
    assert payload["commit"] == "deadbeef"
    assert payload["cos_level_bindings"] == ["L8", "L9", "L10", "L11", "L12"]
    assert len(qdrant.points[0]["vector"]["semantic"]) == 1024
    assert len(qdrant.points[0]["vector"]["cos20"]) == 20


def test_search_uses_cos20_for_candidates_then_exact_semantic_rerank() -> None:
    query = _unit(0)
    weak = _unit(1)
    strong = query.copy()
    qdrant = FakeQdrant()
    qdrant.query_results = [
        {"id": "route-winner", "score": 0.99, "vector": {"semantic": weak}, "payload": {"path": "weak.py"}},
        {"id": "semantic-winner", "score": 0.70, "vector": {"semantic": strong}, "payload": {"path": "strong.py"}},
    ]
    plane = SemanticKnowledgePlane(SemanticConfig(), ollama=FakeOllama(vectors=[query]), qdrant=qdrant)
    hits = plane.search("find exact semantic match", limit=2)
    assert hits[0].point_id == "semantic-winner"
    assert hits[0].semantic_score > hits[1].semantic_score


class MissingModelOllama(FakeOllama):
    def health(self):
        return {"models": [{"name": "other-model:latest"}]}


def test_doctor_fails_closed_when_embedding_model_is_missing() -> None:
    plane = SemanticKnowledgePlane(SemanticConfig(), ollama=MissingModelOllama(), qdrant=FakeQdrant())
    report = plane.doctor()
    assert report["ollama"]["service_ok"] is True
    assert report["ollama"]["model_present"] is False
    assert report["ollama"]["ok"] is False
    assert report["ok"] is False


def test_existing_ave_graph_is_reused_as_structural_metadata(tmp_path: Path) -> None:
    graph_dir = tmp_path / "GRAPH"
    graph_dir.mkdir()
    (graph_dir / "graph.json").write_text('{"nodes":[{"id":"src/a.js","file":"src/a.js","type":"src","deps":["src/b.js"],"dependents":["src/c.js"]}]}', encoding="utf-8")
    (graph_dir / "communities.json").write_text('{"communities":[{"id":7,"label":"render","topDir":"src","members":["src/a.js"]}]}', encoding="utf-8")
    context = load_structural_context(tmp_path)
    assert context["src/a.js"]["source"] == "GRAPH/graph.json"
    assert context["src/a.js"]["dependencies"] == ["src/b.js"]
    assert context["src/a.js"]["dependents"] == ["src/c.js"]
    assert context["src/a.js"]["community"]["label"] == "render"
