from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable

from .resources import canonicalize_resource, resource_overlap


class Sensitivity(IntEnum):
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    RESTRICTED = 3


@dataclass(frozen=True, slots=True)
class CapabilityGrant:
    agent_id: str
    operation: str
    resource_scope: tuple[str, ...]
    sensitivity_ceiling: Sensitivity

    def __post_init__(self) -> None:
        if not self.agent_id.startswith("motion://agent/"):
            raise ValueError("agent_id must be canonical")
        if not self.operation or self.operation.upper() != self.operation:
            raise ValueError("operation must be upper-case")
        if not self.resource_scope:
            raise ValueError("resource_scope is required")
        for scope in self.resource_scope:
            canonicalize_resource(scope)


class PolicyDenied(PermissionError):
    pass


class CapabilityPolicy:
    """Default-deny reference authorization policy for protected coordination commands."""

    def __init__(self, grants: Iterable[CapabilityGrant] = ()) -> None:
        self._grants = tuple(grants)

    def authorize(
        self,
        *,
        agent_id: str,
        operation: str,
        resource_uri: str,
        sensitivity: str,
    ) -> CapabilityGrant:
        try:
            requested_sensitivity = Sensitivity[sensitivity]
        except KeyError as exc:
            raise PolicyDenied("unknown sensitivity fails closed") from exc
        requested = canonicalize_resource(resource_uri)
        for grant in self._grants:
            if grant.agent_id != agent_id or grant.operation != operation:
                continue
            if requested_sensitivity > grant.sensitivity_ceiling:
                continue
            if any(resource_overlap(canonicalize_resource(scope), requested) for scope in grant.resource_scope):
                return grant
        raise PolicyDenied(
            f"no grant for agent={agent_id} operation={operation} resource={requested.uri} sensitivity={sensitivity}"
        )
