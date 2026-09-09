#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.studio.run_manifest import build_product_run_manifest, verify_product_run_manifest


_CHUNK = 1024 * 1024


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(path)
    verify_product_run_manifest(_load(path))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seal a physical Phase06→Studio→Remotion run into a deterministic technical product manifest"
    )
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--runtime-evidence", type=Path, required=True)
    parser.add_argument("--runtime-spec", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--artifact-ref", required=True)
    parser.add_argument("--git-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if not args.runtime_spec.is_file() or args.runtime_spec.stat().st_size <= 0:
        raise SystemExit("runtime spec missing or empty")
    if not args.artifact.is_file() or args.artifact.stat().st_size <= 0:
        raise SystemExit("physical artifact missing or empty")

    bundle = _load(args.bundle)
    runtime_evidence = _load(args.runtime_evidence)
    runtime_spec = _load(args.runtime_spec)
    manifest = build_product_run_manifest(
        bundle,
        runtime_evidence,
        runtime_spec,
        git_sha=args.git_sha,
        artifact_ref=args.artifact_ref,
        artifact_sha256=_sha256_file(args.artifact),
        artifact_bytes=args.artifact.stat().st_size,
        runtime_spec_file_sha256=_sha256_file(args.runtime_spec),
    )
    _write_atomic(args.out, manifest)

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "run_id": manifest["run_id"],
                "git_sha": manifest["git_sha"],
                "content_id": manifest["content_id"],
                "graph_hash": manifest["graph_hash"],
                "render_manifest_hash": manifest["render_manifest_hash"],
                "runtime_spec_hash": manifest["runtime_spec_hash"],
                "artifact_sha256": manifest["physical_artifact"]["sha256"],
                "recovery_ready": manifest["recovery"]["recovery_ready"],
                "production_authority": manifest["production_authority"],
                "creative_authority": manifest["creative_authority"],
                "project_done": manifest["project_done"],
                "out": str(args.out),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
