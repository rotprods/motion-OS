from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any
import hashlib
import json


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


@dataclass(frozen=True)
class SpendPolicy:
    max_credits_per_render: float
    max_credits_per_day: float
    max_concurrent_renders: int
    max_retries: int = 1


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
    if not explicit_authorization:
        raise PermissionError("explicit render authorization required")
    if not preflight_ok:
        raise ValueError("preflight must pass before render authorization")
    if concurrent_renders >= policy.max_concurrent_renders:
        raise RuntimeError("concurrent render limit reached")
    if estimated_credits is not None:
        if estimated_credits > policy.max_credits_per_render:
            raise RuntimeError("per-render credit budget exceeded")
        if spent_today + estimated_credits > policy.max_credits_per_day:
            raise RuntimeError("daily credit budget exceeded")
    script_hash = hash_script(script)
    return RenderIntent(
        intent_id=make_render_intent_id(content_id=content_id, profile_id=profile_id, script=script),
        content_id=content_id,
        profile_id=profile_id,
        script_hash=script_hash,
        state=RenderState.AUTHORIZED,
        estimated_credits=estimated_credits,
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
    if intent.retry_count >= policy.max_retries:
        return RenderIntent(**{**intent.__dict__, "state": RenderState.FAILED_FINAL})
    return RenderIntent(**{**intent.__dict__, "state": RenderState.AUTHORIZED, "retry_count": intent.retry_count + 1})


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
