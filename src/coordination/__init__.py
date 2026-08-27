"""MOTION.OS multi-agent coordination primitives.

The package defines authority-neutral contracts. In-memory implementations are
reference/test backends only; production multi-host authority is an optional
promotion stage, not a requirement for local/reference verification.
"""

from .bus import CoordinationBus, InMemoryReferenceBus
from .conflicts import ConflictClass, ConflictFinding, classify_conflict
from .context import ContextPack, ContextPackCompiler, ContextSourceRef
from .cos_adapter import COS_BASELINE_COMMIT, CosProjectionBundle, CosShadowAdapter
from .event_semantics import EventRole, event_role, outcome_satisfies_command
from .event_store import (
    CoordinationEventStore,
    IdempotencyConflict,
    InMemoryReferenceEventStore,
    RevisionConflict as AggregateRevisionConflict,
    StateSnapshot,
    StoredEvent,
)
from .events import CoordinationEvent, ProvenanceRef, canonical_event_hash
from .github_lifecycle import GitHubLifecycleSnapshot, PRLifecycle, PullRequestSnapshot
from .inbox import InboxRecord, ReferenceInbox
from .leases import (
    Lease,
    LeaseConflict,
    ReferenceCASStore,
    ReferenceLeaseAuthority,
    RevisionConflict,
    StaleFencingToken,
    resources_overlap,
)
from .live_context import LiveContextCompiler
from .planning import PlanningGraph, PlanningTask, TaskState
from .postgres_store import PostgresCoordinationStore
from .projection import CoordinationGraphProjector, CosProjectionSink, ProjectionSnapshot
from .snapshot import CoordinationSnapshot

__all__ = [
    "AggregateRevisionConflict",
    "COS_BASELINE_COMMIT",
    "ConflictClass",
    "ConflictFinding",
    "ContextPack",
    "ContextPackCompiler",
    "ContextSourceRef",
    "CoordinationBus",
    "CoordinationEvent",
    "CoordinationEventStore",
    "CoordinationGraphProjector",
    "CoordinationSnapshot",
    "CosProjectionBundle",
    "CosProjectionSink",
    "CosShadowAdapter",
    "EventRole",
    "GitHubLifecycleSnapshot",
    "IdempotencyConflict",
    "InboxRecord",
    "InMemoryReferenceBus",
    "InMemoryReferenceEventStore",
    "Lease",
    "LeaseConflict",
    "LiveContextCompiler",
    "PRLifecycle",
    "PlanningGraph",
    "PlanningTask",
    "PostgresCoordinationStore",
    "ProjectionSnapshot",
    "ProvenanceRef",
    "PullRequestSnapshot",
    "ReferenceCASStore",
    "ReferenceInbox",
    "ReferenceLeaseAuthority",
    "RevisionConflict",
    "StateSnapshot",
    "StoredEvent",
    "StaleFencingToken",
    "TaskState",
    "canonical_event_hash",
    "classify_conflict",
    "event_role",
    "outcome_satisfies_command",
    "resources_overlap",
]
