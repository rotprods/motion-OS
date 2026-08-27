from src.coordination.delivery import ReferenceDeliveryProcessor
from src.coordination.events import CoordinationEvent, ProvenanceRef


def event(event_type="TASK_STARTED"):
    return CoordinationEvent(
        event_type=event_type,
        aggregate_type="task",
        aggregate_id="motion://task/delivery",
        aggregate_revision=1,
        expected_revision=0,
        project_id="motion://project/MOTION.OS",
        agent_id="motion://agent/test",
        session_id="motion://session/test",
        correlation_id="motion://work/delivery",
        idempotency_key=f"idem:{event_type}",
        payload={"value": 1},
        provenance=(ProvenanceRef("test", "delivery"),),
    )


def test_duplicate_delivery_has_one_logical_effect():
    calls = []
    processor = ReferenceDeliveryProcessor(
        consumer_id="consumer-a",
        handlers={"TASK_STARTED": lambda e: calls.append(e.event_id) or e.payload_hash},
    )
    e = event()
    first = processor.process(e)
    second = processor.process(e)
    assert first.applied is True
    assert second.duplicate is True
    assert calls == [e.event_id]


def test_unknown_event_is_quarantined_not_acknowledged():
    processor = ReferenceDeliveryProcessor(consumer_id="consumer-a", handlers={})
    e = event("UNKNOWN_EVENT")
    outcome = processor.process(e)
    assert outcome.quarantined is True
    assert not processor.inbox.processed(consumer_id="consumer-a", event_id=e.event_id)
    assert processor.quarantine()[0].event_id == e.event_id


def test_handler_failure_can_be_retried_after_handler_repair():
    state = {"fail": True}
    def handler(e):
        if state["fail"]:
            raise RuntimeError("boom")
        return e.payload_hash

    processor = ReferenceDeliveryProcessor(consumer_id="consumer-a", handlers={"TASK_STARTED": handler})
    e = event()
    assert processor.process(e).quarantined is True
    state["fail"] = False
    outcome = processor.retry_quarantined(e)
    assert outcome.applied is True
    assert processor.quarantine() == ()
