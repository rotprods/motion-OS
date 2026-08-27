from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _mapping_tuple(items: Iterable[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    normalized = [dict(item) for item in items]
    return tuple(sorted(normalized, key=_canonical_json))


@dataclass(frozen=True, slots=True)
class OperatorStatusSnapshot:
    project_id: str
    main_sha: str
    event_watermark: int
    health: Mapping[str, Any]
    active_work: tuple[Mapping[str, Any], ...]
    conflicts: tuple[Mapping[str, Any], ...]
    next_actions: tuple[Mapping[str, Any], ...]
    traces: tuple[Mapping[str, Any], ...]
    snapshot_sha256: str

    def canonical_payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["snapshot_sha256"] = ""
        return data

    def verify(self) -> bool:
        expected = hashlib.sha256(_canonical_json(self.canonical_payload()).encode("utf-8")).hexdigest()
        return expected == self.snapshot_sha256

    def trace(self, identifier: str) -> tuple[Mapping[str, Any], ...]:
        if not identifier:
            raise ValueError("identifier required")
        hits = []
        for item in self.traces:
            searchable = _canonical_json(item)
            if identifier in searchable:
                hits.append(item)
        return tuple(hits)


class OperatorStatusCompiler:
    """Compile a deterministic read-only operator view from already-authoritative facts."""

    def compile(
        self,
        *,
        project_id: str,
        main_sha: str,
        event_watermark: int,
        health: Mapping[str, Any],
        active_work: Iterable[Mapping[str, Any]] = (),
        conflicts: Iterable[Mapping[str, Any]] = (),
        next_actions: Iterable[Mapping[str, Any]] = (),
        traces: Iterable[Mapping[str, Any]] = (),
    ) -> OperatorStatusSnapshot:
        if not project_id.startswith("motion://project/"):
            raise ValueError("project_id must be canonical")
        if len(main_sha) < 7:
            raise ValueError("main_sha required")
        if event_watermark < 0:
            raise ValueError("event_watermark must be >= 0")
        draft = OperatorStatusSnapshot(
            project_id=project_id,
            main_sha=main_sha,
            event_watermark=event_watermark,
            health=dict(sorted(dict(health).items())),
            active_work=_mapping_tuple(active_work),
            conflicts=_mapping_tuple(conflicts),
            next_actions=_mapping_tuple(next_actions),
            traces=_mapping_tuple(traces),
            snapshot_sha256="",
        )
        digest = hashlib.sha256(_canonical_json(draft.canonical_payload()).encode("utf-8")).hexdigest()
        return OperatorStatusSnapshot(**{**asdict(draft), "snapshot_sha256": digest})
