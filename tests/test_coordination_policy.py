import pytest

from src.coordination.policy import CapabilityGrant, CapabilityPolicy, PolicyDenied, Sensitivity


AGENT = "motion://agent/a"


def policy():
    return CapabilityPolicy([
        CapabilityGrant(
            agent_id=AGENT,
            operation="WRITE",
            resource_scope=("tree:src/coordination", "contract:coordination-event"),
            sensitivity_ceiling=Sensitivity.CONFIDENTIAL,
        )
    ])


def test_matching_agent_operation_scope_and_sensitivity_is_allowed():
    grant = policy().authorize(
        agent_id=AGENT,
        operation="WRITE",
        resource_uri="file:src/coordination/events.py",
        sensitivity="INTERNAL",
    )
    assert grant.agent_id == AGENT


@pytest.mark.parametrize("kwargs", [
    {"agent_id": "motion://agent/b", "operation": "WRITE", "resource_uri": "file:src/coordination/events.py", "sensitivity": "INTERNAL"},
    {"agent_id": AGENT, "operation": "DELETE", "resource_uri": "file:src/coordination/events.py", "sensitivity": "INTERNAL"},
    {"agent_id": AGENT, "operation": "WRITE", "resource_uri": "file:src/avatar/private.py", "sensitivity": "INTERNAL"},
    {"agent_id": AGENT, "operation": "WRITE", "resource_uri": "file:src/coordination/events.py", "sensitivity": "RESTRICTED"},
    {"agent_id": AGENT, "operation": "WRITE", "resource_uri": "file:src/coordination/events.py", "sensitivity": "TOP_SECRET"},
])
def test_policy_denies_unknown_or_out_of_scope_requests(kwargs):
    with pytest.raises(PolicyDenied):
        policy().authorize(**kwargs)


def test_empty_policy_is_default_deny():
    with pytest.raises(PolicyDenied):
        CapabilityPolicy().authorize(
            agent_id=AGENT,
            operation="WRITE",
            resource_uri="contract:coordination-event",
            sensitivity="PUBLIC",
        )
