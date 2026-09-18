#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reverse_engineering.qualification import compile_qualification_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile MOTION.OS observable output-fidelity 9D graph")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    result = compile_qualification_manifest(manifest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "promotion_state": result["promotion_state"],
        "output_fidelity_9d_validated": result["output_fidelity_9d_validated"],
        "authoring_provenance_complete": result["authoring_provenance_complete"],
        "diagnostic_output_claim_coverage_ratio": result["diagnostic_output_claim_coverage_ratio"],
        "defects_by_severity": result["defects_by_severity"],
        "qualified_dimensions": [name for name, value in result["output_dimensions"].items() if value["qualified"]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
