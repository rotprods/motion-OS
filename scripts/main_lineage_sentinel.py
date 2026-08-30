#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
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
        out["matched_pr_numbers"] = list(self.matched_pr_numbers)
        out["ok"] = self.ok
        return out


def _validate_repo(repo: object) -> str:
    if not isinstance(repo, str) or not _REPO_RE.fullmatch(repo):
        raise ValueError("repository must be owner/name using safe GitHub characters")
    return repo


def _validate_sha(sha: object) -> str:
    if not isinstance(sha, str) or not _SHA_RE.fullmatch(sha):
        raise ValueError("commit_sha must be exactly 40 hexadecimal characters")
    return sha.lower()


def _validate_branch(branch: object) -> str:
    if not isinstance(branch, str) or not branch or len(branch) > 128:
        raise ValueError("target_branch must be a non-empty bounded string")
    if any(ch in branch for ch in "\r\n\x00"):
        raise ValueError("target_branch contains control characters")
    return branch


def _safe_output_path(value: object, *, root: Path | None = None) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("json_out must be a non-empty relative path")
    raw = Path(value)
    if raw.is_absolute() or ".." in raw.parts:
        raise ValueError("json_out must remain inside the working tree")
    base = (root or Path.cwd()).resolve()
    candidate = (base / raw).resolve()
    if candidate == base or base not in candidate.parents:
        raise ValueError("json_out must remain inside the working tree")
    return candidate


def assess_lineage(*, repository: str, commit_sha: str, target_branch: str, pulls: object) -> LineageVerdict:
    repo = _validate_repo(repository)
    sha = _validate_sha(commit_sha)
    branch = _validate_branch(target_branch)
    if not isinstance(pulls, list):
        raise ValueError("GitHub associated-pulls response must be a list")
    if len(pulls) > 100:
        raise ValueError("associated-pulls response exceeds safety bound")

    matched: set[int] = set()
    for raw in pulls:
        if not isinstance(raw, dict):
            raise ValueError("associated pull entry must be an object")
        number = raw.get("number")
        merged_at = raw.get("merged_at")
        merge_commit_sha = raw.get("merge_commit_sha")
        base = raw.get("base")
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ValueError("associated pull number must be a positive integer")
        if merged_at is not None and not isinstance(merged_at, str):
            raise ValueError("associated pull merged_at must be string or null")
        if merge_commit_sha is not None and not isinstance(merge_commit_sha, str):
            raise ValueError("associated pull merge_commit_sha must be string or null")
        if not isinstance(base, dict) or not isinstance(base.get("ref"), str):
            raise ValueError("associated pull base.ref is required")

        if merged_at and base["ref"] == branch and isinstance(merge_commit_sha, str):
            if _SHA_RE.fullmatch(merge_commit_sha) and merge_commit_sha.lower() == sha:
                matched.add(number)

    if matched:
        return LineageVerdict(
            repository=repo,
            commit_sha=sha,
            target_branch=branch,
            state="VERIFIED_PR_LINEAGE",
            authority="VERIFIED",
            matched_pr_numbers=tuple(sorted(matched)),
            reason="commit matches merge_commit_sha of a merged pull request targeting the protected logical branch",
        )

    return LineageVerdict(
        repository=repo,
        commit_sha=sha,
        target_branch=branch,
        state="DIRECT_WRITE_OR_UNTRACEABLE",
        authority="BLOCKED",
        matched_pr_numbers=(),
        reason="no merged pull request targeting the branch binds this exact commit SHA; reconcile before release authority",
    )


def fetch_associated_pulls(*, repository: str, commit_sha: str, token: str, timeout_s: float = 10.0) -> list[dict[str, Any]]:
    repo = _validate_repo(repository)
    sha = _validate_sha(commit_sha)
    if not isinstance(token, str) or not token.strip():
        raise ValueError("GitHub token is required")
    if not isinstance(timeout_s, (int, float)) or isinstance(timeout_s, bool) or timeout_s <= 0 or timeout_s > 30:
        raise ValueError("timeout_s must be within (0, 30]")

    url = f"{API_ROOT}/repos/{repo}/commits/{sha}/pulls?per_page=100"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motion-os-main-lineage-sentinel/1",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=float(timeout_s)) as response:  # noqa: S310 - fixed GitHub API root + validated path components
            if getattr(response, "status", 200) != 200:
                raise RuntimeError(f"GitHub API returned unexpected status {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"GitHub lineage lookup unavailable: {type(exc).__name__}") from exc
    if not isinstance(payload, list):
        raise RuntimeError("GitHub lineage lookup returned non-list payload")
    if len(payload) > 100:
        raise RuntimeError("GitHub lineage lookup exceeded bounded page size")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-visible sentinel for direct/untraceable writes to MOTION.OS main")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--sha", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--branch", default="main")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    safe_out: Path | None = None
    try:
        repository = _validate_repo(args.repository)
        commit_sha = _validate_sha(args.sha)
        branch = _validate_branch(args.branch)
        if args.json_out is not None:
            safe_out = _safe_output_path(args.json_out)
        pulls = fetch_associated_pulls(repository=repository, commit_sha=commit_sha, token=args.token)
        verdict = assess_lineage(repository=repository, commit_sha=commit_sha, target_branch=branch, pulls=pulls)
        document = verdict.to_dict()
        exit_code = 0 if verdict.ok else 2
    except Exception as exc:  # fail closed: lookup/validation failure is never release evidence
        document = {
            "repository": args.repository,
            "commit_sha": args.sha,
            "target_branch": args.branch,
            "state": "LINEAGE_CHECK_DEGRADED",
            "authority": "BLOCKED",
            "matched_pr_numbers": [],
            "reason": type(exc).__name__,
            "ok": False,
        }
        exit_code = 3

    text = json.dumps(document, sort_keys=True, ensure_ascii=False)
    if safe_out is not None:
        safe_out.parent.mkdir(parents=True, exist_ok=True)
        safe_out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
