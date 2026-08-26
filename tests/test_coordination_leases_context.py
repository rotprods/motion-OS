from datetime import datetime, timedelta, timezone

import pytest

from src.coordination.context import ContextPackCompiler, ContextSourceRef
from src.coordination.leases import (
    LeaseConflict,
    ReferenceCASStore,
    ReferenceLeaseAuthority,
    RevisionConflict,
    StaleFencingToken,
    resources_overlap,
)


UTC = timezone.utc


def test_resource_scope_overlap_for_tree_and_file():
    assert resources_overlap("tree:src/content/**", "file:src/content/factory.py")
    assert resources_overlap("tree:src/**", "tree:src/content/**")
    assert not resources_overlap("tree:src/content/**", "file:src/avatar/render.py")
    assert resources_overlap("contract:avatar-handoff", "contract:avatar-handoff")
    assert not resources_overlap("contract:avatar-handoff", "contract:studio-entry")


def test_disjoint_writers_can_work_concurrently():
    authority = ReferenceLeaseAuthority()
    now = datetime(2026, 8, 26, 19, 0, tzinfo=UTC)
    a = authority.acquire(
        resource_uri="tree:src/content/**", scope="WRITE",
        agent_id="motion://agent/a", session_id="motion://session/a",
        now=now,
    )
    b = authority.acquire(
        resource_uri="tree:runtime/remotion/**", scope="WRITE",
        agent_id="motion://agent/b", session_id="motion://session/b",
        now=now,
    )
    assert a.fencing_token == 1
    assert b.fencing_token == 1


def test_overlapping_writer_fails_before_mutation():
    authority = ReferenceLeaseAuthority()
    now = datetime(2026, 8, 26, 19, 0, tzinfo=UTC)
    authority.acquire(
        resource_uri="tree:src/content/**", scope="WRITE",
        agent_id="motion://agent/a", session_id="motion://session/a",
        now=now,
    )
    with pytest.raises(LeaseConflict):
        authority.acquire(
            resource_uri="file:src/content/content_factory.py", scope="WRITE",
            agent_id="motion://agent/b", session_id="motion://session/b",
            now=now,
        )


def test_expired_writer_can_be_taken_over_and_stale_owner_is_rejected():
    authority = ReferenceLeaseAuthority()
    t0 = datetime(2026, 8, 26, 19, 0, tzinfo=UTC)
    old = authority.acquire(
        resource_uri="contract:avatar-handoff", scope="EXCLUSIVE_WRITE",
        agent_id="motion://agent/a", session_id="motion://session/a",
        ttl_seconds=10, now=t0,
    )
    t1 = t0 + timedelta(seconds=11)
    new = authority.acquire(
        resource_uri="contract:avatar-handoff", scope="EXCLUSIVE_WRITE",
        agent_id="motion://agent/b", session_id="motion://session/b",
        ttl_seconds=10, now=t1,
    )
    assert new.fencing_token == old.fencing_token + 1
    with pytest.raises(StaleFencingToken):
        authority.assert_write_authorized(old.lease_id, old.fencing_token, "contract:avatar-handoff", now=t1)
    authority.assert_write_authorized(new.lease_id, new.fencing_token, "contract:avatar-handoff", now=t1)


def test_cas_prevents_stale_revision_overwrite():
    store = ReferenceCASStore()
    v1 = store.compare_and_set("contract:studio-entry", {"version": 1}, expected_revision=0)
    assert v1.revision == 1
    with pytest.raises(RevisionConflict):
        store.compare_and_set("contract:studio-entry", {"version": 2}, expected_revision=0)
    v2 = store.compare_and_set("contract:studio-entry", {"version": 2}, expected_revision=1)
    assert v2.revision == 2


def test_context_pack_is_deterministic_sealed_and_invalidates_on_source_change():
    compiler = ContextPackCompiler()
    generated = datetime(2026, 8, 26, 19, 0, tzinfo=UTC)
    stale_after = generated + timedelta(hours=1)
    kwargs = dict(
        context_pack_id="cp-1",
        project_id="motion://project/MOTION.OS",
        agent_id="motion://agent/a",
        session_id="motion://session/a",
        generated_at=generated,
        stale_after=stale_after,
        main_sha="abcdef1234567",
        projection_version=7,
        projection_hash="a" * 64,
        goal_summary="brief to professional master",
        active_prs=[{"number": 37}, {"number": 34}],
        allowed_write_scopes=["contract:avatar-handoff"],
        source_refs=[ContextSourceRef(uri="git:AGENTS.md", revision="r1", sha256="b" * 64)],
    )
    pack1 = compiler.compile(**kwargs)
    pack2 = compiler.compile(**kwargs)
    assert pack1.seal_sha256 == pack2.seal_sha256
    assert pack1.verify_seal()
    assert not pack1.is_stale(
        now=generated + timedelta(minutes=10),
        main_sha="abcdef1234567",
        projection_version=7,
        projection_hash="a" * 64,
        current_source_revisions={"git:AGENTS.md": "r1"},
    )
    assert pack1.is_stale(
        now=generated + timedelta(minutes=10),
        main_sha="abcdef1234567",
        projection_version=7,
        projection_hash="a" * 64,
        current_source_revisions={"git:AGENTS.md": "r2"},
    )


def test_context_pack_invalidates_after_main_merge_or_projection_change():
    compiler = ContextPackCompiler()
    generated = datetime(2026, 8, 26, 19, 0, tzinfo=UTC)
    pack = compiler.compile(
        context_pack_id="cp-1",
        project_id="motion://project/MOTION.OS",
        agent_id="motion://agent/a",
        session_id="motion://session/a",
        generated_at=generated,
        stale_after=generated + timedelta(hours=1),
        main_sha="main-old",
        projection_version=1,
        projection_hash="c" * 64,
        goal_summary="goal",
    )
    assert pack.is_stale(
        now=generated + timedelta(minutes=1),
        main_sha="main-new",
        projection_version=1,
        projection_hash="c" * 64,
        current_source_revisions={},
    )
    assert pack.is_stale(
        now=generated + timedelta(minutes=1),
        main_sha="main-old",
        projection_version=2,
        projection_hash="d" * 64,
        current_source_revisions={},
    )
