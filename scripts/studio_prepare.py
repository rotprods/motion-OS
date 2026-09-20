#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.studio.content_bridge import prepare_studio_execution


def _load(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return document


def _write_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
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
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            tmp_path = Path(handle.name)
        tmp_path.replace(path)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def _persist_outputs(
    bundle: dict[str, Any],
    *,
    out: Path,
    runtime_spec_out: Path | None,
    graph_out: Path | None,
) -> None:
    # The bundle is the authoritative completion marker. Remove any prior marker
    # before writing derived sidecars, then publish the new bundle last. A crash
    # or sidecar failure therefore cannot leave a stale bundle representing the
    # interrupted execution as complete.
    out.unlink(missing_ok=True)
    if runtime_spec_out is not None:
        _write_atomic(runtime_spec_out, bundle["runtime_spec"])
    if graph_out is not None:
        _write_atomic(graph_out, bundle["graph"])
    _write_atomic(out, bundle)


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

    # Fail closed on reruns: once this invocation starts, a previous bundle at
    # the requested destination must not remain usable as evidence of success.
    args.out.unlink(missing_ok=True)

    manifest = _load(args.manifest)
    handoff = _load(args.handoff)
    bundle = prepare_studio_execution(
        manifest,
        handoff,
        fps=args.fps,
        width=args.width,
        height=args.height,
    )
    _persist_outputs(
        bundle,
        out=args.out,
        runtime_spec_out=args.runtime_spec_out,
        graph_out=args.graph_out,
    )

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
