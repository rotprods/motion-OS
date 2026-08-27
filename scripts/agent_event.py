#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import uuid

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "agent_event.schema.json"
EVENT_ROOT = ROOT / "state" / "agent_events"


def git(*args: str) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip() or None
    except Exception:
        return None


def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-")[:80] or "agent"


def load_schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _validate_timestamp(value: object) -> None:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an RFC3339 string")
    raw = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("timestamp must be valid RFC3339 date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include an explicit timezone")


def validate_event(event: dict) -> None:
    validator = Draft202012Validator(load_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(event), key=lambda e: list(e.path))
    if errors:
        raise ValueError("; ".join(error.message for error in errors))
    _validate_timestamp(event.get("timestamp"))


def emit(args: argparse.Namespace) -> Path:
    now = datetime.now(timezone.utc)
    branch = args.branch or git("branch", "--show-current") or "unknown"
    commit = args.commit_sha or git("rev-parse", "HEAD")
    event_id = args.event_id or f"{now.strftime('%Y%m%dT%H%M%S%fZ')}-{slug(args.agent_id)}-{uuid.uuid4().hex[:8]}"
    event = {
        "event_id": event_id,
        "event_type": args.event_type,
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "agent_id": args.agent_id,
        "project": "MOTION.OS",
        "branch": branch,
        "commit_sha": commit,
        "pr_number": args.pr_number,
        "summary": args.summary,
        "affected_paths": sorted(set(args.path or [])),
        "checks": {},
        "authority": args.authority,
        "correlation_id": args.correlation_id,
        "metadata": {},
    }
    validate_event(event)
    day = now.strftime("%Y-%m-%d")
    out = EVENT_ROOT / day / f"{event_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(out)
    out.write_text(json.dumps(event, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def validate_tree() -> int:
    count = 0
    ids: set[str] = set()
    for path in sorted(EVENT_ROOT.glob("**/*.json")):
        event = json.loads(path.read_text(encoding="utf-8"))
        validate_event(event)
        if event["event_id"] in ids:
            raise ValueError(f"duplicate event_id: {event['event_id']}")
        ids.add(event["event_id"])
        count += 1
    print(json.dumps({"status": "PASS", "events": count, "root": str(EVENT_ROOT)}, indent=2))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="MOTION.OS immutable agent event bus")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("emit")
    e.add_argument("event_type", choices=["work.started", "work.checkpoint", "work.completed", "work.blocked", "pr.opened", "pr.ready", "pr.merged", "main.verified", "state.reconciled"])
    e.add_argument("--agent-id", required=True)
    e.add_argument("--summary", required=True)
    e.add_argument("--authority", choices=["PROPOSED", "IMPLEMENTED", "EXECUTED", "VERIFIED"], default="IMPLEMENTED")
    e.add_argument("--branch")
    e.add_argument("--commit-sha")
    e.add_argument("--pr-number", type=int)
    e.add_argument("--path", action="append")
    e.add_argument("--correlation-id")
    e.add_argument("--event-id")
    sub.add_parser("validate")
    args = p.parse_args()
    if args.cmd == "validate":
        return validate_tree()
    out = emit(args)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
