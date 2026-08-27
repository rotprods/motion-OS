from datetime import timedelta
import random

import pytest

from src.coordination.leases import LeaseConflict, ReferenceLeaseAuthority, StaleFencingToken


RESOURCE = "contract:shared-runtime"


def test_500_contention_takeover_rounds_never_accept_stale_generation():
    rng = random.Random(20260827)
    authority = ReferenceLeaseAuthority()
    previous = None

    for round_no in range(500):
        agent = f"motion://agent/a{round_no % 3}"
        session = f"motion://session/s{round_no}"

        if previous is None:
            current = authority.acquire(
                resource_uri=RESOURCE,
                scope="WRITE",
                agent_id=agent,
                session_id=session,
                ttl_seconds=1,
            )
        else:
            takeover_at = previous.expires_at + timedelta(milliseconds=rng.randint(1, 1000))
            current = authority.acquire(
                resource_uri=RESOURCE,
                scope="WRITE",
                agent_id=agent,
                session_id=session,
                ttl_seconds=1,
                now=takeover_at,
            )
            assert current.fencing_token == previous.fencing_token + 1
            with pytest.raises(StaleFencingToken):
                authority.assert_write_authorized(
                    previous.lease_id,
                    previous.fencing_token,
                    RESOURCE,
                    now=takeover_at,
                )
        previous = current


def test_live_lease_rejects_all_competing_agents():
    authority = ReferenceLeaseAuthority()
    current = authority.acquire(
        resource_uri=RESOURCE,
        scope="EXCLUSIVE_WRITE",
        agent_id="motion://agent/owner",
        session_id="motion://session/owner",
        ttl_seconds=60,
    )
    for i in range(100):
        with pytest.raises(LeaseConflict):
            authority.acquire(
                resource_uri=RESOURCE,
                scope="WRITE",
                agent_id=f"motion://agent/competitor-{i}",
                session_id=f"motion://session/competitor-{i}",
                ttl_seconds=60,
                now=current.acquired_at + timedelta(milliseconds=i + 1),
            )
