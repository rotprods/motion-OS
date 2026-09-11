from __future__ import annotations

import math
import random
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any, Sequence

from .core import RepoManifest, DeterministicJLProjector, chunk_repository, cosine, l2_normalize
from .engine import SemanticKnowledgePlane


def _percentile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def _synthetic_vectors(*, count: int = 480, dims: int = 1024, clusters: int = 12, seed: int = 20260902) -> tuple[list[list[float]], list[int]]:
    rng = random.Random(seed)
    centers = [l2_normalize([rng.gauss(0.0, 1.0) for _ in range(dims)]) for _ in range(clusters)]
    vectors: list[list[float]] = []
    labels: list[int] = []
    for index in range(count):
        label = index % clusters
        center = centers[label]
        vector = [center[j] + rng.gauss(0.0, 0.055) for j in range(dims)]
        vectors.append(l2_normalize(vector))
        labels.append(label)
    return vectors, labels


def benchmark_synthetic(*, semantic_dims: int = 1024, route_dims: int = 20, k: int = 10, route_multiplier: int = 32) -> dict[str, Any]:
    projector = DeterministicJLProjector(output_dims=route_dims)
    vectors, labels = _synthetic_vectors(dims=semantic_dims)
    start = time.perf_counter()
    routes = [projector.project(vector) for vector in vectors]
    projection_seconds = time.perf_counter() - start
    query_indices = list(range(0, len(vectors), max(1, len(vectors) // 40)))[:40]
    candidate_count = min(len(vectors) - 1, max(k * route_multiplier, 32))
    exact_neighbor_recall: list[float] = []
    topic_precision: list[float] = []
    rerank_topic_precision: list[float] = []
    query_latencies_ms: list[float] = []
    for query_index in query_indices:
        started = time.perf_counter()
        semantic = vectors[query_index]
        route = routes[query_index]
        truth = sorted(((idx, cosine(semantic, vector)) for idx, vector in enumerate(vectors) if idx != query_index), key=lambda item: item[1], reverse=True)
        truth_ids = {idx for idx, _ in truth[:k]}
        route_ranked = sorted(((idx, cosine(route, candidate_route)) for idx, candidate_route in enumerate(routes) if idx != query_index), key=lambda item: item[1], reverse=True)
        candidate_ids = [idx for idx, _ in route_ranked[:candidate_count]]
        exact_neighbor_recall.append(len(truth_ids.intersection(candidate_ids)) / k)
        topic_precision.append(sum(labels[idx] == labels[query_index] for idx in candidate_ids[:k]) / k)
        reranked = sorted(((idx, cosine(semantic, vectors[idx])) for idx in candidate_ids), key=lambda item: item[1], reverse=True)[:k]
        rerank_topic_precision.append(sum(labels[idx] == labels[query_index] for idx, _ in reranked) / k)
        query_latencies_ms.append((time.perf_counter() - started) * 1000)
    with tempfile.TemporaryDirectory(prefix="semantic-bench-") as tmp:
        root = Path(tmp)
        (root / "src").mkdir()
        for i in range(120):
            text = f"# module {i}\n\n" + "\n\n".join(f"def function_{i}_{j}(value):\n    return value * {j + 1}\n" for j in range(12))
            (root / "src" / f"module_{i}.py").write_text(text, encoding="utf-8")
        manifest = RepoManifest(repo_id="benchmark/synthetic", include=("*", "**/*"), target_chars=900, max_chars=1300, overlap_chars=120)
        started = time.perf_counter()
        chunks = chunk_repository(root, manifest)
        chunk_seconds = time.perf_counter() - started
        total_bytes = sum(len(chunk.text.encode("utf-8")) for chunk in chunks)
    report = {
        "kind": "synthetic-core",
        "vectors": len(vectors),
        "semantic_dims": semantic_dims,
        "route_dims": route_dims,
        "queries": len(query_indices),
        "k": k,
        "route_multiplier": route_multiplier,
        "candidate_count": candidate_count,
        "projection_vectors_per_second": round(len(vectors) / max(projection_seconds, 1e-9), 2),
        "route_candidate_exact_recall_at_k_mean": round(statistics.mean(exact_neighbor_recall), 4),
        "route_topic_precision_at_k_mean": round(statistics.mean(topic_precision), 4),
        "reranked_topic_precision_at_k_mean": round(statistics.mean(rerank_topic_precision), 4),
        "synthetic_query_cpu_ms_p50": round(_percentile(query_latencies_ms, 0.50), 3),
        "synthetic_query_cpu_ms_p95": round(_percentile(query_latencies_ms, 0.95), 3),
        "chunk_count": len(chunks),
        "chunking_mib_per_second": round((total_bytes / (1024 * 1024)) / max(chunk_seconds, 1e-9), 3),
        "gates": {
            "projection_is_20d": route_dims == 20,
            "reranked_topic_precision_at_k_gte_0_99": statistics.mean(rerank_topic_precision) >= 0.99,
            "candidate_exact_recall_at_k_gte_0_95": statistics.mean(exact_neighbor_recall) >= 0.95,
        },
    }
    report["passed"] = all(report["gates"].values())
    return report


def benchmark_live(plane: SemanticKnowledgePlane, *, iterations: int = 8) -> dict[str, Any]:
    doctor = plane.doctor()
    if not doctor.get("ok"):
        return {"kind": "live-services", "passed": False, "doctor": doctor, "reason": "services_unavailable"}
    embed_ms: list[float] = []
    search_ms: list[float] = []
    sample = ["reference retrieval visual dna motion graphics", "agent coordination causal graph qdrant", "semantic chunk provenance repository", "style signature render critic"]
    for index in range(iterations):
        started = time.perf_counter()
        plane.ollama.embed(sample)
        embed_ms.append((time.perf_counter() - started) * 1000)
        started = time.perf_counter()
        plane.search(sample[index % len(sample)], limit=10)
        search_ms.append((time.perf_counter() - started) * 1000)
    return {
        "kind": "live-services",
        "passed": True,
        "iterations": iterations,
        "ollama_batch4_ms_p50": round(_percentile(embed_ms, 0.50), 3),
        "ollama_batch4_ms_p95": round(_percentile(embed_ms, 0.95), 3),
        "end_to_end_search_ms_p50": round(_percentile(search_ms, 0.50), 3),
        "end_to_end_search_ms_p95": round(_percentile(search_ms, 0.95), 3),
        "doctor": doctor,
    }
