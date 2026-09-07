#!/usr/bin/env python3
"""Fail-closed final verdict for the existing Merge Safe workflow.

This consumes GitHub's needs object as data. It neither classifies paths nor
provides branch-protection, release, or cryptographic provenance authority.
"""
from __future__ import annotations

import json
import os
from typing import Any

JOBS = ("classify", "quick", "compat311", "analysis", "remotion", "security")
FLAGS = ("full", "analysis", "remotion", "security")
CONDITIONAL_JOBS = {
    "compat311": "full",
    "analysis": "analysis",
    "remotion": "remotion",
    "security": "security",
}
RESULTS = ("success", "failure", "cancelled", "skipped")
EVENTS = ("pull_request", "merge_group", "workflow_dispatch")
MAX_INPUT_CHARS = 65_536


def evaluate_gate(needs: object, event_name: object) -> dict[str, Any]:
    """Return deterministic errors without reflecting untrusted values into logs."""
    errors: list[str] = []
    flags: dict[str, bool] = {}
    results: dict[str, str] = {}
    required = ["classify", "quick"]

    if not isinstance(event_name, str) or event_name not in EVENTS:
        errors.append("event_not_supported")
    if not isinstance(needs, dict):
        errors.append("needs_must_be_object")
        needs = {}
    if set(needs) != set(JOBS):
        errors.append("needs_job_set_mismatch")

    for job in JOBS:
        node = needs.get(job)
        if not isinstance(node, dict):
            errors.append(f"job_missing_or_invalid:{job}")
            results[job] = "INVALID"
            continue
        result = node.get("result")
        if not isinstance(result, str) or result not in RESULTS:
            errors.append(f"job_result_invalid:{job}")
            results[job] = "INVALID"
        else:
            results[job] = result

    classify = needs.get("classify")
    outputs = classify.get("outputs") if isinstance(classify, dict) else None
    if not isinstance(outputs, dict):
        errors.append("classification_outputs_missing_or_invalid")
        outputs = {}
    for flag in FLAGS:
        value = outputs.get(flag)
        # GitHub outputs are strings, not Python/JSON truthy values.
        if not isinstance(value, str) or value not in ("true", "false"):
            errors.append(f"classification_flag_invalid:{flag}")
        else:
            flags[flag] = value == "true"

    if flags.get("full") is True and not all(
        flags.get(flag) is True for flag in ("analysis", "remotion", "security")
    ):
        errors.append("full_classification_inconsistent")
    if event_name in ("merge_group", "workflow_dispatch") and not all(
        flags.get(flag) is True for flag in FLAGS
    ):
        errors.append("event_requires_full_verification")

    for job, flag in CONDITIONAL_JOBS.items():
        # Unknown requirements must never authorize a skipped dependency.
        if flags.get(flag) is not False:
            required.append(job)
    for job in JOBS:
        result = results.get(job)
        if job in required:
            if result != "success":
                errors.append(f"required_job_not_success:{job}")
        elif result not in ("success", "skipped"):
            errors.append(f"optional_job_not_success_or_skipped:{job}")

    return {
        "schema": "motion-os.merge-safe-verdict/v1",
        "status": "FAIL" if errors else "PASS",
        "errors": sorted(set(errors)),
        "required_jobs": required,
        "classification": flags,
        "job_results": results,
    }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ValueError("nonfinite_json_constant")


def main() -> int:
    raw = os.environ.get("MERGE_SAFE_NEEDS_JSON", "")
    try:
        if not raw or len(raw) > MAX_INPUT_CHARS:
            raise ValueError("input_size_invalid")
        needs = json.loads(
            raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant
        )
    except (ValueError, RecursionError):
        # Do not persist parser errors, input payloads, credentials, or log controls.
        payload = {
            "schema": "motion-os.merge-safe-verdict/v1",
            "status": "FAIL",
            "errors": ["needs_json_invalid"],
        }
    else:
        payload = evaluate_gate(needs, os.environ.get("MERGE_SAFE_EVENT_NAME", ""))
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
