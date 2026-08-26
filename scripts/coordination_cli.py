#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

from src.coordination.snapshot import CoordinationSnapshot


KINDS = {"HELLO", "CLAIM", "HEARTBEAT", "BLOCKED", "DECISION", "RELEASE", "CHECKPOINT", "CONFLICT"}


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")
    return data


def dump_json(value: Any, output: str | None = None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def cmd_snapshot_validate(args: argparse.Namespace) -> int:
    snapshot = CoordinationSnapshot.from_mapping(load_json(args.snapshot))
    dump_json({"valid": True, "snapshot_sha256": snapshot.snapshot_sha256})
    return 0


def cmd_context_compile(args: argparse.Namespace) -> int:
    snapshot = CoordinationSnapshot.from_mapping(load_json(args.snapshot))
    pack = snapshot.compile_context_pack(
        agent_id=args.agent_id,
        session_id=args.session_id,
        allowed_write_scopes=args.allow or [],
        forbidden_write_scopes=args.forbid or [],
        goal_summary=args.goal,
        ttl_seconds=args.ttl,
    )
    if not pack.verify_seal():
        raise RuntimeError("compiled ContextPack seal verification failed")
    dump_json(asdict(pack), args.output)
    return 0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def cmd_message(args: argparse.Namespace) -> int:
    kind = args.kind.upper()
    if kind not in KINDS:
        raise ValueError(f"unsupported coordination message kind: {kind}")
    message = {
        "kind": kind,
        "agent_id": args.agent_id,
        "session_id": args.session_id,
        "timestamp": args.timestamp or _now_iso(),
        "branch": args.branch,
        "pr": args.pr,
        "correlation_id": args.correlation_id,
        "causation_id": args.causation_id,
        "scope": args.scope or [],
        "expected_revision": args.expected_revision,
        "summary": args.summary,
        "evidence": args.evidence or [],
        "next": args.next or [],
    }
    if args.state:
        message["state"] = args.state
    dump_json(message, args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MOTION.OS agent coordination bootstrap CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("snapshot-validate", help="validate and hash a portable coordination snapshot")
    validate.add_argument("snapshot")
    validate.set_defaults(func=cmd_snapshot_validate)

    context = sub.add_parser("context-compile", help="compile a deterministic ContextPack from a snapshot")
    context.add_argument("snapshot")
    context.add_argument("--agent-id", required=True)
    context.add_argument("--session-id", required=True)
    context.add_argument("--goal", required=True)
    context.add_argument("--allow", action="append", default=[])
    context.add_argument("--forbid", action="append", default=[])
    context.add_argument("--ttl", type=int, default=900)
    context.add_argument("--output")
    context.set_defaults(func=cmd_context_compile)

    message = sub.add_parser("message", help="generate a structured Coordination Bus message")
    message.add_argument("--kind", required=True)
    message.add_argument("--agent-id", required=True)
    message.add_argument("--session-id", required=True)
    message.add_argument("--branch")
    message.add_argument("--pr", type=int)
    message.add_argument("--correlation-id", required=True)
    message.add_argument("--causation-id")
    message.add_argument("--scope", action="append", default=[])
    message.add_argument("--expected-revision")
    message.add_argument("--summary", required=True)
    message.add_argument("--evidence", action="append", default=[])
    message.add_argument("--next", action="append", default=[])
    message.add_argument("--state")
    message.add_argument("--timestamp")
    message.add_argument("--output")
    message.set_defaults(func=cmd_message)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:  # CLI boundary: fail visibly, never convert to success.
        print(f"coordination_cli error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
