from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .render_guard import RenderIntent, RenderState, reconcile_state


class FaultMode(str, Enum):
    TIMEOUT_BEFORE_ACCEPT = "TIMEOUT_BEFORE_ACCEPT"
    TIMEOUT_AFTER_ACCEPT = "TIMEOUT_AFTER_ACCEPT"
    PROVIDER_5XX = "PROVIDER_5XX"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    COMPLETED_WITHOUT_ASSET = "COMPLETED_WITHOUT_ASSET"
    DUPLICATE_CALLBACK = "DUPLICATE_CALLBACK"


@dataclass(frozen=True)
class FaultOutcome:
    state: RenderState
    retry_allowed: bool
    reconcile_required: bool
    reason: str


def simulate_fault(intent: RenderIntent, mode: FaultMode) -> FaultOutcome:
    if mode == FaultMode.TIMEOUT_BEFORE_ACCEPT:
        return FaultOutcome(RenderState.FAILED_RETRYABLE, True, False, "no provider acknowledgement observed")
    if mode == FaultMode.TIMEOUT_AFTER_ACCEPT:
        return FaultOutcome(RenderState.RECONCILE_REQUIRED, False, True, "provider may have accepted paid job")
    if mode == FaultMode.PROVIDER_5XX:
        return FaultOutcome(RenderState.RECONCILE_REQUIRED, False, True, "ambiguous provider failure; reconcile first")
    if mode == FaultMode.MALFORMED_RESPONSE:
        return FaultOutcome(RenderState.RECONCILE_REQUIRED, False, True, "response cannot establish provider state")
    if mode == FaultMode.COMPLETED_WITHOUT_ASSET:
        return FaultOutcome(RenderState.RECONCILE_REQUIRED, False, True, "completed state missing asset reference")
    if mode == FaultMode.DUPLICATE_CALLBACK:
        return FaultOutcome(intent.state, False, False, "idempotent callback should not change terminal state")
    raise ValueError(f"unsupported fault mode: {mode}")


def apply_provider_snapshot(intent: RenderIntent, snapshot: dict[str, Any]) -> RenderIntent:
    """Normalize a provider snapshot without inventing a retryable state."""
    return reconcile_state(
        intent,
        provider_status=snapshot.get("status"),
        provider_job_id=snapshot.get("id") or snapshot.get("video_id"),
    )
