from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, TypeVar

from .downstream_integrity import DownstreamIntegrityError, require_verified_downstream_handoff
from .integrity import verify_manifest

T = TypeVar("T")


class StudioExecutionRejected(RuntimeError):
    """Raised before any Studio executor is invoked when authority checks fail."""


@dataclass(frozen=True)
class StudioExecutionContext:
    content_id: str
    provenance_root: str
    replay_fingerprint: str
    semantic_beat_ids: tuple[str, ...]
    render_job_id: str | None


def _authority_from_manifest(manifest: Mapping[str, Any]) -> StudioExecutionContext:
    if not verify_manifest(dict(manifest)):
        raise StudioExecutionRejected("sealed manifest integrity verification failed")

    content_id = manifest.get("content_id")
    provenance = manifest.get("provenance_chain")
    integrity = manifest.get("integrity")
    beats = manifest.get("semantic_beats")

    if not isinstance(content_id, str) or not content_id.strip():
        raise StudioExecutionRejected("manifest content_id missing or invalid")
    if not isinstance(provenance, Mapping):
        raise StudioExecutionRejected("manifest provenance_chain missing")
    if not isinstance(integrity, Mapping):
        raise StudioExecutionRejected("manifest integrity block missing")
    if not isinstance(beats, list) or not beats:
        raise StudioExecutionRejected("manifest semantic_beats missing")

    provenance_root = provenance.get("root")
    replay_fingerprint = integrity.get("replay_fingerprint")
    beat_ids = tuple(str(beat.get("id", "")) for beat in beats if isinstance(beat, Mapping))

    if not isinstance(provenance_root, str) or not provenance_root.startswith("PRV_"):
        raise StudioExecutionRejected("manifest provenance root missing or invalid")
    if not isinstance(replay_fingerprint, str) or not replay_fingerprint.startswith("MNF_"):
        raise StudioExecutionRejected("manifest replay fingerprint missing or invalid")
    if len(beat_ids) != len(beats) or any(not beat_id for beat_id in beat_ids):
        raise StudioExecutionRejected("manifest semantic beat IDs missing or invalid")
    if len(set(beat_ids)) != len(beat_ids):
        raise StudioExecutionRejected("manifest semantic beat IDs must be unique")

    render = manifest.get("render")
    render_job_id = render.get("provider_job_id") if isinstance(render, Mapping) else None
    if render_job_id is not None and not isinstance(render_job_id, str):
        raise StudioExecutionRejected("manifest render job ID malformed")

    return StudioExecutionContext(
        content_id=content_id,
        provenance_root=provenance_root,
        replay_fingerprint=replay_fingerprint,
        semantic_beat_ids=beat_ids,
        render_job_id=render_job_id,
    )


def authorize_studio_execution(
    sealed_manifest: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> StudioExecutionContext:
    """Derive authority from the sealed manifest and validate the handoff against it.

    Callers cannot provide their own expected PRV/MNF/beat IDs. The sealed manifest is
    the sole authority source. This function performs no rendering and has no side effects.
    """
    ctx = _authority_from_manifest(sealed_manifest)

    if handoff.get("content_id") != ctx.content_id:
        raise StudioExecutionRejected("handoff content_id mismatch")

    try:
        require_verified_downstream_handoff(
            handoff,
            expected_provenance_root=ctx.provenance_root,
            expected_replay_fingerprint=ctx.replay_fingerprint,
            expected_beat_ids=ctx.semantic_beat_ids,
        )
    except DownstreamIntegrityError as exc:
        raise StudioExecutionRejected(str(exc)) from exc

    handoff_job = handoff.get("render_job_id")
    if ctx.render_job_id is not None and handoff_job != ctx.render_job_id:
        raise StudioExecutionRejected("render job identity mismatch")

    return ctx


def execute_verified_studio_handoff(
    sealed_manifest: Mapping[str, Any],
    handoff: Mapping[str, Any],
    executor: Callable[[StudioExecutionContext], T],
) -> T:
    """Canonical Phase06 -> Studio boundary: executor is unreachable on failed authority."""
    if not callable(executor):
        raise TypeError("executor must be callable")
    ctx = authorize_studio_execution(sealed_manifest, handoff)
    return executor(ctx)
