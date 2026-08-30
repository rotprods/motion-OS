from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.reverse_engineering.action_inventory import (
    gauntlet_coverage_from_frame_metrics,
    load_action_inventory,
    validate_action_inventory,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate observable-action coverage for a MOTION.OS reverse-engineering specimen")
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--frame-metrics", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    inventory = load_action_inventory(args.inventory)
    validate_action_inventory(inventory)
    metrics = json.loads(Path(args.frame_metrics).read_text(encoding="utf-8"))
    report = gauntlet_coverage_from_frame_metrics(inventory, metrics)
    report["claim_boundary"] = (
        "PASS means required P90 plus deep P80/P75 measured frame-change/motion residuals have no unexplained events after "
        "action/subevent/continuous/source-native adjudication. It does not recover hidden original project internals and does not "
        "grant render/fidelity/generalization authority."
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["observable_action_closed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
