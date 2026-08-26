from dataclasses import replace

import pytest

from src.coordination.bus import InMemoryReferenceBus
from src.coordination.events import CoordinationEvent


def make_event(**overrides):
    data = dict(
        event_type="task.started",
        aggregate_type="task",
        aggregate_id="motion://task/t-1",
        project_id="motion://project/MOTION.OS",
        agent_id="motion://agent/test-agent",
        session_id="motion://session/test-session",
        correlation_id="work-1",
        payload={"task": "t-1"},
    )
    data.update(overrides)
    return CoordinationEvent(**data)


def test_event_hash_is_self_verified_and_stable_for_same_content():
    event = make_event()
    rebuilt = replace(event)
    assert len(event.provenance_hash) == 64
    assert rebuilt.provenance_hash == event.provenance_hash


def test_append_is_idempotent_by_event_id_and_hash():
    bus = InMemoryReferenceBus()
    event = make_event()
    first = bus.append_checked(event)
    second = bus.append_checked(event)
    assert first.offset == 1
    assert not first.duplicate
    assert second.offset == 1
    assert second.duplicate
    assert len(bus.read()) == 1


def test_same_event_id_with_different_content_fails_closed():
    bus = InMemoryReferenceBus()
    event = make_event()
    bus.append(event)
    with pytest.raises(ValueError, match="event_id collision"):
        bus.append(replace(event, payload={"task": "tampered"}, provenance_hash=""))


def test_consumer_offsets_are_monotonic_and_isolated():
    bus = InMemoryReferenceBus()
    bus.append(make_event(aggregate_id="motion://task/a", correlation_id="a"))
    bus.append(make_event(aggregate_id="motion://task/b", correlation_id="b"))

    assert [offset for offset, _ in bus.poll("consumer-a")] == [1, 2]
    bus.acknowledge("consumer-a", 1)
    assert [offset for offset, _ in bus.poll("consumer-a")] == [2]
    assert [offset for offset, _ in bus.poll("consumer-b")] == [1, 2]

    with pytest.raises(ValueError, match="rewind"):
        bus.acknowledge("consumer-a", 0)


def test_read_is_ordered_and_bounded():
    bus = InMemoryReferenceBus()
    for i in range(5):
        bus.append(make_event(aggregate_id=f"motion://task/{i}", correlation_id=f"c-{i}"))

    page = bus.read(after_offset=1, limit=2)
    assert [offset for offset, _ in page] == [2, 3]


def test_reference_bus_never_claims_multi_host_authority():
    bus = InMemoryReferenceBus()
    assert bus.authority_level == "REFERENCE_TEST_ONLY"
