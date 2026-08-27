from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class DownstreamIntegrityResult:
    ok: bool
    errors: tuple[str, ...]


class DownstreamIntegrityError(RuntimeError):
    pass


def _stable_beat_ids(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise DownstreamIntegrityError("semantic_beat_ids must be a sequence")
    ids = tuple(str(item) for item in value)
    if not ids or any(not beat_id for beat_id in ids):
        raise DownstreamIntegrityError("semantic beat IDs must be non-empty")
    if len(set(ids)) != len(ids):
        raise DownstreamIntegrityError("semantic beat IDs must be unique")
    return ids


def verify_downstream_handoff(
    handoff: Mapping[str, Any],
    *,
    expected_provenance_root: str,
    expected_replay_fingerprint: str,
    expected_beat_ids: Sequence[str],
) -> DownstreamIntegrityResult:
    """Fail-closed Phase06 -> Studio Engine semantic authority gate.

    This verifies identity only. It does not claim ownership over downstream motion,
    renderer or timeline decisions.
    """
    errors: list[str] = []
    provenance = handoff.get("provenance_root")
    replay = handoff.get("replay_fingerprint")

    if not isinstance(provenance, str) or not provenance.startswith("PRV_"):
        errors.append("missing_or_invalid_provenance_root")
    elif provenance != expected_provenance_root:
        errors.append("provenance_root_mismatch")

    if not isinstance(replay, str) or not replay.startswith("MNF_"):
        errors.append("missing_or_invalid_replay_fingerprint")
    elif replay != expected_replay_fingerprint:
        errors.append("replay_fingerprint_mismatch")

    try:
        actual_beats = _stable_beat_ids(handoff.get("semantic_beat_ids"))
    except DownstreamIntegrityError as exc:
        errors.append(str(exc))
        actual_beats = ()

    expected = tuple(str(item) for item in expected_beat_ids)
    if actual_beats and actual_beats != expected:
        errors.append("semantic_beat_identity_mismatch")

    return DownstreamIntegrityResult(ok=not errors, errors=tuple(errors))


def require_verified_downstream_handoff(
    handoff: Mapping[str, Any],
    *,
    expected_provenance_root: str,
    expected_replay_fingerprint: str,
    expected_beat_ids: Sequence[str],
) -> None:
    result = verify_downstream_handoff(
        handoff,
        expected_provenance_root=expected_provenance_root,
        expected_replay_fingerprint=expected_replay_fingerprint,
        expected_beat_ids=expected_beat_ids,
    )
    if not result.ok:
        raise DownstreamIntegrityError("downstream handoff rejected: " + ",".join(result.errors))
