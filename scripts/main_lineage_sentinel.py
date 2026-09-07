#!/usr/bin/env python3
"""Exact merged-PR lineage from donor #102; read-only, not release authority."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from scripts.local_verify import _write_report

API_ROOT = "https://api.github.com"
MAX_BYTES = 1_048_576
_REPO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}$")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


@dataclass(frozen=True)
class LineageVerdict:
    repository: str
    commit_sha: str
    target_branch: str
    state: str
    authority: str
    matched_pr_numbers: tuple[int, ...]
    reason: str

    @property
    def ok(self) -> bool:
        return self.state == "VERIFIED_PR_LINEAGE"

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out.update(matched_pr_numbers=list(self.matched_pr_numbers), ok=self.ok,
                   authority_scope="exact-merged-pr-lineage", promotion_authorized=False)
        return out


def _validate_repo(repo: object) -> str:
    if not isinstance(repo, str) or not _REPO_RE.fullmatch(repo) or repo.split("/")[1] in {".", ".."}:
        raise ValueError("invalid_repository")
    return repo


def _validate_sha(sha: object) -> str:
    if not isinstance(sha, str) or not _SHA_RE.fullmatch(sha):
        raise ValueError("invalid_commit_sha")
    return sha.lower()


def _validate_branch(branch: object) -> str:
    if (not isinstance(branch, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,127}", branch)
            or ".." in branch or "//" in branch or branch.endswith(("/", ".", ".lock"))):
        raise ValueError("invalid_branch")
    return branch


def _strict_json(raw: bytes) -> object:
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise ValueError("json_size_limit")

    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate_json_key")
            out[key] = value
        return out

    def invalid_constant(_):
        raise ValueError("nonfinite_json")

    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid_constant)
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > 32:
            raise ValueError("json_depth_limit")
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("nonfinite_json")
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
    return value


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("github_redirect_rejected")


def _github_json(*, repository: str, resource: str, token: str, timeout_s: float = 10.0) -> object:
    """Only fixed GitHub GET resources; no redirects, proxy inheritance or pagination guess."""
    repo = _validate_repo(repository)
    if resource != "branches/main" and not re.fullmatch(r"commits/[0-9a-f]{40}/pulls\?per_page=100", resource):
        raise ValueError("invalid_github_resource")
    if (not isinstance(token, str) or not token or len(token) > 4096
            or any(ord(c) < 33 or ord(c) > 126 for c in token)):
        raise ValueError("invalid_token")
    if (isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float))
            or not math.isfinite(timeout_s) or not 0 < timeout_s <= 30):
        raise ValueError("invalid_timeout")
    url = f"{API_ROOT}/repos/{repo}/{resource}"
    request = Request(url, headers={"Accept": "application/vnd.github+json",
        "Accept-Encoding": "identity", "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "motion-os-lineage/2"}, method="GET")
    # A renamed repository must be reconfigured explicitly; never forward auth on redirect.
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    with opener.open(request, timeout=float(timeout_s)) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError("unexpected_github_response")
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type not in {"application/json", "application/vnd.github+json"}:
            raise ValueError("unexpected_content_type")
        if response.headers.get("Content-Encoding", "identity").lower() not in {"", "identity"}:
            raise ValueError("unexpected_content_encoding")
        # Reject a truncated association set, rather than claim its first page is complete.
        if re.search(r'\brel\s*=\s*["\']?next\b', response.headers.get("Link", ""), re.I):
            raise ValueError("incomplete_github_pagination")
        return _strict_json(response.read(MAX_BYTES + 1))


def assess_lineage(*, repository: str, commit_sha: str, target_branch: str, pulls: object) -> LineageVerdict:
    repo, sha, branch = _validate_repo(repository), _validate_sha(commit_sha), _validate_branch(target_branch)
    if not isinstance(pulls, list) or len(pulls) > 100:
        raise ValueError("invalid_associated_pulls")
    matched: set[int] = set()
    seen: set[int] = set()
    for raw in pulls:
        if not isinstance(raw, dict):
            raise ValueError("invalid_pull")
        number, merged_at, merge_sha, base = (raw.get(k) for k in ("number", "merged_at", "merge_commit_sha", "base"))
        if type(number) is not int or number <= 0 or number in seen:
            raise ValueError("invalid_or_duplicate_pull_number")
        seen.add(number)
        if (not isinstance(base, dict) or not isinstance(base.get("ref"), str)
                or not isinstance(base.get("repo"), dict)):
            raise ValueError("invalid_pull_base")
        base_repo = _validate_repo(base["repo"].get("full_name"))
        if raw.get("state") not in {"open", "closed"} or type(raw.get("draft")) is not bool:
            raise ValueError("invalid_pull_lifecycle")
        if merged_at is not None:
            if not isinstance(merged_at, str) or not merged_at:
                raise ValueError("invalid_merge_time")
            stamp = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
            if stamp.tzinfo is None or stamp.utcoffset() is None:
                raise ValueError("invalid_merge_time")
        if merge_sha is not None:
            merge_sha = _validate_sha(merge_sha)
        if (merged_at is not None and raw["state"] == "closed" and raw["draft"] is False
                and raw.get("merged", True) is True and base["ref"] == branch
                and base_repo.casefold() == repo.casefold() and merge_sha == sha):
            matched.add(number)
    return LineageVerdict(repo, sha, branch,
        "VERIFIED_PR_LINEAGE" if matched else "DIRECT_WRITE_OR_UNTRACEABLE",
        "VERIFIED" if matched else "BLOCKED", tuple(sorted(matched)),
        "exact_merged_pr_match" if matched else "no_exact_merged_pr_match")


def fetch_associated_pulls(*, repository: str, commit_sha: str, token: str, timeout_s: float = 10.0) -> list[dict[str, Any]]:
    sha = _validate_sha(commit_sha)
    payload = _github_json(repository=repository, resource=f"commits/{sha}/pulls?per_page=100", token=token, timeout_s=timeout_s)
    if not isinstance(payload, list) or len(payload) > 100:
        raise ValueError("invalid_associated_pulls")
    return payload


def _emit(path: Path | None, document: dict) -> None:
    _write_report(path, document)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--sha", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--branch", default="main")
    parser.add_argument("--json-out", type=Path, default=Path(".artifacts/main-lineage.json"))
    args = parser.parse_args(argv)
    document = {"schema": "motion-os.main-lineage/v2", "state": "RUNNING", "authority": "BLOCKED",
                "ok": False, "promotion_authorized": False}
    code = 3
    try:
        _emit(args.json_out, document)
        repo, sha, branch = _validate_repo(args.repository), _validate_sha(args.sha), _validate_branch(args.branch)
        pulls = fetch_associated_pulls(repository=repo, commit_sha=sha, token=os.environ.get("GITHUB_TOKEN"))
        document.update(assess_lineage(repository=repo, commit_sha=sha, target_branch=branch, pulls=pulls).to_dict())
        code = 0 if document["ok"] else 2
    except Exception as exc:
        document.update(state="LINEAGE_CHECK_DEGRADED", authority="BLOCKED", ok=False,
                        reason="invalid_or_unavailable_evidence", error_type=type(exc).__name__)
    try:
        _emit(args.json_out, document)
    except (OSError, ValueError):
        document.update(state="RECEIPT_WRITE_FAILED", authority="BLOCKED", ok=False)
        code = 3
    print(json.dumps(document, sort_keys=True, allow_nan=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
