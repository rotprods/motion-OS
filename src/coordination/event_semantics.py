from __future__ import annotations

from enum import Enum


class EventRole(str, Enum):
    COMMAND = "COMMAND"
    OUTCOME = "OUTCOME"
    FACT = "FACT"


_COMMAND_SUFFIXES = ("_REQUESTED", "_PROPOSED", "_AUTHORIZED")
_OUTCOME_SUFFIXES = ("_COMPLETED", "_FAILED", "_REJECTED", "_ACCEPTED", "_VERIFIED", "_CLAIMED")


def event_role(event_type: str) -> EventRole:
    if not event_type or event_type.upper() != event_type:
        raise ValueError("event_type must be upper-case")
    if event_type.endswith(_COMMAND_SUFFIXES):
        return EventRole.COMMAND
    if event_type.endswith(_OUTCOME_SUFFIXES):
        return EventRole.OUTCOME
    return EventRole.FACT


def outcome_satisfies_command(command_type: str, outcome_type: str) -> bool:
    """Conservative structural guard; semantic policy may be stricter per aggregate."""
    if event_role(command_type) != EventRole.COMMAND:
        raise ValueError("first event is not a command")
    if event_role(outcome_type) != EventRole.OUTCOME:
        raise ValueError("second event is not an outcome")
    command_root = command_type.rsplit("_", 1)[0]
    outcome_root = outcome_type.rsplit("_", 1)[0]
    return command_root == outcome_root
