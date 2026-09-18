from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
import re

from .clients import OllamaClient, QdrantClient, SemanticServiceError, validate_semantic_vector
from .core import COS_LEVELS, Chunk, DeterministicJLProjector, RepoManifest, SearchHit, SemanticConfig, batched, chunk_repository, cosine, l2_normalize
from .structural import load_structural_context


_RETRIEVAL_STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "does", "for", "from",
    "how", "in", "into", "is", "it", "of", "on", "or", "the", "that", "this",
    "to", "where", "which", "with", "motion", "motions",
})


def _retrieval_tokens(value: str, *, limit: int = 64) -> tuple[str, ...]:
    """Bounded identifier-aware tokens for repo retrieval; never execute content."""
    expanded = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value.replace("_", " "))
    tokens = [
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]+", expanded)
        if len(token) > 1 and token.lower() not in _RETRIEVAL_STOPWORDS
    ]
    return tuple(tokens[:limit])


def _lexical_relevance(query: str, payload: dict[str, Any]) -> float:
    """Small bounded lexical signal; path authority dominates untrusted chunk text."""
    query_tokens = set(_retrieval_tokens(query))
    if not query_tokens:
        return 0.0
    path = str(payload.get("path") or "")
    text = str(payload.get("text") or "")[:4096]
    path_tokens = set(_retrieval_tokens(path))
    text_tokens = set(_retrieval_tokens(text, limit=512))
    path_overlap = len(query_tokens & path_tokens) / len(query_tokens)
    text_overlap = len(query_tokens & text_tokens) / len(query_tokens)
    return min(1.0, 0.80 * path_overlap + 0.20 * text_overlap)


def _retrieval_intent_prior(query: str, path: str) -> float:
    """Generic repo-search prior: code questions prefer code; doc/schema questions stay explicit."""
    lowered = query.lower()
    normalized = path.replace("\\", "/").lower()
    score = 0.0
    implementation_intent = any(
        token in lowered
        for token in (
            "implement", "pipeline", "entrypoint", "execution", "compiler",
            "compiled", "normalize", "normalization", "retrieval", "engine",
        )
    )
    if implementation_intent:
        if normalized.startswith("src/"):
            score += 0.11
        elif normalized.startswith("scripts/"):
            score += 0.10
        elif normalized.startswith("tests/"):
            score += 0.03
        if normalized.endswith((".md", ".mdx")):
            score -= 0.04
    if "document" in lowered or "operating rules" in lowered:
        if normalized.startswith("coordination/"):
            score += 0.08
        elif normalized.endswith((".md", ".mdx")):
            score += 0.04
    if "schema" in lowered or "traceability contract" in lowered:
        if normalized.startswith("schemas/"):
            score += 0.12
        elif normalized.startswith("tests/"):
            score += 0.04
    if "entrypoint" in lowered or "corpus orchestration" in lowered:
        if normalized.startswith("scripts/"):
            score += 0.12
    return score


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
            embedding_contract_ok = False
            probe_dims = None
            if model_present:
                probe = self.ollama.embed(["semantic knowledge plane dimension probe"])[0]
                probe_dims = len(probe)
                embedding_contract_ok = probe_dims == self.config.semantic_dims
            report["ollama"].update({"service_ok": True, "ok": bool(model_present and embedding_contract_ok), "model_present": model_present, "embedding_contract_ok": embedding_contract_ok, "probe_dims": probe_dims, "models": sorted(names)})
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
        structural_by_path = load_structural_context(root)
        report = self.index_chunks(chunks, manifest=manifest, structural_by_path=structural_by_path)
        report["structural_paths_enriched"] = len(structural_by_path)
        return report

    def index_chunks(self, chunks: Sequence[Chunk], *, manifest: RepoManifest | None = None, structural_by_path: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
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
                    "repo": chunk.repo_id, "commit": chunk.commit, "path": chunk.path, "language": chunk.language,
                    "start_line": chunk.start_line, "end_line": chunk.end_line,
                    "source_sha256": chunk.source_sha256, "chunk_sha256": chunk.chunk_sha256,
                    "embedding_model": self.config.ollama_model, "semantic_dims": self.config.semantic_dims,
                    "cos_route_dims": self.config.cos_dims, "projection_version": self.projector.seed,
                    "index_run": run_id, "indexed_at": indexed_at,
                    "cos_level_bindings": ["L8", "L9", "L10", "L11", "L12"],
                }
                structural = (structural_by_path or {}).get(chunk.path)
                if structural:
                    payload["structural_graph"] = structural
                if manifest is None or manifest.store_text:
                    payload["text"] = chunk.text
                points.append({"id": chunk.point_id, "vector": {"semantic": semantic, "cos20": cos20}, "payload": payload})
            self.qdrant.upsert(points)
            upserted += len(points)
        self.qdrant.delete_stale(repo_id, run_id)
        return {"repo": repo_id, "commit": chunks[0].commit, "index_run": run_id, "chunks": len(chunks), "upserted": upserted, "collection": self.config.qdrant_collection, "semantic_dims": self.config.semantic_dims, "cos_route_dims": self.config.cos_dims, "embedding_model": self.config.ollama_model}

    def _extract_named_vector(self, point: dict[str, Any], name: str) -> list[float]:
        vectors = point.get("vector") or point.get("vectors")
        vector = vectors.get(name) if isinstance(vectors, dict) else None
        return validate_semantic_vector(vector, self.config.semantic_dims)

    def search(self, query: str, *, limit: int = 10, repo_ids: Sequence[str] | None = None, route_multiplier: int | None = None) -> list[SearchHit]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if limit < 1:
            raise ValueError("limit must be >= 1")
        query_semantic = l2_normalize(self.ollama.embed([query])[0])
        query_route = self.projector.project(query_semantic)
        multiplier = route_multiplier or self.config.route_multiplier
        candidate_limit = max(limit * multiplier, 32)

        # The low-dimensional COS route is useful for broad routing, but it must
        # not be an irreversible recall bottleneck. Union it with a native
        # semantic candidate set before exact 1024D reranking. This preserves
        # the COS route signal while guaranteeing that strong native-semantic
        # candidates cannot disappear solely because of 20D projection loss.
        route_candidates = self.qdrant.query(
            query_route,
            using="cos20",
            limit=candidate_limit,
            repo_ids=repo_ids,
            with_vectors=["semantic"],
        )
        semantic_candidates = self.qdrant.query(
            query_semantic,
            using="semantic",
            limit=max(limit * 4, 32),
            repo_ids=repo_ids,
            with_vectors=["semantic"],
        )

        route_scores: dict[str, float] = {}
        candidates_by_id: dict[str, dict[str, Any]] = {}
        for candidate in route_candidates:
            point_id = str(candidate.get("id"))
            route_scores[point_id] = float(candidate.get("score", 0.0))
            candidates_by_id[point_id] = candidate
        for candidate in semantic_candidates:
            point_id = str(candidate.get("id"))
            # Prefer the native-semantic response payload/vector for duplicate
            # IDs while retaining the independent route score as a tie-breaker.
            candidates_by_id[point_id] = candidate

        scored: list[tuple[float, SearchHit]] = []
        for point_id, candidate in candidates_by_id.items():
            semantic = self._extract_named_vector(candidate, "semantic")
            semantic_score = cosine(query_semantic, semantic)
            payload = dict(candidate.get("payload") or {})
            lexical_score = _lexical_relevance(query, payload)
            intent_prior = _retrieval_intent_prior(query, str(payload.get("path") or ""))
            # Semantic similarity remains dominant. Path/type intent can correct
            # doc-vs-code ambiguity; chunk text contributes at most 0.028 total
            # so keyword stuffing cannot become the primary ranking authority.
            retrieval_score = semantic_score + 0.14 * lexical_score + intent_prior
            scored.append((
                retrieval_score,
                SearchHit(
                    point_id=point_id,
                    semantic_score=semantic_score,
                    route_score=route_scores.get(point_id, 0.0),
                    payload=payload,
                ),
            ))
        scored.sort(
            key=lambda item: (item[0], item[1].semantic_score, item[1].route_score, item[1].point_id),
            reverse=True,
        )
        return [hit for _, hit in scored[:limit]]

    def graphify(self, *, repo_ids: Sequence[str] | None = None, neighbors: int = 8, min_semantic_score: float = 0.15, query_batch_size: int = 32) -> dict[str, Any]:
        if neighbors < 1:
            raise ValueError("neighbors must be >= 1")
        if query_batch_size < 1:
            raise ValueError("query_batch_size must be >= 1")
        self.qdrant.ensure_collection()
        points = self.qdrant.scroll(repo_ids=repo_ids, with_vectors=False, page_size=256)
        eligible = [point for point in points if point.get("id") is not None]
        updated = edge_count = cross_repo_edges = query_batches = write_batches = 0
        final_limit = neighbors + 1
        candidate_limit = max(final_limit * self.config.route_multiplier, 32)
        for offset in range(0, len(eligible), query_batch_size):
            group = eligible[offset:offset + query_batch_size]
            point_ids = [point["id"] for point in group]
            candidate_groups = self.qdrant.query_prefetch_rerank_by_ids_batch(
                point_ids,
                candidate_limit=candidate_limit,
                limit=final_limit,
                repo_ids=repo_ids,
                score_threshold=min_semantic_score,
            )
            query_batches += 1
            payload_updates: list[tuple[str | int, dict[str, Any]]] = []
            graphified_at = datetime.now(timezone.utc).isoformat()
            for point, candidates in zip(group, candidate_groups):
                point_id = point.get("id")
                payload = dict(point.get("payload") or {})
                ranked: list[dict[str, Any]] = []
                for candidate in candidates:
                    if str(candidate.get("id")) == str(point_id):
                        continue
                    score = float(candidate.get("score", 0.0))
                    candidate_payload = dict(candidate.get("payload") or {})
                    ranked.append({
                        "edge_type": "semantic_neighbor",
                        "id": str(candidate.get("id")),
                        "semantic_score": round(score, 8),
                        "repo": candidate_payload.get("repo"),
                        "path": candidate_payload.get("path"),
                        "start_line": candidate_payload.get("start_line"),
                        "end_line": candidate_payload.get("end_line"),
                    })
                    if len(ranked) >= neighbors:
                        break
                edge_count += len(ranked)
                cross_repo_edges += sum(1 for item in ranked if item.get("repo") != payload.get("repo"))
                if point_id is not None:
                    payload_updates.append((point_id, {
                        "graph_neighbors": ranked,
                        "graphify_version": "graphify-v4-qdrant-prefetch-rerank",
                        "graphified_at": graphified_at,
                        "cos_level_bindings": ["L8", "L9", "L10", "L11", "L12"],
                    }))
                    updated += 1
            if payload_updates:
                self.qdrant.set_payload_batch(payload_updates)
                write_batches += 1
        return {
            "graphify_version": "graphify-v4-qdrant-prefetch-rerank",
            "collection": self.config.qdrant_collection,
            "nodes_seen": len(points),
            "nodes_updated": updated,
            "edges": edge_count,
            "cross_repo_edges": cross_repo_edges,
            "neighbors_per_node": neighbors,
            "query_batch_size": query_batch_size,
            "query_batches": query_batches,
            "write_batches": write_batches,
            "candidate_limit": candidate_limit,
            "vector_payload_transfer": "none",
            "rerank_backend": "qdrant Query API: cos20 prefetch -> semantic rerank by point id",
            "cos_active_levels": {
                "L8": "Knowledge Graph: chunk identity + provenance + repository-owned structural metadata",
                "L9": "Semantic Graph: semantic-neighbor relations",
                "L10": "Embedding Graph: bge-m3 1024D + cos20 route vector",
                "L11": "GraphRAG: Qdrant cos20 prefetch -> semantic rerank -> provenance",
                "L12": "Memory Graph: rebuildable Qdrant projection; Git remains authority",
            },
        }

    def cos_graph_engine(self, query: str, *, limit: int = 10, repo_ids: Sequence[str] | None = None) -> dict[str, Any]:
        hits = self.search(query, limit=limit, repo_ids=repo_ids)
        return {"query": query, "collection": self.config.qdrant_collection, "pipeline": ["Ollama bge-m3 1024D embedding", "deterministic cos20 routing projection", "Qdrant cos20 + native semantic candidate union", "1024D cosine + bounded path/text intent rerank", "provenance-preserving GraphRAG result"], "cos_20_levels": list(COS_LEVELS), "active_retrieval_levels": ["L8", "L9", "L10", "L11", "L12"], "hits": [asdict(hit) for hit in hits]}
