"""MOTION.OS multi-agent coordination primitives.

The package defines authority-neutral contracts. In-memory implementations are
reference/test backends only; production multi-host authority is PostgreSQL.
"""

from .bus import CoordinationBus, InMemoryReferenceBus
from .context import ContextPack, ContextPackCompiler, ContextSourceRef
from .events import CoordinationEvent, canonical_event_hash
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
    "ContextPack",
    "ContextPackCompiler",
    "ContextSourceRef",
    "CoordinationBus",
    "CoordinationEvent",
    "CoordinationGraphProjector",
    "CoordinationSnapshot",
    "CosProjectionSink",
    "InMemoryReferenceBus",
    "Lease",
    "LeaseConflict",
    "PostgresCoordinationStore",
    "ProjectionSnapshot",
    "ReferenceCASStore",
    "ReferenceLeaseAuthority",
    "RevisionConflict",
    "StaleFencingToken",
    "canonical_event_hash",
    "resources_overlap",
]
