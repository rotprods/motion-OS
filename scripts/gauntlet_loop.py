from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import hashlib
import json


class GauntletError(ValueError):
    pass


@dataclass(frozen=True)
class Attempt:
    iteration: int
    strategy: str
    result_hash: str
    verifier_complete: bool
    verifier_reason: str
    measurable_progress: float

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Attempt":
        return cls(
            iteration=int(raw["iteration"]),
            strategy=str(raw["strategy"]),
            result_hash=str(raw["result_hash"]),
            verifier_complete=bool(raw.get("verifier_complete", False)),
            verifier_reason=str(raw.get("verifier_reason", "")),
            measurable_progress=float(raw.get("measurable_progress", 0.0)),
        )


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evaluate_gauntlet(
    attempts: list[dict[str, Any]],
    *,
    max_attempts: int = 3,
    min_progress_delta: float = 0.01,
    kill_switch: bool = False,
) -> dict[str, Any]:
    if max_attempts < 1:
        raise GauntletError("max_attempts must be >= 1")
    if kill_switch:
        return {"state": "BLOCKED", "reason": "KILL_SWITCH_ACTIVE", "next_action": "stop immediately"}
    parsed = [Attempt.from_dict(item) for item in attempts]
    if not parsed:
        return {"state": "ITERATE", "reason": "NO_ATTEMPTS", "remaining_attempts": max_attempts}
    iterations = [item.iteration for item in parsed]
    if iterations != list(range(1, len(parsed) + 1)):
        raise GauntletError("attempt iterations must be contiguous starting at 1")
    if len(parsed) > max_attempts:
        raise GauntletError("attempt history exceeds configured budget")

    latest = parsed[-1]
    if latest.verifier_complete:
        return {
            "state": "VERIFIED",
            "reason": latest.verifier_reason or "VERIFIER_COMPLETE",
            "attempts": len(parsed),
            "result_hash": latest.result_hash,
        }

    if len(parsed) >= max_attempts:
        return {
            "state": "BLOCKED",
            "reason": "ATTEMPT_BUDGET_EXHAUSTED",
            "attempts": len(parsed),
            "next_action": "persist blocker and require a materially different strategy or authority input",
        }

    if len(parsed) >= 2:
        prev = parsed[-2]
        same_strategy = latest.strategy.strip().lower() == prev.strategy.strip().lower()
        same_result = latest.result_hash == prev.result_hash
        progress_delta = latest.measurable_progress - prev.measurable_progress
        if same_strategy and (same_result or progress_delta < min_progress_delta):
            return {
                "state": "BLOCKED",
                "reason": "STUCK_LOOP",
                "attempts": len(parsed),
                "verifier_feedback": latest.verifier_reason,
                "next_action": "change strategy before any retry",
            }

    return {
        "state": "ITERATE",
        "reason": "VERIFIER_NOT_COMPLETE",
        "attempts": len(parsed),
        "remaining_attempts": max_attempts - len(parsed),
        "verifier_feedback": latest.verifier_reason,
        "require_materially_different_strategy": len(parsed) >= 2,
    }
