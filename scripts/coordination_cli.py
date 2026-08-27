#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

# Direct execution (`python scripts/coordination_cli.py`) puts `scripts/` rather
# than the repository root on sys.path. Add the root deterministically before
# importing MOTION.OS modules. This is bootstrap CLI plumbing, not package state.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.coordination.github_lifecycle import GitHubLifecycleSnapshot  # noqa: E402
from src.coordination.live_context import LiveContextCompiler  # noqa: E402
from src.coordination.snapshot import CoordinationSnapshot  # noqa: E402


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


def parse_iso(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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


def cmd_live_context_compile(args: argparse.Namespace) -> int:
    bootstrap = CoordinationSnapshot.from_mapping(load_json(args.snapshot))
    lifecycle_raw = load_json(args.lifecycle)
    supersessions = {
        int(key): int(value)
        for key, value in dict(lifecycle_raw.get("supersessions", {})).items()
    }
    lifecycle = GitHubLifecycleSnapshot.build(
        repository=str(lifecycle_raw["repository"]),
        main_sha=str(lifecycle_raw["main_sha"]),
        prs=list(lifecycle_raw.get("prs", [])),
        supersessions=supersessions,
    )
    pack = LiveContextCompiler().compile(
        bootstrap=bootstrap,
        github=lifecycle,
        agent_id=args.agent_id,
        session_id=args.session_id,
        goal_summary=args.goal,
        generated_at=parse_iso(args.generated_at),
        ttl_seconds=args.ttl,
        allowed_write_scopes=args.allow or [],
        forbidden_write_scopes=args.forbid or [],
        event_watermark=args.event_watermark,
    )
    if not pack.verify_seal():
        raise RuntimeError("compiled live ContextPack seal verification failed")
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

    live = sub.add_parser(
        "live-context-compile",
        help="reconcile a bootstrap snapshot with fresh GitHub lifecycle state and compile a sealed ContextPack",
    )
    live.add_argument("snapshot")
    live.add_argument("lifecycle", help="normalized GitHub lifecycle JSON")
    live.add_argument("--agent-id", required=True)
    live.add_argument("--session-id", required=True)
    live.add_argument("--goal", required=True)
    live.add_argument("--generated-at", required=True, help="RFC3339 timestamp; explicit for deterministic replay")
    live.add_argument("--event-watermark", type=int)
    live.add_argument("--allow", action="append", default=[])
    live.add_argument("--forbid", action="append", default=[])
    live.add_argument("--ttl", type=int, default=900)
    live.add_argument("--output")
    live.set_defaults(func=cmd_live_context_compile)

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
