#!/usr/bin/env python3
"""Read-only release-candidate rehearsal. Never grants promotion authority."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.main_lineage_sentinel import MAX_BYTES, _strict_json, _validate_repo, _validate_sha
from scripts.local_verify import _write_report

API_ROOT = "https://api.github.com"
BARRIER_ISSUE = 48


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("github_redirect_rejected")


def _canonical_hash(value: object) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _github_json(*, repository: str, resource: str, token: str, timeout_s: float = 10.0) -> object:
    repo = _validate_repo(repository)
    if resource not in {"branches/main", f"issues/{BARRIER_ISSUE}"}:
        raise ValueError("invalid_github_resource")
    if (not isinstance(token, str) or not token or len(token) > 4096
            or any(ord(c) < 33 or ord(c) > 126 for c in token)):
        raise ValueError("invalid_token")
    if (isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float))
            or not math.isfinite(timeout_s) or not 0 < timeout_s <= 30):
        raise ValueError("invalid_timeout")
    url = f"{API_ROOT}/repos/{repo}/{resource}"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Accept-Encoding": "identity",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motion-os-release-rehearsal/1",
        },
        method="GET",
    )
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    with opener.open(request, timeout=float(timeout_s)) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError("unexpected_github_response")
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type not in {"application/json", "application/vnd.github+json"}:
            raise ValueError("unexpected_content_type")
        if response.headers.get("Content-Encoding", "identity").lower() not in {"", "identity"}:
            raise ValueError("unexpected_content_encoding")
        return _strict_json(response.read(MAX_BYTES + 1))


def _parse_main(payload: object) -> tuple[str, bool]:
    if not isinstance(payload, dict) or payload.get("name") != "main":
        raise ValueError("invalid_main_response")
    commit = payload.get("commit")
    protected = payload.get("protected")
    if not isinstance(commit, dict) or type(protected) is not bool:
        raise ValueError("invalid_main_response")
    return _validate_sha(commit.get("sha")), protected


def _parse_barrier(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("invalid_barrier_response")
    if payload.get("number") != BARRIER_ISSUE or payload.get("state") not in {"open", "closed"}:
        raise ValueError("invalid_barrier_response")
    return str(payload["state"])


def assess_rehearsal(
    *,
    repository: str,
    candidate_sha: str,
    expected_main_sha: str,
    main_before: object,
    main_after: object,
    barrier_before: object,
    barrier_after: object,
) -> dict[str, Any]:
    repo = _validate_repo(repository)
    candidate = _validate_sha(candidate_sha)
    expected = _validate_sha(expected_main_sha)
    before_sha, before_protected = _parse_main(main_before)
    after_sha, after_protected = _parse_main(main_after)
    before_barrier = _parse_barrier(barrier_before)
    after_barrier = _parse_barrier(barrier_after)

    blockers: list[str] = []
    if before_sha != after_sha or before_protected != after_protected or before_barrier != after_barrier:
        status = "STALE_LIVE_AUTHORITY"
        blockers.append("live_authority_drifted_during_check")
    elif expected != before_sha:
        status = "STALE_EXPECTED_MAIN"
        blockers.append("expected_main_sha_mismatch")
    else:
        if before_barrier != "closed":
            blockers.append("issue_48_open")
        if not before_protected:
            blockers.append("main_native_protection_absent")
        status = "BLOCKED_EXTERNAL" if blockers else "PRECONDITIONS_SATISFIED"

    document: dict[str, Any] = {
        "schema": "motion-os.release-candidate-rehearsal/v1",
        "repository": repo,
        "candidate_sha": candidate,
        "expected_main_sha": expected,
        "observed_main_sha": after_sha,
        "main_protected": after_protected,
        "barrier_issue": BARRIER_ISSUE,
        "barrier_state": after_barrier,
        "status": status,
        "authority": "PRE_RELEASE_REHEARSAL_ONLY",
        "blockers": blockers,
        "promotion_authorized": False,
        "release_authorized": False,
        "project_done": False,
    }
    document["attestation_hash"] = _canonical_hash(document)
    return document


def verify_attestation(document: object) -> None:
    if not isinstance(document, dict):
        raise ValueError("invalid_attestation")
    digest = document.get("attestation_hash")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("invalid_attestation_hash")
    unsigned = dict(document)
    unsigned.pop("attestation_hash", None)
    if _canonical_hash(unsigned) != digest:
        raise ValueError("attestation_hash_mismatch")
    if document.get("promotion_authorized") is not False or document.get("release_authorized") is not False:
        raise ValueError("rehearsal_cannot_authorize_release")
    if document.get("project_done") is not False:
        raise ValueError("rehearsal_cannot_claim_project_done")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--candidate-sha", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--expected-main-sha", required=True)
    parser.add_argument("--json-out", type=Path, default=Path(".artifacts/release-candidate-rehearsal.json"))
    parser.add_argument(
        "--expect-status",
        choices=("BLOCKED_EXTERNAL", "PRECONDITIONS_SATISFIED", "STALE_LIVE_AUTHORITY", "STALE_EXPECTED_MAIN"),
    )
    args = parser.parse_args(argv)

    document: dict[str, Any] = {
        "schema": "motion-os.release-candidate-rehearsal/v1",
        "status": "RUNNING",
        "authority": "BLOCKED",
        "promotion_authorized": False,
        "release_authorized": False,
        "project_done": False,
    }
    exit_code = 3
    try:
        _write_report(args.json_out, document)
        repo = _validate_repo(args.repository)
        candidate = _validate_sha(args.candidate_sha)
        expected = _validate_sha(args.expected_main_sha)
        token = os.environ.get("GITHUB_TOKEN")
        main_before = _github_json(repository=repo, resource="branches/main", token=token)
        barrier_before = _github_json(repository=repo, resource=f"issues/{BARRIER_ISSUE}", token=token)
        main_after = _github_json(repository=repo, resource="branches/main", token=token)
        barrier_after = _github_json(repository=repo, resource=f"issues/{BARRIER_ISSUE}", token=token)
        document = assess_rehearsal(
            repository=repo,
            candidate_sha=candidate,
            expected_main_sha=expected,
            main_before=main_before,
            main_after=main_after,
            barrier_before=barrier_before,
            barrier_after=barrier_after,
        )
        verify_attestation(document)
        if args.expect_status is not None:
            exit_code = 0 if document["status"] == args.expect_status else 2
        else:
            exit_code = 0 if document["status"] == "PRECONDITIONS_SATISFIED" else 2
    except Exception as exc:
        document = {
            "schema": "motion-os.release-candidate-rehearsal/v1",
            "status": "REHEARSAL_DEGRADED",
            "authority": "BLOCKED",
            "promotion_authorized": False,
            "release_authorized": False,
            "project_done": False,
            "reason": "invalid_or_unavailable_evidence",
            "error_type": type(exc).__name__,
        }
        document["attestation_hash"] = _canonical_hash(document)
        exit_code = 3
    try:
        _write_report(args.json_out, document)
    except (OSError, ValueError):
        return 3
    print(json.dumps(document, sort_keys=True, allow_nan=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
