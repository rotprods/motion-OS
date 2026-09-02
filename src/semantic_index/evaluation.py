from __future__ import annotations

import fnmatch
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .core import SearchHit
from .engine import SemanticKnowledgePlane


@dataclass(frozen=True)
class ExpectedTarget:
    repo: str
    path_glob: str


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    query: str
    expected: tuple[ExpectedTarget, ...]


@dataclass(frozen=True)
class EvaluationDataset:
    name: str
    k: int
    repo_ids: tuple[str, ...]
    chunk_oversample: int
    gates: dict[str, float]
    cases: tuple[EvaluationCase, ...]


def load_dataset(path: Path) -> EvaluationDataset:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("evaluation dataset must be a JSON object")
    cases_raw = raw.get("cases")
    if not isinstance(cases_raw, list) or not cases_raw:
        raise ValueError("evaluation dataset requires at least one case")

    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()
    for item in cases_raw:
        if not isinstance(item, dict):
            raise ValueError("every evaluation case must be an object")
        case_id = str(item.get("id") or "").strip()
        query = str(item.get("query") or "").strip()
        expected_raw = item.get("expected")
        if not case_id or case_id in seen_ids:
            raise ValueError(f"invalid or duplicate case id: {case_id!r}")
        if not query:
            raise ValueError(f"case {case_id!r} has an empty query")
        if not isinstance(expected_raw, list) or not expected_raw:
            raise ValueError(f"case {case_id!r} requires expected targets")
        expected: list[ExpectedTarget] = []
        for target in expected_raw:
            if not isinstance(target, dict):
                raise ValueError(f"case {case_id!r} contains a non-object expected target")
            repo = str(target.get("repo") or "").strip()
            path_glob = str(target.get("path_glob") or "").strip().replace("\\", "/")
            if not repo or not path_glob:
                raise ValueError(f"case {case_id!r} has an incomplete expected target")
            expected.append(ExpectedTarget(repo=repo, path_glob=path_glob))
        seen_ids.add(case_id)
        cases.append(EvaluationCase(case_id=case_id, query=query, expected=tuple(expected)))

    k = int(raw.get("k", 10))
    if k < 1:
        raise ValueError("k must be >= 1")
    chunk_oversample = int(raw.get("chunk_oversample", 8))
    if chunk_oversample < 1:
        raise ValueError("chunk_oversample must be >= 1")
    repo_ids_raw = raw.get("repo_ids") or []
    if not isinstance(repo_ids_raw, list) or not repo_ids_raw:
        repo_ids = tuple(sorted({target.repo for case in cases for target in case.expected}))
    else:
        repo_ids = tuple(str(value) for value in repo_ids_raw if str(value).strip())
    gates_raw = raw.get("gates") or {}
    if not isinstance(gates_raw, dict):
        raise ValueError("gates must be an object")
    gates = {
        "hit_rate_at_k_min": float(gates_raw.get("hit_rate_at_k_min", 0.85)),
        "mean_recall_at_k_min": float(gates_raw.get("mean_recall_at_k_min", 0.70)),
        "mrr_min": float(gates_raw.get("mrr_min", 0.65)),
        "ndcg_at_k_min": float(gates_raw.get("ndcg_at_k_min", 0.70)),
    }
    for name, value in gates.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"gate {name} must be between 0 and 1")
    return EvaluationDataset(
        name=str(raw.get("name") or path.stem),
        k=k,
        repo_ids=repo_ids,
        chunk_oversample=chunk_oversample,
        gates=gates,
        cases=tuple(cases),
    )


def _file_key(hit: SearchHit) -> tuple[str, str] | None:
    repo = str(hit.payload.get("repo") or "").strip()
    path = str(hit.payload.get("path") or "").strip().replace("\\", "/")
    if not repo or not path:
        return None
    return repo, path


def _dedupe_files(hits: Sequence[SearchHit], k: int) -> list[SearchHit]:
    seen: set[tuple[str, str]] = set()
    files: list[SearchHit] = []
    for hit in hits:
        key = _file_key(hit)
        if key is None or key in seen:
            continue
        seen.add(key)
        files.append(hit)
        if len(files) >= k:
            break
    return files


def _matches(repo: str, path: str, target: ExpectedTarget) -> bool:
    return repo == target.repo and fnmatch.fnmatch(path, target.path_glob)


def score_case(case: EvaluationCase, hits: Sequence[SearchHit], *, k: int) -> dict[str, Any]:
    ranked = _dedupe_files(hits, k)
    covered: set[int] = set()
    relevance: list[int] = []
    first_relevant_rank: int | None = None
    ranked_files: list[dict[str, Any]] = []

    for rank, hit in enumerate(ranked, start=1):
        key = _file_key(hit)
        assert key is not None
        repo, path = key
        matches = [index for index, target in enumerate(case.expected) if _matches(repo, path, target)]
        if matches and first_relevant_rank is None:
            first_relevant_rank = rank
        covered.update(matches)
        relevance.append(1 if matches else 0)
        ranked_files.append(
            {
                "rank": rank,
                "repo": repo,
                "path": path,
                "semantic_score": round(float(hit.semantic_score), 8),
                "route_score": round(float(hit.route_score), 8),
                "matched_target_indices": matches,
            }
        )

    hit_at_k = 1.0 if covered else 0.0
    recall_at_k = len(covered) / len(case.expected)
    reciprocal_rank = 0.0 if first_relevant_rank is None else 1.0 / first_relevant_rank
    dcg = sum(rel / math.log2(rank + 1) for rank, rel in enumerate(relevance, start=1))
    ideal_relevant = min(len(case.expected), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_relevant + 1))
    ndcg = dcg / idcg if idcg else 0.0

    return {
        "id": case.case_id,
        "query": case.query,
        "expected": [{"repo": target.repo, "path_glob": target.path_glob} for target in case.expected],
        "hit_at_k": round(hit_at_k, 6),
        "recall_at_k": round(recall_at_k, 6),
        "reciprocal_rank": round(reciprocal_rank, 6),
        "ndcg_at_k": round(ndcg, 6),
        "covered_targets": len(covered),
        "target_count": len(case.expected),
        "ranked_files": ranked_files,
    }


def evaluate_dataset(
    plane: SemanticKnowledgePlane,
    dataset_path: Path,
    *,
    k_override: int | None = None,
) -> dict[str, Any]:
    dataset = load_dataset(dataset_path)
    k = k_override or dataset.k
    if k < 1:
        raise ValueError("k_override must be >= 1")
    fetch_limit = max(k, k * dataset.chunk_oversample)
    cases: list[dict[str, Any]] = []
    for case in dataset.cases:
        hits = plane.search(case.query, limit=fetch_limit, repo_ids=dataset.repo_ids)
        cases.append(score_case(case, hits, k=k))

    hit_rate = statistics.mean(case["hit_at_k"] for case in cases)
    mean_recall = statistics.mean(case["recall_at_k"] for case in cases)
    mrr = statistics.mean(case["reciprocal_rank"] for case in cases)
    ndcg = statistics.mean(case["ndcg_at_k"] for case in cases)
    metrics = {
        "hit_rate_at_k": round(hit_rate, 6),
        "mean_recall_at_k": round(mean_recall, 6),
        "mrr": round(mrr, 6),
        "ndcg_at_k": round(ndcg, 6),
    }
    gates = {
        "hit_rate_at_k": metrics["hit_rate_at_k"] >= dataset.gates["hit_rate_at_k_min"],
        "mean_recall_at_k": metrics["mean_recall_at_k"] >= dataset.gates["mean_recall_at_k_min"],
        "mrr": metrics["mrr"] >= dataset.gates["mrr_min"],
        "ndcg_at_k": metrics["ndcg_at_k"] >= dataset.gates["ndcg_at_k_min"],
    }
    return {
        "dataset": dataset.name,
        "dataset_path": str(dataset_path),
        "case_count": len(cases),
        "repo_ids": list(dataset.repo_ids),
        "k": k,
        "chunk_oversample": dataset.chunk_oversample,
        "fetch_limit": fetch_limit,
        "metrics": metrics,
        "thresholds": dataset.gates,
        "gates": gates,
        "passed": all(gates.values()),
        "cases": cases,
    }
