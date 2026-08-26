"""MOTION.OS multi-agent coordination primitives.

The package defines authority-neutral contracts. The in-memory implementation is a
reference/test backend only; production multi-host authority is PostgreSQL.
"""

from .bus import CoordinationBus, InMemoryReferenceBus
from .events import CoordinationEvent, canonical_event_hash

__all__ = [
    "CoordinationBus",
    "CoordinationEvent",
    "InMemoryReferenceBus",
    "canonical_event_hash",
]
