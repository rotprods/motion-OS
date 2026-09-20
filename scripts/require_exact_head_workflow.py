#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

ALLOWED_EVENTS = {"pull_request", "merge_group"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WORKFLOW_RE = re.compile(r"^[A-Za-z0-9_.-]+\.ya?ml$")


def fetch_runs(repo: str, workflow: str, head: str, event: str, token: str) -> list[dict]:
    url = (
        f"https://api.github.com/repos/{repo}/actions/workflows/{quote(workflow)}/runs"
        f"?head_sha={quote(head)}&event={quote(event)}&per_page=20"
    )
    request = Request(url)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list):
        raise RuntimeError("workflow_runs_missing")
    return [run for run in runs if run.get("head_sha") == head and run.get("event") == event]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--poll-seconds", type=int, default=5)
    args = parser.parse_args()

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not REPO_RE.fullmatch(repo) or not SHA_RE.fullmatch(args.head):
        raise SystemExit("invalid exact-head workflow selector")
    if not WORKFLOW_RE.fullmatch(args.workflow) or args.event not in ALLOWED_EVENTS:
        raise SystemExit("unsupported exact-head workflow selector")
    if not token:
        raise SystemExit("GITHUB_TOKEN missing")
    if not (10 <= args.timeout_seconds <= 600 and 1 <= args.poll_seconds <= 30):
        raise SystemExit("invalid polling bounds")

    deadline = time.monotonic() + args.timeout_seconds
    while True:
        runs = fetch_runs(repo, args.workflow, args.head, args.event, token)
        if runs:
            run = max(runs, key=lambda item: (item.get("run_number", 0), item.get("run_attempt", 0), item.get("id", 0)))
            status = run.get("status")
            conclusion = run.get("conclusion")
            if status == "completed":
                payload = {
                    "schema": "motion-os.exact-head-workflow/v1",
                    "status": "PASS" if conclusion == "success" else "FAIL",
                    "workflow": args.workflow,
                    "head_sha": args.head,
                    "event": args.event,
                    "run_id": run.get("id"),
                    "run_attempt": run.get("run_attempt"),
                    "conclusion": conclusion,
                }
                print(json.dumps(payload, sort_keys=True))
                return 0 if conclusion == "success" else 1
        if time.monotonic() >= deadline:
            print(json.dumps({
                "schema": "motion-os.exact-head-workflow/v1",
                "status": "FAIL",
                "workflow": args.workflow,
                "head_sha": args.head,
                "event": args.event,
                "reason": "timeout_waiting_for_exact_head_success",
            }, sort_keys=True))
            return 1
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
