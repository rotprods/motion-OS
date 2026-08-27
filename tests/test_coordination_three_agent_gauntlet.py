from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from src.coordination.event_store import InMemoryReferenceEventStore
from src.coordination.leases import ReferenceLeaseAuthority, StaleFencingToken
from src.coordination.observability import CoordinationMetrics
from src.coordination.replay import ReplayVerifier
from src.coordination.sdk import AgentCoordinationSDK


BASE = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def test_three_agents_conflict_crash_takeover_and_replay_are_safe():
    store = InMemoryReferenceEventStore()
    leases = ReferenceLeaseAuthority()
    metrics = CoordinationMetrics()
    a = AgentCoordinationSDK(event_store=store, lease_authority=leases)
    b = AgentCoordinationSDK(event_store=store, lease_authority=leases)
    c = AgentCoordinationSDK(event_store=store, lease_authority=leases)

    first = a.claim(
        agent_id="motion://agent/a",
        session_id="motion://session/a",
        workstream_id="motion://workstream/a",
        resource_uri="contract:avatar-handoff",
        scope="WRITE",
        correlation_id="motion://work/a",
        idempotency_key="gauntlet-a",
        ttl_seconds=10,
    )

    assert b.preflight_claim(requested_scopes=("contract:avatar-handoff",)).approved is False
    assert c.preflight_claim(requested_scopes=("contract:avatar-handoff",)).approved is False

    # Simulate A disappearing and its lease expiring. A new authority generation
    # must be issued to the taker; the old generation may never write again.
    takeover_time = first.lease.expires_at + timedelta(seconds=1)
    second = leases.acquire(
        resource_uri="contract:avatar-handoff",
        scope="WRITE",
        agent_id="motion://agent/b",
        session_id="motion://session/b",
        ttl_seconds=10,
        now=takeover_time,
    )
    assert second.fencing_token == first.lease.fencing_token + 1

    with pytest.raises(StaleFencingToken):
        leases.assert_write_authorized(
            first.lease.lease_id,
            first.lease.fencing_token,
            "contract:avatar-handoff",
            now=takeover_time,
        )
    metrics.stale_writer_rejected()

    events = tuple(item.event for item in store.read())
    verifier = ReplayVerifier()
    left = verifier.rebuild(events, projection_version=1)
    right = verifier.rebuild(events, projection_version=1)
    assert verifier.equivalent(left, right)
    assert left.state_snapshot.event_watermark == len(events)

    health = metrics.snapshot(event_store=store, lease_authority=leases)
    assert health.stale_writer_rejections == 1
    assert health.replay_failures == 0


def test_event_order_change_changes_replay_identity():
    store = InMemoryReferenceEventStore()
    leases = ReferenceLeaseAuthority()
    client = AgentCoordinationSDK(event_store=store, lease_authority=leases)
    client.claim(
        agent_id="motion://agent/a",
        session_id="motion://session/a",
        workstream_id="motion://workstream/a",
        resource_uri="contract:coordination-event",
        scope="WRITE",
        correlation_id="motion://work/a",
        idempotency_key="ordered-a",
    )
    events = tuple(item.event for item in store.read())
    assert len(events) == 2
    verifier = ReplayVerifier()
    canonical = verifier.rebuild(events)
    # Reversing causal history must fail, not silently generate another valid state.
    with pytest.raises(Exception):
        verifier.rebuild(tuple(reversed(events)))
    assert canonical.graph_snapshot.verify_hash()
