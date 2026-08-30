#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Iterable

_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_ZERO_SHA = "0" * 40
_MAIN_REF = "refs/heads/main"


@dataclass(frozen=True)
class PushUpdate:
    local_ref: str
    local_sha: str
    remote_ref: str
    remote_sha: str


def _safe_ref(value: str, *, name: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise ValueError(f"{name} must be a non-empty bounded ref")
    if any(ch in value for ch in "\x00\r\n") or any(ch.isspace() for ch in value):
        raise ValueError(f"{name} contains invalid whitespace/control characters")
    if not value.startswith("refs/"):
        raise ValueError(f"{name} must be a fully-qualified git ref")
    return value


def _sha(value: str, *, name: str) -> str:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise ValueError(f"{name} must be exactly 40 hexadecimal characters")
    return value.lower()


def parse_push_updates(lines: Iterable[str]) -> tuple[PushUpdate, ...]:
    updates: list[PushUpdate] = []
    for index, raw in enumerate(lines, start=1):
        if not isinstance(raw, str):
            raise ValueError("pre-push input line must be text")
        line = raw.rstrip("\n")
        if not line:
            continue
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"pre-push line {index} must contain exactly four fields")
        local_ref, local_sha, remote_ref, remote_sha = parts
        updates.append(
            PushUpdate(
                local_ref=_safe_ref(local_ref, name="local_ref"),
                local_sha=_sha(local_sha, name="local_sha"),
                remote_ref=_safe_ref(remote_ref, name="remote_ref"),
                remote_sha=_sha(remote_sha, name="remote_sha"),
            )
        )
    if not updates:
        raise ValueError("pre-push input contained no ref updates")
    if len(updates) > 256:
        raise ValueError("pre-push update count exceeds safety bound")
    return tuple(updates)


def blocked_main_updates(updates: Iterable[PushUpdate]) -> tuple[PushUpdate, ...]:
    blocked: list[PushUpdate] = []
    for update in updates:
        # Any attempted update/create of remote main is prohibited locally.
        # Deletion is also prohibited because main deletion is destructive and must be admin-governed.
        if update.remote_ref == _MAIN_REF:
            blocked.append(update)
    return tuple(blocked)


def main() -> int:
    try:
        updates = parse_push_updates(sys.stdin)
        blocked = blocked_main_updates(updates)
    except ValueError as exc:
        print(f"MOTION.OS pre-push ref guard: BLOCKED malformed input ({exc})", file=sys.stderr)
        return 3

    if blocked:
        print("MOTION.OS policy: direct push/update/delete of refs/heads/main is prohibited.", file=sys.stderr)
        print("Create a branch + PR and use the governed promotion train instead.", file=sys.stderr)
        return 2

    print(f"MOTION.OS pre-push ref guard: {len(updates)} non-main update(s) accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
