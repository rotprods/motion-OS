from __future__ import annotations

from copy import deepcopy
from random import Random
from typing import Any, Callable


MUTATION_KEYS = (
    "drop_required",
    "wrong_type",
    "oversize_string",
    "unknown_enum",
    "null_nested",
    "duplicate_beat_id",
    "future_schema",
)


def mutate_manifest(base: dict[str, Any], *, seed: int, rounds: int = 25) -> list[dict[str, Any]]:
    rng = Random(seed)
    out: list[dict[str, Any]] = []
    required = ["content_id", "script_display_text", "script_tts_text", "semantic_beats", "viral_driver"]
    for _ in range(rounds):
        item = deepcopy(base)
        mutation = rng.choice(MUTATION_KEYS)
        item["_fuzz_mutation"] = mutation
        if mutation == "drop_required":
            item.pop(rng.choice(required), None)
        elif mutation == "wrong_type":
            item[rng.choice(required)] = rng.choice([[], {}, 3.14159, True, None])
        elif mutation == "oversize_string":
            item["script_tts_text"] = "A" * 100_000
        elif mutation == "unknown_enum":
            item["viral_driver"] = "UNBOUNDED_MAGIC"
        elif mutation == "null_nested":
            item["cta"] = None
        elif mutation == "duplicate_beat_id":
            beats = deepcopy(item.get("semantic_beats") or [])
            if beats:
                beats.append(deepcopy(beats[0]))
            item["semantic_beats"] = beats
        elif mutation == "future_schema":
            item["schema_version"] = 999
        out.append(item)
    return out


def mutate_provider_result(*, seed: int, rounds: int = 25) -> list[dict[str, Any]]:
    rng = Random(seed)
    values = []
    for _ in range(rounds):
        case = rng.randrange(8)
        if case == 0:
            values.append({"status": "ALIEN_STATE"})
        elif case == 1:
            values.append({"status": "completed", "duration": -rng.random()})
        elif case == 2:
            values.append({"status": "completed", "duration": "not-a-number"})
        elif case == 3:
            values.append({"status": "completed", "video_url": "file:///etc/passwd"})
        elif case == 4:
            values.append({"status": "completed", "video_url": 123})
        elif case == 5:
            values.append({"status": "processing", "id": "x" * 500})
        elif case == 6:
            values.append({"status": None, "duration": None})
        else:
            values.append({"status": "completed", "duration": rng.uniform(1, 300), "video_url": "https://example.test/v.mp4"})
    return values


def run_no_crash(cases: list[dict[str, Any]], evaluator: Callable[[dict[str, Any]], Any]) -> list[tuple[str, str]]:
    """Execute malformed cases and return only unexpected exception classes/messages.

    ValueError/TypeError/RuntimeError/PermissionError are considered controlled rejections.
    Any other exception is a harness finding because malformed external input should not
    cause an unclassified crash.
    """
    findings: list[tuple[str, str]] = []
    controlled = (ValueError, TypeError, RuntimeError, PermissionError, KeyError)
    for case in cases:
        try:
            evaluator(case)
        except controlled:
            continue
        except Exception as exc:  # pragma: no cover - this path is the thing fuzzing seeks
            findings.append((type(exc).__name__, str(exc)))
    return findings
