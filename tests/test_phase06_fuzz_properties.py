from __future__ import annotations

from src.avatar.heygen_adapter import validate_provider_result
from src.content.content_factory import preflight_manifest
from src.content.fuzz_harness import mutate_manifest, mutate_provider_result, run_no_crash
from src.content.schema_migrations import migrate


PROFILE = {
    "initial_words_per_second": 2.55,
    "duration_hard_min_s": 30,
    "duration_hard_max_s": 45,
    "pause_cost_s": {"comma": .1, "sentence": .22, "ellipsis": .32, "colon": .16},
}

BASE = {
    "content_id": "CNT_FUZZ",
    "schema_version": 2,
    "source_refs": ["https://example.test"],
    "claims": [],
    "viral_driver": "MONEY",
    "script_display_text": "Esto es una frase simple. " * 18,
    "script_tts_text": "Esto es una frase simple. " * 18,
    "semantic_beats": [
        {"id": "B00_HOOK", "function": "hook", "text": "hook", "target_duration_s": 3.0},
        {"id": "B01_PROOF", "function": "proof", "text": "proof", "target_duration_s": 3.0},
    ],
    "cta": {"text": "Comenta TEST"},
    "moral": "Cierre.",
}


def test_manifest_fuzz_has_no_unclassified_crashes():
    cases = mutate_manifest(BASE, seed=606, rounds=100)

    def evaluate(case):
        if case.get("schema_version", 1) != 2:
            case = migrate(case)
        return preflight_manifest(case, PROFILE)

    assert run_no_crash(cases, evaluate) == []


def test_provider_fuzz_validation_never_crashes():
    cases = mutate_provider_result(seed=607, rounds=100)
    assert run_no_crash(cases, validate_provider_result) == []


def test_fuzz_is_deterministic_for_same_seed():
    assert mutate_manifest(BASE, seed=99, rounds=12) == mutate_manifest(BASE, seed=99, rounds=12)
    assert mutate_provider_result(seed=99, rounds=12) == mutate_provider_result(seed=99, rounds=12)
