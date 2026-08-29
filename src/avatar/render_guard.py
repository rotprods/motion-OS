from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from numbers import Real
from typing import Any
import hashlib
import json
import math


class RenderState(str, Enum):
    PREPARED = "PREPARED"
    AUTHORIZED = "AUTHORIZED"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"


def _finite_nonnegative_number(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite non-negative number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return normalized


def _nonnegative_int(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


@dataclass(frozen=True)
class SpendPolicy:
    max_credits_per_render: float
    max_credits_per_day: float
    max_concurrent_renders: int
    max_retries: int = 1

    def __post_init__(self) -> None:
        per_render = _finite_nonnegative_number(self.max_credits_per_render, name="max_credits_per_render")
        per_day = _finite_nonnegative_number(self.max_credits_per_day, name="max_credits_per_day")
        if per_render > per_day:
            raise ValueError("max_credits_per_render cannot exceed max_credits_per_day")
        concurrent = _nonnegative_int(self.max_concurrent_renders, name="max_concurrent_renders")
        if concurrent < 1:
            raise ValueError("max_concurrent_renders must be at least 1")
        _nonnegative_int(self.max_retries, name="max_retries")


@dataclass(frozen=True)
class RenderIntent:
    intent_id: str
    content_id: str
    profile_id: str
    script_hash: str
    state: RenderState
    estimated_credits: float | None = None
    provider_job_id: str | None = None
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["state"] = self.state.value
        return out


def hash_script(script: str) -> str:
    return hashlib.sha256(script.strip().encode("utf-8")).hexdigest()


def make_render_intent_id(*, content_id: str, profile_id: str, script: str, provider: str = "heygen") -> str:
    canonical = json.dumps({
        "content_id": content_id,
        "profile_id": profile_id,
        "script_hash": hash_script(script),
        "provider": provider,
    }, sort_keys=True, separators=(",", ":"))
    return "RND_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20].upper()


def authorize_render(*, content_id: str, profile_id: str, script: str, explicit_authorization: bool,
                     preflight_ok: bool, estimated_credits: float | None, spent_today: float,
                     concurrent_renders: int, policy: SpendPolicy) -> RenderIntent:
    if explicit_authorization is not True:
        raise PermissionError("explicit render authorization required")
    if preflight_ok is not True:
        raise ValueError("preflight must pass before render authorization")
    spent = _finite_nonnegative_number(spent_today, name="spent_today")
    concurrent = _nonnegative_int(concurrent_renders, name="concurrent_renders")
    if concurrent >= policy.max_concurrent_renders:
        raise RuntimeError("concurrent render limit reached")
    if estimated_credits is None:
        raise ValueError("estimated_credits is required for paid render authorization")
    credits = _finite_nonnegative_number(estimated_credits, name="estimated_credits")
    if credits > policy.max_credits_per_render:
        raise RuntimeError("per-render credit budget exceeded")
    if spent + credits > policy.max_credits_per_day:
        raise RuntimeError("daily credit budget exceeded")
    script_hash = hash_script(script)
    return RenderIntent(
        intent_id=make_render_intent_id(content_id=content_id, profile_id=profile_id, script=script),
        content_id=content_id,
        profile_id=profile_id,
        script_hash=script_hash,
        state=RenderState.AUTHORIZED,
        estimated_credits=credits,
    )


def can_submit(intent: RenderIntent, known_intents: dict[str, RenderIntent]) -> bool:
    existing = known_intents.get(intent.intent_id)
    if existing is None:
        return intent.state == RenderState.AUTHORIZED
    # Any ambiguous or already-spent state must reconcile, never blindly resubmit.
    return existing.state in {RenderState.FAILED_RETRYABLE} and existing.provider_job_id is None


def next_retry(intent: RenderIntent, policy: SpendPolicy) -> RenderIntent:
    if intent.state != RenderState.FAILED_RETRYABLE:
        raise ValueError("retry allowed only from FAILED_RETRYABLE")
    if intent.provider_job_id:
        raise RuntimeError("provider job exists; reconcile instead of retrying")
    retry_count = _nonnegative_int(intent.retry_count, name="retry_count")
    if retry_count >= policy.max_retries:
        return RenderIntent(**{**intent.__dict__, "state": RenderState.FAILED_FINAL})
    return RenderIntent(**{**intent.__dict__, "state": RenderState.AUTHORIZED, "retry_count": retry_count + 1})


def reconcile_state(intent: RenderIntent, provider_status: str | None, provider_job_id: str | None) -> RenderIntent:
    mapping = {
        "pending": RenderState.ACKNOWLEDGED,
        "queued": RenderState.ACKNOWLEDGED,
        "processing": RenderState.RUNNING,
        "running": RenderState.RUNNING,
        "completed": RenderState.COMPLETED,
        "failed": RenderState.FAILED_FINAL,
    }
    if provider_job_id and not provider_status:
        state = RenderState.RECONCILE_REQUIRED
    else:
        state = mapping.get((provider_status or "").lower(), RenderState.RECONCILE_REQUIRED)
    return RenderIntent(**{**intent.__dict__, "state": state, "provider_job_id": provider_job_id or intent.provider_job_id})
