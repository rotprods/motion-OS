from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .clients import OllamaClient, QdrantClient, SemanticServiceError
from .core import (
    COS_LEVELS,
    Chunk,
    DeterministicJLProjector,
    RepoManifest,
    SearchHit,
    SemanticConfig,
    batched,
    chunk_repository,
    cosine,
    l2_normalize,
)


class SemanticKnowledgePlane:
    """Rebuildable knowledge plane. Git remains authority; Qdrant is a derived projection."""

    def __init__(self, config: SemanticConfig | None = None, *, ollama: OllamaClient | None = None, qdrant: QdrantClient | None = None, projector: DeterministicJLProjector | None = None):
        self.config = config or SemanticConfig.from_env()
        self.ollama = ollama or OllamaClient(self.config)
        self.qdrant = qdrant or QdrantClient(self.config)
        self.projector = projector or DeterministicJLProjector(output_dims=self.config.cos_dims)

    def doctor(self) -> dict[str, Any]:
        report: dict[str, Any] = {
            "ollama": {"ok": False, "url": self.config.ollama_url, "model": self.config.ollama_model},
            "qdrant": {"ok": False, "url": self.config.qdrant_url, "collection": self.config.qdrant_collection},
            "contract": {"semantic_dims": self.config.semantic_dims, "cos_route_dims": self.config.cos_dims, "cos_levels": list(COS_LEVELS)},
        }
        try:
            tags = self.ollama.health()
            models = tags.get("models", []) if isinstance(tags, dict) else []
            names = {str(model.get("name") or model.get("model")) for model in models if isinstance(model, dict)}
            base = self.config.ollama_model.split(":", 1)[0]
            model_present = any(name.split(":", 1)[0] == base for name in names if name)
            report["ollama"].update({"ok": True, "model_present": model_present, "models": sorted(names)})
        except SemanticServiceError as exc:
            report["ollama"]["error"] = str(exc)
        try:
            self.qdrant.health()
            collection = self.qdrant.ensure_collection()
            report["qdrant"].update({"ok": True, "collection_state": collection})
        except SemanticServiceError as exc:
            report["qdrant"]["error"] = str(exc)
        report["ok"] = bool(report["ollama"]["ok"] and report["qdrant"]["ok"])
        return report

    def index_repository(self, root: Path) -> dict[str, Any]:
        root = root.resolve()
        manifest = RepoManifest.load(root)
        chunks = chunk_repository(root, manifest)
        return self.index_chunks(chunks, manifest=manifest)

    def index_chunks(self, chunks: Sequence[Chunk], *, manifest: RepoManifest | None = None) -> dict[str, Any]:
        if not chunks:
            return {"repo": manifest.repo_id if manifest else None, "chunks": 0, "upserted": 0}
        repo_ids = {chunk.repo_id for chunk in chunks}
        if len(repo_ids) != 1:
            raise ValueError("index_chunks requires exactly one repository per transaction")
        repo_id = next(iter(repo_ids))
        run_id = str(uuid.uuid4())
        indexed_at = datetime.now(timezone.utc).isoformat()
        self.qdrant.ensure_collection()
        upserted = 0
        for batch in batched(list(chunks), self.config.batch_size):
            embeddings = self.ollama.embed([chunk.embedding_text() for chunk in batch])
            points: list[dict[str, Any]] = []
            for chunk, embedding in zip(batch, embeddings):
                semantic = l2_normalize(embedding)
                cos20 = self.projector.project(semantic)
                payload: dict[str, Any] = {
                    "repo": chunk.repo_id,
                    "commit": chunk.commit,
                    "path": chunk.path,
                    "language": chunk.language,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "source_sha256": chunk.source_sha256,
                    "chunk_sha256": chunk.chunk_sha256,
                    "embedding_model": self.config.ollama_model,
                    "semantic_dims": self.config.semantic_dims,
                    "cos_route_dims": self.config.cos_dims,
                    "projection_version": self.projector.seed,
                    "index_run": run_id,
                    "indexed_at": indexed_at,
                    "cos_level_bindings": ["L8", "L9", "L10", "L11", "L12"],
                }
                if manifest is None or manifest.store_text:
                    payload["text"] = chunk.text
                points.append({"id": chunk.point_id, "vector": {"semantic": semantic, "cos20": cos20}, "payload": payload})
            self.qdrant.upsert(points)
            upserted += len(points)
        self.qdrant.delete_stale(repo_id, run_id)
        return {
            "repo": repo_id,
            "commit": chunks[0].commit,
            "index_run": run_id,
            "chunks": len(chunks),
            "upserted": upserted,
            "collection": self.config.qdrant_collection,
            "semantic_dims": self.config.semantic_dims,
            "cos_route_dims": self.config.cos_dims,
            "embedding_model": self.config.ollama_model,
        }

    @staticmethod
    def _extract_named_vector(point: dict[str, Any], name: str) -> list[float] | None:
        vectors = point.get("vector") or point.get("vectors")
        if isinstance(vectors, dict):
            vector = vectors.get(name)
            if isinstance(vector, list):
                return [float(value) for value in vector]
        return None

    def search(self, query: str, *, limit: int = 10, repo_ids: Sequence[str] | None = None, route_multiplier: int | None = None) -> list[SearchHit]:
        if not query.strip():
            raise ValueError("query must not be empty")
        query_semantic = l2_normalize(self.ollama.embed([query])[0])
        query_route = self.projector.project(query_semantic)
        multiplier = route_multiplier or self.config.route_multiplier
        candidates = self.qdrant.query(query_route, using="cos20", limit=max(limit * multiplier, 32), repo_ids=repo_ids, with_vectors=["semantic"])
        hits: list[SearchHit] = []
        for candidate in candidates:
            semantic = self._extract_named_vector(candidate, "semantic")
            route_score = float(candidate.get("score", 0.0))
            semantic_score = cosine(query_semantic, semantic) if semantic is not None else route_score
            hits.append(SearchHit(point_id=str(candidate.get("id")), semantic_score=semantic_score, route_score=route_score, payload=dict(candidate.get("payload") or {})))
        hits.sort(key=lambda hit: (hit.semantic_score, hit.route_score), reverse=True)
        return hits[:limit]

    def graphify(self, *, repo_ids: Sequence[str] | None = None, neighbors: int = 8, min_semantic_score: float = 0.15) -> dict[str, Any]:
        if neighbors < 1:
            raise ValueError("neighbors must be >= 1")
        self.qdrant.ensure_collection()
        points = self.qdrant.scroll(repo_ids=repo_ids, with_vectors=["semantic", "cos20"], page_size=128)
        updated = edge_count = cross_repo_edges = 0
        for point in points:
            point_id = point.get("id")
            semantic = self._extract_named_vector(point, "semantic")
            route = self._extract_named_vector(point, "cos20")
            if semantic is None or route is None:
                continue
            payload = dict(point.get("payload") or {})
            candidates = self.qdrant.query(route, using="cos20", limit=max(neighbors * self.config.route_multiplier, 32), repo_ids=repo_ids, with_vectors=["semantic"])
            ranked: list[dict[str, Any]] = []
            for candidate in candidates:
                if str(candidate.get("id")) == str(point_id):
                    continue
                candidate_semantic = self._extract_named_vector(candidate, "semantic")
                if candidate_semantic is None:
                    continue
                score = cosine(semantic, candidate_semantic)
                if score < min_semantic_score:
                    continue
                candidate_payload = dict(candidate.get("payload") or {})
                ranked.append({"id": str(candidate.get("id")), "semantic_score": round(score, 8), "route_score": round(float(candidate.get("score", 0.0)), 8), "repo": candidate_payload.get("repo"), "path": candidate_payload.get("path"), "start_line": candidate_payload.get("start_line"), "end_line": candidate_payload.get("end_line")})
            ranked.sort(key=lambda item: (item["semantic_score"], item["route_score"]), reverse=True)
            ranked = ranked[:neighbors]
            edge_count += len(ranked)
            cross_repo_edges += sum(1 for item in ranked if item.get("repo") != payload.get("repo"))
            self.qdrant.set_payload(point_id, {"graph_neighbors": ranked, "graphify_version": "graphify-v1", "graphified_at": datetime.now(timezone.utc).isoformat(), "cos_level_bindings": ["L8", "L9", "L10", "L11", "L12"]})
            updated += 1
        return {
            "graphify_version": "graphify-v1",
            "collection": self.config.qdrant_collection,
            "nodes_seen": len(points),
            "nodes_updated": updated,
            "edges": edge_count,
            "cross_repo_edges": cross_repo_edges,
            "neighbors_per_node": neighbors,
            "cos_active_levels": {
                "L8": "Knowledge Graph: chunk identity + provenance",
                "L9": "Semantic Graph: semantic-neighbor relations",
                "L10": "Embedding Graph: bge-m3 1024D + cos20 route vector",
                "L11": "GraphRAG: route -> native rerank -> provenance",
                "L12": "Memory Graph: rebuildable Qdrant projection; Git remains authority",
            },
        }

    def cos_graph_engine(self, query: str, *, limit: int = 10, repo_ids: Sequence[str] | None = None) -> dict[str, Any]:
        hits = self.search(query, limit=limit, repo_ids=repo_ids)
        return {
            "query": query,
            "collection": self.config.qdrant_collection,
            "pipeline": ["Ollama bge-m3 1024D embedding", "deterministic cos20 routing projection", "Qdrant cos20 candidate retrieval", "exact 1024D cosine rerank", "provenance-preserving GraphRAG result"],
            "cos_20_levels": list(COS_LEVELS),
            "active_retrieval_levels": ["L8", "L9", "L10", "L11", "L12"],
            "hits": [asdict(hit) for hit in hits],
        }
