from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import hashlib
import json
import math
import re


class GauntletError(ValueError):
    pass


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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
        if not isinstance(raw, dict):
            raise GauntletError("attempt must be an object")
        iteration = raw.get("iteration")
        if isinstance(iteration, bool) or not isinstance(iteration, int) or iteration < 1:
            raise GauntletError("attempt iteration must be a positive integer")
        strategy = str(raw.get("strategy", "")).strip()
        if not strategy:
            raise GauntletError("attempt strategy is required")
        result_hash = str(raw.get("result_hash", ""))
        if not SHA256_RE.fullmatch(result_hash):
            raise GauntletError("attempt result_hash must be lowercase sha256")
        verifier_complete = raw.get("verifier_complete", False)
        if type(verifier_complete) is not bool:
            raise GauntletError("verifier_complete must be a JSON boolean")
        progress_raw = raw.get("measurable_progress", 0.0)
        if isinstance(progress_raw, bool) or not isinstance(progress_raw, (int, float)):
            raise GauntletError("measurable_progress must be numeric")
        measurable_progress = float(progress_raw)
        if not math.isfinite(measurable_progress):
            raise GauntletError("measurable_progress must be finite")
        return cls(
            iteration=iteration,
            strategy=strategy,
            result_hash=result_hash,
            verifier_complete=verifier_complete,
            verifier_reason=str(raw.get("verifier_reason", "")).strip(),
            measurable_progress=measurable_progress,
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
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts < 1:
        raise GauntletError("max_attempts must be a positive integer")
    if isinstance(min_progress_delta, bool) or not isinstance(min_progress_delta, (int, float)):
        raise GauntletError("min_progress_delta must be numeric")
    min_progress_delta = float(min_progress_delta)
    if not math.isfinite(min_progress_delta) or min_progress_delta < 0:
        raise GauntletError("min_progress_delta must be finite and non-negative")
    if type(kill_switch) is not bool:
        raise GauntletError("kill_switch must be a JSON boolean")
    if kill_switch:
        return {"state": "BLOCKED", "reason": "KILL_SWITCH_ACTIVE", "next_action": "stop immediately"}
    if not isinstance(attempts, list):
        raise GauntletError("attempts must be an array")

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
        same_strategy = latest.strategy.casefold() == prev.strategy.casefold()
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
