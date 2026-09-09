#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_remotion_render import verify as verify_physical_render
from src.studio.replay import (
    safe_extract_product_evidence,
    seal_replay_report,
    verify_product_evidence_directory,
    verify_replay_report_hash,
)


def _write_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    persisted = json.loads(path.read_text(encoding="utf-8"))
    verify_replay_report_hash(persisted)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a persisted MOTION.OS Product E2E evidence ZIP after producer-workspace destruction"
    )
    parser.add_argument("--package", type=Path, required=True, help="persisted Product E2E ZIP")
    parser.add_argument("--out", type=Path, default=None, help="optional offline replay report JSON")
    parser.add_argument(
        "--skip-physical-probe",
        action="store_true",
        help="verify content-addressed replay only; does not grant physical replay authority",
    )
    args = parser.parse_args()

    with TemporaryDirectory(prefix="motion-os-offline-replay-") as tmp:
        extracted = Path(tmp) / "evidence"
        archive = safe_extract_product_evidence(args.package, extracted)
        replay = verify_product_evidence_directory(extracted)

        physical = None
        if not args.skip_physical_probe:
            physical = verify_physical_render(
                extracted / "runtime/remotion/src/runtimeSpec.json",
                extracted / "runtime/remotion/out/runtime-local.mp4",
            )

        sealed = seal_replay_report(
            replay,
            archive_sha256=archive["archive_sha256"],
            archive_bytes=archive["archive_bytes"],
            physical_probe=physical,
        )
        verify_replay_report_hash(sealed)
        if args.out:
            _write_atomic(args.out, sealed)
        print(json.dumps(sealed, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
