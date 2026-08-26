from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
import hashlib
import json
import os
import time

from .render_guard import RenderIntent, RenderState


@dataclass(frozen=True)
class LedgerEvent:
    seq: int
    intent_id: str
    event: str
    state: str
    timestamp: str
    payload: dict[str, Any]
    prev_hash: str
    event_hash: str


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _event_hash(body: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


class RenderLedger:
    """Append-only JSONL execution ledger with hash-chain corruption detection.

    The lockfile prevents concurrent writers from silently interleaving entries. It is
    deliberately simple and local; distributed deployments should replace this storage
    adapter with a transactional backend while preserving the same event contract.
    """

    def __init__(self, path: str | Path, *, lock_timeout_s: float = 3.0) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.lock_timeout_s = lock_timeout_s

    @contextmanager
    def _lock(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.lock_timeout_s
        fd: int | None = None
        while fd is None:
            try:
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.write(fd, f"pid={os.getpid()}".encode("utf-8"))
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("render ledger lock acquisition timed out")
                time.sleep(0.025)
        try:
            yield
        finally:
            os.close(fd)
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass

    def read(self) -> list[LedgerEvent]:
        if not self.path.exists():
            return []
        events: list[LedgerEvent] = []
        for line_no, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                events.append(LedgerEvent(**json.loads(line)))
            except Exception as exc:
                raise ValueError(f"invalid render ledger entry at line {line_no}") from exc
        self.validate(events)
        return events

    @staticmethod
    def validate(events: list[LedgerEvent]) -> None:
        prev = "GENESIS"
        for expected_seq, event in enumerate(events, 1):
            if event.seq != expected_seq:
                raise ValueError("render ledger sequence discontinuity")
            if event.prev_hash != prev:
                raise ValueError("render ledger hash chain mismatch")
            body = asdict(event)
            observed = body.pop("event_hash")
            if _event_hash(body) != observed:
                raise ValueError("render ledger event hash mismatch")
            prev = observed

    def append(self, intent: RenderIntent, event: str, payload: dict[str, Any] | None = None) -> LedgerEvent:
        with self._lock():
            events = self.read()
            seq = len(events) + 1
            prev_hash = events[-1].event_hash if events else "GENESIS"
            body = {
                "seq": seq,
                "intent_id": intent.intent_id,
                "event": event,
                "state": intent.state.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": payload or {},
                "prev_hash": prev_hash,
            }
            record = LedgerEvent(**body, event_hash=_event_hash(body))
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(_canonical(asdict(record)) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            return record

    def latest_intents(self) -> dict[str, RenderIntent]:
        latest: dict[str, RenderIntent] = {}
        for event in self.read():
            snapshot = event.payload.get("intent")
            if snapshot:
                latest[event.intent_id] = RenderIntent(
                    intent_id=snapshot["intent_id"],
                    content_id=snapshot["content_id"],
                    profile_id=snapshot["profile_id"],
                    script_hash=snapshot["script_hash"],
                    state=RenderState(snapshot["state"]),
                    estimated_credits=snapshot.get("estimated_credits"),
                    provider_job_id=snapshot.get("provider_job_id"),
                    retry_count=int(snapshot.get("retry_count", 0)),
                )
        return latest

    def record_intent(self, intent: RenderIntent, event: str) -> LedgerEvent:
        return self.append(intent, event, {"intent": intent.to_dict()})

    def assert_unique_submission(self, intent_id: str) -> None:
        submitted = [e for e in self.read() if e.intent_id == intent_id and e.event == "SUBMITTED"]
        if submitted:
            raise RuntimeError("render intent already submitted; reconcile before any retry")
