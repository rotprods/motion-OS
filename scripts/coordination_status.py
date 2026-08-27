#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.coordination.operator_status import OperatorStatusCompiler  # noqa: E402


def load_json(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("status input must be a JSON object")
    return value


def compile_snapshot(raw: dict[str, Any]):
    return OperatorStatusCompiler().compile(
        project_id=str(raw["project_id"]),
        main_sha=str(raw["main_sha"]),
        event_watermark=int(raw.get("event_watermark", 0)),
        health=dict(raw.get("health", {})),
        active_work=tuple(raw.get("active_work", [])),
        conflicts=tuple(raw.get("conflicts", [])),
        next_actions=tuple(raw.get("next_actions", [])),
        traces=tuple(raw.get("traces", [])),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only MOTION.OS coordination operator status")
    parser.add_argument("input", help="normalized operator facts JSON")
    parser.add_argument("command", choices=("status", "health", "next", "conflicts", "trace"))
    parser.add_argument("identifier", nargs="?", help="required only for trace")
    args = parser.parse_args()
    try:
        snapshot = compile_snapshot(load_json(args.input))
        if not snapshot.verify():
            raise RuntimeError("operator snapshot seal failed")
        if args.command == "status":
            payload: Any = asdict(snapshot)
        elif args.command == "health":
            payload = dict(snapshot.health)
        elif args.command == "next":
            payload = list(snapshot.next_actions)
        elif args.command == "conflicts":
            payload = list(snapshot.conflicts)
        else:
            if not args.identifier:
                raise ValueError("trace requires an identifier")
            payload = list(snapshot.trace(args.identifier))
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        return 0
    except Exception as exc:
        print(f"coordination_status error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
