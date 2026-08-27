from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .conflicts import ConflictClass, ConflictFinding, classify_conflict
from .event_store import CoordinationEventStore
from .events import CoordinationEvent, ProvenanceRef
from .leases import Lease, ReferenceLeaseAuthority


PROJECT_ID = "motion://project/MOTION.OS"


@dataclass(frozen=True, slots=True)
class ClaimPreflight:
    finding: ConflictFinding
    approved: bool


@dataclass(frozen=True, slots=True)
class ClaimResult:
    lease: Lease
    command_event_id: str
    outcome_event_id: str


class AgentCoordinationSDK:
    """Small fail-closed orchestration surface for developer/runtime agents.

    This SDK composes existing authority-neutral primitives. It does not upgrade
    the authority level of injected stores; reference stores remain local/test
    semantics even when accessed through this interface.
    """

    def __init__(self, *, event_store: CoordinationEventStore, lease_authority: ReferenceLeaseAuthority) -> None:
        self._events = event_store
        self._leases = lease_authority

    def preflight_claim(
        self,
        *,
        requested_scopes: Iterable[str],
        requested_authority: Iterable[str] = (),
        dependency_edges: Mapping[str, Iterable[str]] | None = None,
    ) -> ClaimPreflight:
        active = self._leases.active()
        active_scopes = tuple(lease.resource_uri for lease in active)
        active_authority = tuple(
            lease.resource_uri for lease in active if lease.resource_uri.startswith("capability:")
        )
        finding = classify_conflict(
            requested_scopes=requested_scopes,
            active_scopes=active_scopes,
            dependency_edges=dependency_edges,
            requested_authority=requested_authority,
            active_authority=active_authority,
        )
        # Claiming protected write work is conservative: any known overlap/risk
        # requires an explicit coordination decision or a narrower scope.
        return ClaimPreflight(finding=finding, approved=finding.classification == ConflictClass.NONE)

    def claim(
        self,
        *,
        agent_id: str,
        session_id: str,
        workstream_id: str,
        resource_uri: str,
        scope: str,
        correlation_id: str,
        idempotency_key: str,
        ttl_seconds: int = 300,
        expected_revision: int | None = None,
        provenance: tuple[ProvenanceRef, ...] | None = None,
    ) -> ClaimResult:
        preflight = self.preflight_claim(
            requested_scopes=(resource_uri,),
            requested_authority=(resource_uri,) if resource_uri.startswith("capability:") else (),
        )
        if not preflight.approved:
            raise RuntimeError(
                f"claim blocked by {preflight.finding.classification.value}: {preflight.finding.details}"
            )

        aggregate_type = "workstream"
        aggregate_id = workstream_id
        current = self._events.aggregate_revision(aggregate_type, aggregate_id)
        refs = provenance or (ProvenanceRef("coordination-sdk", "claim"),)
        command = CoordinationEvent(
            event_type="WORK_CLAIM_REQUESTED",
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            aggregate_revision=current + 1,
            expected_revision=current,
            project_id=PROJECT_ID,
            agent_id=agent_id,
            session_id=session_id,
            workstream_id=workstream_id,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            resource_scope=(resource_uri,),
            payload={"resource_uri": resource_uri, "scope": scope, "ttl_seconds": ttl_seconds},
            provenance=refs,
        )
        stored_command = self._events.append(command)
        if stored_command.duplicate:
            raise RuntimeError("claim command replay requires outcome reconciliation before retry")

        lease: Lease | None = None
        try:
            lease = self._leases.acquire(
                resource_uri=resource_uri,
                scope=scope,
                agent_id=agent_id,
                session_id=session_id,
                ttl_seconds=ttl_seconds,
                expected_revision=expected_revision,
            )
            current = self._events.aggregate_revision(aggregate_type, aggregate_id)
            outcome = CoordinationEvent(
                event_type="WORK_CLAIMED",
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                aggregate_revision=current + 1,
                expected_revision=current,
                project_id=PROJECT_ID,
                agent_id=agent_id,
                session_id=session_id,
                workstream_id=workstream_id,
                correlation_id=correlation_id,
                causation_id=command.event_id,
                parent_event_ids=(command.event_id,),
                idempotency_key=f"{idempotency_key}:outcome",
                resource_scope=(lease.resource_uri,),
                payload={
                    "resource_uri": lease.resource_uri,
                    "scope": lease.scope,
                    "lease_id": lease.lease_id,
                    "fencing_token": lease.fencing_token,
                },
                provenance=refs,
            )
            self._events.append(outcome)
        except Exception as exc:
            compensation = "NOT_REQUIRED"
            if lease is not None:
                try:
                    self._leases.release(lease.lease_id, lease.fencing_token)
                    compensation = "LEASE_RELEASED"
                except Exception:
                    # Do not hide a failed compensation. Recovery must reconcile
                    # the lease authority before any retry.
                    compensation = "LEASE_RELEASE_FAILED_RECONCILE_REQUIRED"
            current = self._events.aggregate_revision(aggregate_type, aggregate_id)
            failure = CoordinationEvent(
                event_type="WORK_CLAIM_FAILED",
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                aggregate_revision=current + 1,
                expected_revision=current,
                project_id=PROJECT_ID,
                agent_id=agent_id,
                session_id=session_id,
                workstream_id=workstream_id,
                correlation_id=correlation_id,
                causation_id=command.event_id,
                parent_event_ids=(command.event_id,),
                idempotency_key=f"{idempotency_key}:failed",
                resource_scope=(resource_uri,),
                payload={
                    "resource_uri": resource_uri,
                    "error_type": type(exc).__name__,
                    "compensation": compensation,
                },
                provenance=refs,
            )
            self._events.append(failure)
            raise

        assert lease is not None
        return ClaimResult(lease=lease, command_event_id=command.event_id, outcome_event_id=outcome.event_id)

    def checkpoint(
        self,
        *,
        agent_id: str,
        session_id: str,
        workstream_id: str,
        correlation_id: str,
        idempotency_key: str,
        summary: str,
        evidence_refs: Iterable[str] = (),
    ) -> CoordinationEvent:
        current = self._events.aggregate_revision("workstream", workstream_id)
        event = CoordinationEvent(
            event_type="SESSION_CHECKPOINTED",
            aggregate_type="workstream",
            aggregate_id=workstream_id,
            aggregate_revision=current + 1,
            expected_revision=current,
            project_id=PROJECT_ID,
            agent_id=agent_id,
            session_id=session_id,
            workstream_id=workstream_id,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            payload={"summary": summary},
            evidence_refs=tuple(sorted(set(evidence_refs))),
            provenance=(ProvenanceRef("coordination-sdk", "checkpoint"),),
        )
        stored = self._events.append(event)
        return stored.event

    def release(self, *, lease_id: str, fencing_token: int) -> Lease:
        return self._leases.release(lease_id, fencing_token)
