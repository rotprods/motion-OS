from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable

from .events import CoordinationEvent
from .github_lifecycle import GitHubLifecycleSnapshot
from .replay import ReplayResult, ReplayVerifier


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class RecoveryError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True, order=True)
class RecoverySourceStatus:
    source: str
    required: bool
    available: bool
    revision: str = ""
    sha256: str = ""
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("recovery source name is required")
        if self.available and (not self.revision or not self.sha256):
            raise ValueError("available recovery source requires revision + sha256")
        if self.sha256 and (len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256)):
            raise ValueError("recovery source sha256 must be lowercase hex")
        if not self.available and not self.reason:
            raise ValueError("unavailable recovery source requires explicit reason")


@dataclass(frozen=True, slots=True)
class ColdRecoveryReport:
    repository: str
    live_main_sha: str
    lifecycle_revision: str
    replay_state_hash: str
    replay_graph_hash: str
    cos_bundle_hash: str
    event_watermark: int
    sources: tuple[RecoverySourceStatus, ...]
    authority: str
    report_hash: str

    def canonical_payload(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "live_main_sha": self.live_main_sha,
            "lifecycle_revision": self.lifecycle_revision,
            "replay_state_hash": self.replay_state_hash,
            "replay_graph_hash": self.replay_graph_hash,
            "cos_bundle_hash": self.cos_bundle_hash,
            "event_watermark": self.event_watermark,
            "sources": [asdict(item) for item in self.sources],
            "authority": self.authority,
        }

    def verify_hash(self) -> bool:
        return _sha256(self.canonical_payload()) == self.report_hash

    @property
    def degraded_sources(self) -> tuple[str, ...]:
        return tuple(item.source for item in self.sources if not item.available)


class ColdRecoveryVerifier:
    """Fail-closed cold recovery from immutable coordination events + live GitHub.

    GitHub lifecycle and immutable event history are required recovery inputs.
    Auxiliary evidence planes (for example Drive) may be unavailable, but their
    absence is represented explicitly as DEGRADED rather than silently ignored or
    promoted into synthetic authority. Graph and COS state are rebuildable
    projections and never become reverse-write authority.
    """

    def rebuild(
        self,
        *,
        events: Iterable[CoordinationEvent],
        github: GitHubLifecycleSnapshot,
        auxiliary_sources: Iterable[RecoverySourceStatus] = (),
        projection_version: int = 1,
    ) -> ColdRecoveryReport:
        if github.repository != "rotprods/motion-OS":
            raise RecoveryError("unexpected recovery repository")

        ordered = tuple(events)
        if not ordered:
            raise RecoveryError("immutable event history is required for cold recovery")

        replay = ReplayVerifier().rebuild(ordered, projection_version=projection_version)
        event_digest = _sha256([event.to_dict() for event in ordered])
        required_sources = (
            RecoverySourceStatus(
                source="github:lifecycle",
                required=True,
                available=True,
                revision=github.revision_hash,
                sha256=github.revision_hash,
            ),
            RecoverySourceStatus(
                source="repo:immutable-events",
                required=True,
                available=True,
                revision=str(replay.state_snapshot.event_watermark),
                sha256=event_digest,
            ),
        )
        sources = tuple(sorted((*required_sources, *tuple(auxiliary_sources))))

        unavailable_required = [item.source for item in sources if item.required and not item.available]
        if unavailable_required:
            raise RecoveryError("required recovery sources unavailable: " + ",".join(unavailable_required))

        authority = "RECOVERED" if all(item.available for item in sources) else "RECOVERED_DEGRADED"
        payload = {
            "repository": github.repository,
            "live_main_sha": github.main_sha,
            "lifecycle_revision": github.revision_hash,
            "replay_state_hash": replay.state_snapshot.state_hash,
            "replay_graph_hash": replay.graph_snapshot.projection_hash,
            "cos_bundle_hash": replay.cos_bundle_hash,
            "event_watermark": replay.state_snapshot.event_watermark,
            "sources": [asdict(item) for item in sources],
            "authority": authority,
        }
        return ColdRecoveryReport(
            repository=github.repository,
            live_main_sha=github.main_sha,
            lifecycle_revision=github.revision_hash,
            replay_state_hash=replay.state_snapshot.state_hash,
            replay_graph_hash=replay.graph_snapshot.projection_hash,
            cos_bundle_hash=replay.cos_bundle_hash,
            event_watermark=replay.state_snapshot.event_watermark,
            sources=sources,
            authority=authority,
            report_hash=_sha256(payload),
        )

    def equivalent(self, left: ColdRecoveryReport, right: ColdRecoveryReport) -> bool:
        return left.report_hash == right.report_hash and left.verify_hash() and right.verify_hash()

    def verify_against_replay(self, report: ColdRecoveryReport, replay: ReplayResult) -> None:
        if report.event_watermark != replay.state_snapshot.event_watermark:
            raise RecoveryError("recovery watermark does not match replay")
        if report.replay_state_hash != replay.state_snapshot.state_hash:
            raise RecoveryError("recovery state hash does not match replay")
        if report.replay_graph_hash != replay.graph_snapshot.projection_hash:
            raise RecoveryError("recovery graph hash does not match replay")
        if report.cos_bundle_hash != replay.cos_bundle_hash:
            raise RecoveryError("recovery COS bundle hash does not match replay")
