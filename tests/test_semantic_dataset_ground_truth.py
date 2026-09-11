from __future__ import annotations

import fnmatch
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "benchmarks" / "semantic_retrieval_v1.json"
MOTION_REPO_ID = "rotprods/motion-OS"


def _tracked_candidate_paths() -> list[str]:
    excluded_roots = {".git", ".venv", "node_modules", "dist", "build", "__pycache__"}
    paths: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in excluded_roots for part in rel.parts):
            continue
        paths.append(rel.as_posix())
    return paths


def test_semantic_retrieval_dataset_has_25_cases_and_frozen_gates() -> None:
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    assert len(dataset["cases"]) == 25
    assert dataset["k"] == 10
    assert dataset["gates"] == {
        "hit_rate_at_k_min": 0.92,
        "mean_recall_at_k_min": 0.75,
        "mrr_min": 0.72,
        "ndcg_at_k_min": 0.75,
    }


def test_every_motion_ground_truth_target_matches_a_real_file() -> None:
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    files = _tracked_candidate_paths()
    missing: list[str] = []
    for case in dataset["cases"]:
        for target in case["expected"]:
            if target["repo"] != MOTION_REPO_ID:
                continue
            pattern = target["path_glob"]
            if not any(fnmatch.fnmatch(path, pattern) for path in files):
                missing.append(f"{case['id']}:{pattern}")
    assert not missing, "stale Motion semantic ground-truth targets: " + ", ".join(missing)


def test_ground_truth_contains_no_known_stale_architecture_paths() -> None:
    dataset_text = DATASET.read_text(encoding="utf-8")
    stale = {
        "src/visual_dna/**",
        "src/extraction/normalize.py",
        "src/extraction/compilers.py",
        "src/knowledge/reference_store.py",
        "scripts/run_phase04_visual_dna_superwave.py",
        "hooks/**",
    }
    found = sorted(path for path in stale if path in dataset_text)
    assert not found, "known stale benchmark labels reintroduced: " + ", ".join(found)
