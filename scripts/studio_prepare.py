#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.studio.content_bridge import prepare_studio_execution


def _load(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return document


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Explicit authorized Phase06 -> Studio compilation transition (no renderer side effect)"
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--handoff", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="Studio execution bundle JSON")
    parser.add_argument("--runtime-spec-out", type=Path)
    parser.add_argument("--graph-out", type=Path)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    args = parser.parse_args()

    manifest = _load(args.manifest)
    handoff = _load(args.handoff)
    bundle = prepare_studio_execution(
        manifest,
        handoff,
        fps=args.fps,
        width=args.width,
        height=args.height,
    )
    _write(args.out, bundle)
    if args.runtime_spec_out:
        _write(args.runtime_spec_out, bundle["runtime_spec"])
    if args.graph_out:
        _write(args.graph_out, bundle["graph"])

    print(
        json.dumps(
            {
                "status": "STUDIO_COMPILED",
                "execution_started": bundle["execution_started"],
                "render_started": bundle["render_started"],
                "content_id": bundle["content_id"],
                "semantic_beat_ids": bundle["semantic_beat_ids"],
                "graph_hash": bundle["graph_hash"],
                "render_manifest_hash": bundle["render_manifest"]["manifest_hash"],
                "runtime_spec_hash": bundle["runtime_spec_hash"],
                "execution_hash": bundle["execution_hash"],
                "bundle": str(args.out),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
