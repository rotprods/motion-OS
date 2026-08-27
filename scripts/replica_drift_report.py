#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.content.replica_reconciliation import build_replica_digest, reconciliation_report


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="MOTION.OS deterministic replica drift reporter")
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--canonical-name", default="github")
    parser.add_argument("--canonical-revision", type=int, required=True)
    parser.add_argument(
        "--replica",
        action="append",
        default=[],
        metavar="NAME:REVISION:PATH",
        help="repeatable replica descriptor; use '-' path for unavailable replica",
    )
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    canonical_payload = _load(args.canonical)
    canonical = build_replica_digest(
        args.canonical_name,
        canonical_payload,
        revision=args.canonical_revision,
    )

    replicas = []
    for descriptor in args.replica:
        parts = descriptor.split(":", 2)
        if len(parts) != 3:
            raise ValueError("replica must be NAME:REVISION:PATH")
        name, revision_raw, path_raw = parts
        if not name:
            raise ValueError("replica name cannot be empty")
        revision = int(revision_raw)
        payload = None if path_raw == "-" else _load(Path(path_raw))
        replicas.append(build_replica_digest(name, payload, revision=revision))

    report = reconciliation_report(canonical, replicas)
    report.update({
        "schema": "motion-os.replica-drift-report/v1",
        "authority": "advisory_read_only",
        "writes_performed": False,
    })
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 2 if report["conflicts"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
