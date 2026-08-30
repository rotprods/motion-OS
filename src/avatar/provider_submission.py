from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Protocol

from .render_guard import (
    RenderIntent,
    RenderState,
    SpendPolicy,
    can_submit,
    make_render_intent_id,
    reconcile_state,
)
from .transactional_store import RenderStateStore


class PaidVideoProviderPort(Protocol):
    """Network/provider capability injected by an outer runtime.

    Implementations are untrusted I/O boundaries. This core module never performs
    network access itself and never assumes provider exceptions mean rejection.
    """

    provider_id: str

    def submit(self, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


class SubmissionBlocked(RuntimeError):
    """The provider must not be called for the requested submission."""


class SubmissionConflict(RuntimeError):
    """Durable state changed while a provider outcome was being reconciled."""


@dataclass(frozen=True)
class SubmissionOutcome:
    intent: RenderIntent
    provider_id: str
    request_sha256: str
    callback_id: str
    provider_called: bool
    failure_type: str | None = None

    @property
    def requires_reconciliation(self) -> bool:
        return self.intent.state in {RenderState.SUBMITTED, RenderState.RECONCILE_REQUIRED}


def _canonical_json(value: Mapping[str, Any]) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise SubmissionBlocked("provider request must be finite JSON data") from exc


def _request_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _prepare_request(intent: RenderIntent, request_payload: Mapping[str, Any], provider_id: str) -> dict[str, Any]:
    if not isinstance(intent, RenderIntent):
        raise SubmissionBlocked("intent must be a RenderIntent")
    if intent.state != RenderState.AUTHORIZED:
        raise SubmissionBlocked("provider submission requires AUTHORIZED intent")
    if not isinstance(provider_id, str) or not provider_id.strip() or len(provider_id) > 64:
        raise SubmissionBlocked("provider_id malformed")
    if not isinstance(request_payload, Mapping):
        raise SubmissionBlocked("provider request must be a mapping")

    payload = dict(request_payload)
    script = payload.get("script")
    if not isinstance(script, str) or not script.strip():
        raise SubmissionBlocked("provider request script required")
    expected_id = make_render_intent_id(
        content_id=intent.content_id,
        profile_id=intent.profile_id,
        script=script,
        provider=provider_id,
    )
    if expected_id != intent.intent_id:
        raise SubmissionBlocked("provider request is not bound to render intent identity")

    callback_id = payload.get("callbackId")
    if callback_id is not None and callback_id != intent.intent_id:
        raise SubmissionBlocked("provider callbackId must equal render intent ID")
    payload["callbackId"] = intent.intent_id

    # Serialization is performed before the durable SUBMITTED transition so a
    # malformed request can never consume the one-way submission gate.
    _canonical_json(payload)
    return payload


def _put_with_fresh_lease(
    *,
    store: RenderStateStore,
    intent: RenderIntent,
    owner_id: str,
    ttl_s: float,
    expected_current: RenderIntent | None,
) -> None:
    lease = store.acquire_lease(intent.intent_id, owner_id, ttl_s=ttl_s)
    try:
        current = store.get_intent(intent.intent_id)
        if expected_current is None:
            if current is not None:
                raise SubmissionConflict("unexpected persisted render intent")
        elif current != expected_current:
            raise SubmissionConflict("persisted render intent changed during submission")
        store.put_intent(intent, lease)
    finally:
        store.release_lease(lease)


def _persist_provider_outcome(
    *,
    store: RenderStateStore,
    submitted: RenderIntent,
    desired: RenderIntent,
    owner_id: str,
    ttl_s: float,
) -> None:
    # Reacquire after network I/O. We deliberately do not hold a DB/lease across
    # the provider call. The durable SUBMITTED state fences duplicate spend while
    # the external outcome is unknown.
    _put_with_fresh_lease(
        store=store,
        intent=desired,
        owner_id=owner_id,
        ttl_s=ttl_s,
        expected_current=submitted,
    )


def submit_paid_render(
    *,
    intent: RenderIntent,
    request_payload: Mapping[str, Any],
    provider: PaidVideoProviderPort,
    store: RenderStateStore,
    policy: SpendPolicy,
    spent_today: float,
    concurrent_renders: int,
    owner_id: str,
    lease_ttl_s: float = 30.0,
) -> SubmissionOutcome:
    """Submit exactly one paid render through a durable fail-closed boundary.

    State transition:
      AUTHORIZED/FAILED_RETRYABLE -> durable SUBMITTED -> provider call ->
      ACKNOWLEDGED/RUNNING/COMPLETED or RECONCILE_REQUIRED.

    Any exception after the durable SUBMITTED write is treated as an unknown
    provider outcome. The exception *type* may be returned for diagnostics, but
    raw provider exception messages are never persisted or returned here because
    they can contain secrets/PII/untrusted provider data.
    """

    if not isinstance(provider, PaidVideoProviderPort):
        # Protocols with data attributes are not safely runtime-checkable; keep
        # the error deterministic via explicit structural validation below.
        pass
    provider_id = getattr(provider, "provider_id", None)
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise SubmissionBlocked("provider port must declare provider_id")
    if not isinstance(store, RenderStateStore):
        # Same runtime-protocol caveat as above; concrete methods are validated by
        # use and any missing method fails before the provider call.
        pass
    if not isinstance(policy, SpendPolicy):
        raise SubmissionBlocked("policy must be a SpendPolicy")
    if not isinstance(owner_id, str) or not owner_id.strip() or len(owner_id) > 256:
        raise SubmissionBlocked("owner_id malformed")
    if isinstance(lease_ttl_s, bool) or not isinstance(lease_ttl_s, (int, float)) or lease_ttl_s <= 0:
        raise SubmissionBlocked("lease_ttl_s must be positive")

    payload = _prepare_request(intent, request_payload, provider_id)
    request_sha = _request_sha256(payload)

    # Phase 1: lock, verify exact current authority, persist SUBMITTED, release.
    lease = store.acquire_lease(intent.intent_id, owner_id, ttl_s=float(lease_ttl_s))
    try:
        persisted = store.get_intent(intent.intent_id)
        if persisted is None:
            raise SubmissionBlocked("render intent must be durably authorized before provider submission")

        if persisted.state == RenderState.AUTHORIZED:
            if persisted != intent or not can_submit(intent, {}):
                raise SubmissionBlocked("authorized intent does not match durable submission authority")
        elif persisted.state == RenderState.FAILED_RETRYABLE:
            if not can_submit(
                intent,
                {intent.intent_id: persisted},
                policy=policy,
                spent_today=spent_today,
                concurrent_renders=concurrent_renders,
            ):
                raise SubmissionBlocked("retry is not an exact live-budget-authorized transition")
        else:
            raise SubmissionBlocked(f"render intent state {persisted.state.value} requires reconciliation before submit")

        submitted = RenderIntent(**{**intent.__dict__, "state": RenderState.SUBMITTED, "provider_job_id": None})
        store.put_intent(submitted, lease)
    finally:
        store.release_lease(lease)

    # Phase 2: external capability. SUBMITTED is already durable, so a process
    # death or ambiguous timeout cannot fall back to AUTHORIZED and spend twice.
    try:
        raw_result = provider.submit(payload)
    except Exception as exc:
        desired = RenderIntent(**{**submitted.__dict__, "state": RenderState.RECONCILE_REQUIRED})
        _persist_provider_outcome(
            store=store,
            submitted=submitted,
            desired=desired,
            owner_id=owner_id,
            ttl_s=float(lease_ttl_s),
        )
        return SubmissionOutcome(
            intent=desired,
            provider_id=provider_id,
            request_sha256=request_sha,
            callback_id=intent.intent_id,
            provider_called=True,
            failure_type=type(exc).__name__,
        )

    # Provider output is UNTRUSTED_DATA. Creation acceptance must include a
    # bounded job identity; otherwise the only safe state is reconciliation.
    job_id: str | None = None
    status: str | None = None
    if isinstance(raw_result, Mapping):
        candidate = raw_result.get("id") or raw_result.get("video_id")
        if isinstance(candidate, str) and candidate.strip() and len(candidate) <= 256:
            job_id = candidate
        candidate_status = raw_result.get("status")
        if isinstance(candidate_status, str) and len(candidate_status) <= 64:
            status = candidate_status

    if job_id is None:
        desired = RenderIntent(**{**submitted.__dict__, "state": RenderState.RECONCILE_REQUIRED})
    else:
        desired = reconcile_state(submitted, status, job_id)

    _persist_provider_outcome(
        store=store,
        submitted=submitted,
        desired=desired,
        owner_id=owner_id,
        ttl_s=float(lease_ttl_s),
    )
    return SubmissionOutcome(
        intent=desired,
        provider_id=provider_id,
        request_sha256=request_sha,
        callback_id=intent.intent_id,
        provider_called=True,
    )
