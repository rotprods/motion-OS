#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.content.studio_execution_gateway import authorize_studio_execution


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MOTION.OS canonical Phase06 -> Studio execution authority gate"
    )
    parser.add_argument("--manifest", type=Path, required=True, help="sealed Phase06 manifest")
    parser.add_argument("--handoff", type=Path, required=True, help="Phase06 downstream handoff JSON")
    parser.add_argument("--out", type=Path, default=None, help="optional execution authorization report")
    args = parser.parse_args()

    manifest = _load(args.manifest)
    handoff = _load(args.handoff)
    ctx = authorize_studio_execution(manifest, handoff)
    report = {
        "schema": "motion-os.studio-execution-authorization/v1",
        "authorized": True,
        "content_id": ctx.content_id,
        "provenance_root": ctx.provenance_root,
        "replay_fingerprint": ctx.replay_fingerprint,
        "semantic_beat_ids": list(ctx.semantic_beat_ids),
        "render_job_id": ctx.render_job_id,
        "authority": "sealed_manifest_fail_closed",
        "execution_started": False,
    }
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
