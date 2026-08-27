"""MOTION.OS multi-agent coordination primitives.

The package defines authority-neutral contracts. In-memory implementations are
reference/test backends only; production multi-host authority is an optional
promotion stage, not a requirement for local/reference verification.
"""

from .bus import CoordinationBus, InMemoryReferenceBus
from .conflicts import ConflictClass, ConflictFinding, classify_conflict
from .context import ContextPack, ContextPackCompiler, ContextSourceRef
from .event_store import (
    CoordinationEventStore,
    IdempotencyConflict,
    InMemoryReferenceEventStore,
    RevisionConflict as AggregateRevisionConflict,
    StoredEvent,
)
from .events import CoordinationEvent, ProvenanceRef, canonical_event_hash
from .leases import (
    Lease,
    LeaseConflict,
    ReferenceCASStore,
    ReferenceLeaseAuthority,
    RevisionConflict,
    StaleFencingToken,
    resources_overlap,
)
from .postgres_store import PostgresCoordinationStore
from .projection import CoordinationGraphProjector, CosProjectionSink, ProjectionSnapshot
from .snapshot import CoordinationSnapshot

__all__ = [
    "AggregateRevisionConflict",
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
    "CosProjectionSink",
    "IdempotencyConflict",
    "InMemoryReferenceBus",
    "InMemoryReferenceEventStore",
    "Lease",
    "LeaseConflict",
    "PostgresCoordinationStore",
    "ProjectionSnapshot",
    "ProvenanceRef",
    "ReferenceCASStore",
    "ReferenceLeaseAuthority",
    "RevisionConflict",
    "StoredEvent",
    "StaleFencingToken",
    "canonical_event_hash",
    "classify_conflict",
    "resources_overlap",
]
