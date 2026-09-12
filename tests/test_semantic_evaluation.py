from __future__ import annotations

import json
from pathlib import Path

from src.semantic_index.core import SearchHit
from src.semantic_index.evaluation import EvaluationCase, ExpectedTarget, evaluate_dataset, load_dataset, score_case


def _hit(point_id: str, repo: str, path: str, score: float) -> SearchHit:
    return SearchHit(point_id=point_id, semantic_score=score, route_score=score - 0.05, payload={"repo": repo, "path": path})


class FakePlane:
    def __init__(self, by_query: dict[str, list[SearchHit]]):
        self.by_query = by_query
        self.calls: list[tuple[str, int, tuple[str, ...]]] = []

    def search(self, query: str, *, limit: int, repo_ids=None):
        self.calls.append((query, limit, tuple(repo_ids or ())))
        return list(self.by_query[query])[:limit]


def test_score_case_deduplicates_chunks_by_file_before_ranking(tmp_path: Path) -> None:
    dataset = {
        "name": "dedupe",
        "k": 3,
        "repo_ids": ["repo/a"],
        "cases": [
            {
                "id": "case",
                "query": "alpha",
                "expected": [
                    {"repo": "repo/a", "path_glob": "src/a.py"},
                    {"repo": "repo/a", "path_glob": "src/b.py"}
                ]
            }
        ]
    }
    case = load_dataset(_write_dataset(dataset, tmp_path)).cases[0]
    result = score_case(
        case,
        [
            _hit("a-1", "repo/a", "src/a.py", 0.99),
            _hit("a-2", "repo/a", "src/a.py", 0.98),
            _hit("x", "repo/a", "src/x.py", 0.80),
            _hit("b", "repo/a", "src/b.py", 0.70),
        ],
        k=3,
    )
    assert [row["path"] for row in result["ranked_files"]] == ["src/a.py", "src/x.py", "src/b.py"]
    assert result["covered_targets"] == 2
    assert result["recall_at_k"] == 1.0
    assert result["reciprocal_rank"] == 1.0


def _write_dataset(payload: dict, directory: Path) -> Path:
    path = directory / "semantic_eval.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_evaluate_dataset_reports_hit_recall_mrr_ndcg_and_gates(tmp_path: Path) -> None:
    path = tmp_path / "dataset.json"
    payload = {
        "name": "metric-contract",
        "k": 2,
        "chunk_oversample": 8,
        "repo_ids": ["repo/a", "repo/b"],
        "gates": {
            "hit_rate_at_k_min": 0.9,
            "mean_recall_at_k_min": 0.9,
            "mrr_min": 0.7,
            "ndcg_at_k_min": 0.7
        },
        "cases": [
            {
                "id": "a",
                "query": "query-a",
                "expected": [{"repo": "repo/a", "path_glob": "src/a.py"}]
            },
            {
                "id": "b",
                "query": "query-b",
                "expected": [{"repo": "repo/b", "path_glob": "docs/*.md"}]
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    plane = FakePlane(
        {
            "query-a": [_hit("a1", "repo/a", "src/a.py", 0.9), _hit("x1", "repo/a", "src/x.py", 0.8)],
            "query-b": [_hit("x2", "repo/b", "src/other.py", 0.9), _hit("b1", "repo/b", "docs/guide.md", 0.8)],
        }
    )
    report = evaluate_dataset(plane, path)
    assert report["case_count"] == 2
    assert report["fetch_limit"] == 16
    assert report["metrics"]["hit_rate_at_k"] == 1.0
    assert report["metrics"]["mean_recall_at_k"] == 1.0
    assert report["metrics"]["mrr"] == 0.75
    assert report["metrics"]["ndcg_at_k"] > 0.8
    assert report["passed"] is True
    assert all(call[1] == 16 for call in plane.calls)


def test_dataset_rejects_duplicate_case_ids(tmp_path: Path) -> None:
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps({
        "cases": [
            {"id": "dup", "query": "a", "expected": [{"repo": "r", "path_glob": "a.py"}]},
            {"id": "dup", "query": "b", "expected": [{"repo": "r", "path_glob": "b.py"}]}
        ]
    }), encoding="utf-8")
    try:
        load_dataset(path)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate ids must fail closed")


def test_ndcg_does_not_reward_repeated_files_in_one_target_group() -> None:
    case = EvaluationCase("glob", "find docs", (ExpectedTarget("repo/a", "docs/**"),))
    hits = [
        _hit("1", "repo/a", "docs/a.md", 0.9),
        _hit("2", "repo/a", "docs/b.md", 0.8),
        _hit("3", "repo/a", "docs/c.md", 0.7),
    ]
    result = score_case(case, hits, k=3)
    assert result["ndcg_at_k"] == 1.0
    assert result["covered_targets"] == 1
    assert [row["new_target_indices"] for row in result["ranked_files"]] == [[0], [], []]


def test_repeated_target_does_not_hide_a_delayed_second_target() -> None:
    case = EvaluationCase("two", "find code and docs", (
        ExpectedTarget("repo/a", "docs/**"), ExpectedTarget("repo/a", "src/**"),
    ))
    result = score_case(case, [
        _hit("1", "repo/a", "docs/a.md", 0.9),
        _hit("2", "repo/a", "docs/b.md", 0.8),
        _hit("3", "repo/a", "src/code.py", 0.7),
    ], k=3)
    assert result["ndcg_at_k"] == 0.919721
    assert result["recall_at_k"] == 1.0


def test_overlapping_target_globs_cannot_inflate_ndcg() -> None:
    case = EvaluationCase("overlap", "find code", (
        ExpectedTarget("repo/a", "src/**"), ExpectedTarget("repo/a", "src/a.py"),
    ))
    result = score_case(case, [
        _hit("1", "repo/a", "src/a.py", 0.9),
        _hit("2", "repo/a", "src/b.py", 0.8),
        _hit("3", "repo/a", "src/c.py", 0.7),
    ], k=3)
    assert 0.0 <= result["ndcg_at_k"] <= 1.0
    assert result["recall_at_k"] == 1.0
