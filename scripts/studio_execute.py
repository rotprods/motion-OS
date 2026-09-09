#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.content.studio_execution_gateway import authorize_studio_execution


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
            tmp_path = Path(handle.name)
        tmp_path.replace(path)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MOTION.OS canonical Phase06 -> Studio execution authority gate"
    )
    parser.add_argument("--manifest", type=Path, required=True, help="sealed Phase06 manifest")
    parser.add_argument("--handoff", type=Path, required=True, help="Phase06 downstream handoff JSON")
    parser.add_argument("--out", type=Path, default=None, help="optional execution authorization report")
    args = parser.parse_args()

    if args.out is not None:
        # A rerun must not leave an earlier authorization report looking current
        # if validation of the new inputs fails.
        args.out.unlink(missing_ok=True)

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
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        _write_atomic(args.out, text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
