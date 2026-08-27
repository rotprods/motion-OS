from __future__ import annotations

from enum import Enum


class EventRole(str, Enum):
    COMMAND = "COMMAND"
    OUTCOME = "OUTCOME"
    FACT = "FACT"


_COMMAND_SUFFIXES = ("_REQUESTED", "_PROPOSED", "_AUTHORIZED")
_OUTCOME_SUFFIXES = ("_COMPLETED", "_FAILED", "_REJECTED", "_ACCEPTED", "_VERIFIED", "_CLAIMED")

# Some domain outcomes are morphological contractions rather than a simple
# suffix replacement (for example WORK_CLAIM_REQUESTED -> WORK_CLAIMED).
# Keep those relations explicit instead of inferring them from string shape.
_EXPLICIT_OUTCOMES: dict[str, frozenset[str]] = {
    "WORK_CLAIM_REQUESTED": frozenset({"WORK_CLAIMED", "WORK_CLAIM_FAILED", "WORK_CLAIM_REJECTED"}),
}


def event_role(event_type: str) -> EventRole:
    if not event_type or event_type.upper() != event_type:
        raise ValueError("event_type must be upper-case")
    if event_type.endswith(_COMMAND_SUFFIXES):
        return EventRole.COMMAND
    if event_type.endswith(_OUTCOME_SUFFIXES):
        return EventRole.OUTCOME
    return EventRole.FACT


def _strip_known_suffix(event_type: str, suffixes: tuple[str, ...]) -> str:
    for suffix in sorted(suffixes, key=len, reverse=True):
        if event_type.endswith(suffix):
            return event_type[: -len(suffix)]
    return event_type


def outcome_satisfies_command(command_type: str, outcome_type: str) -> bool:
    """Conservative command/outcome compatibility guard.

    This function proves only structural compatibility. Aggregate-specific policy
    may be stricter and must still validate causation/correlation/expected state.
    """
    if event_role(command_type) != EventRole.COMMAND:
        raise ValueError("first event is not a command")
    if event_role(outcome_type) != EventRole.OUTCOME:
        raise ValueError("second event is not an outcome")

    explicit = _EXPLICIT_OUTCOMES.get(command_type)
    if explicit is not None:
        return outcome_type in explicit

    command_root = _strip_known_suffix(command_type, _COMMAND_SUFFIXES)
    outcome_root = _strip_known_suffix(outcome_type, _OUTCOME_SUFFIXES)
    return command_root == outcome_root
