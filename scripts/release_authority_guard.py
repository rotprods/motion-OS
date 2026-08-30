#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.main_lineage_sentinel import _validate_repo, _validate_sha, assess_lineage, fetch_associated_pulls

API_ROOT = "https://api.github.com"


@dataclass(frozen=True)
class ReleaseAuthorityVerdict:
    repository: str
    release_sha: str
    live_main_sha: str
    state: str
    authority: str
    matched_pr_numbers: tuple[int, ...]
    reason: str

    @property
    def ok(self) -> bool:
        return self.state == "RELEASE_AUTHORIZED"

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["matched_pr_numbers"] = list(self.matched_pr_numbers)
        out["ok"] = self.ok
        return out


def validate_release_state(document: object) -> None:
    if not isinstance(document, dict):
        raise ValueError("project_state must be an object")
    status = document.get("release_status")
    blockers = document.get("p0_blockers")
    if not isinstance(status, str):
        raise ValueError("release_status must be a string")
    if not isinstance(blockers, list):
        raise ValueError("p0_blockers must be a list")
    if any(not isinstance(item, str) or not item.strip() for item in blockers):
        raise ValueError("p0_blockers entries must be non-empty strings")
    if status != "RELEASED":
        raise ValueError("release_status is not RELEASED")
    if blockers:
        raise ValueError("P0 blockers remain")


def assess_release_authority(
    *,
    repository: str,
    release_sha: str,
    live_main_sha: str,
    project_state: object,
    associated_pulls: object,
) -> ReleaseAuthorityVerdict:
    repo = _validate_repo(repository)
    release = _validate_sha(release_sha)
    main_sha = _validate_sha(live_main_sha)
    validate_release_state(project_state)
    if release != main_sha:
        return ReleaseAuthorityVerdict(
            repository=repo,
            release_sha=release,
            live_main_sha=main_sha,
            state="RELEASE_TARGET_NOT_CURRENT_MAIN",
            authority="BLOCKED",
            matched_pr_numbers=(),
            reason="release/tag target must equal the current live main commit",
        )

    lineage = assess_lineage(repository=repo, commit_sha=main_sha, target_branch="main", pulls=associated_pulls)
    if not lineage.ok:
        return ReleaseAuthorityVerdict(
            repository=repo,
            release_sha=release,
            live_main_sha=main_sha,
            state="MAIN_LINEAGE_UNVERIFIED",
            authority="BLOCKED",
            matched_pr_numbers=(),
            reason=lineage.reason,
        )
    return ReleaseAuthorityVerdict(
        repository=repo,
        release_sha=release,
        live_main_sha=main_sha,
        state="RELEASE_AUTHORIZED",
        authority="VERIFIED",
        matched_pr_numbers=lineage.matched_pr_numbers,
        reason="release state is explicit, P0-free, targets current main and current main has exact merged-PR lineage",
    )


def fetch_live_main_sha(*, repository: str, token: str, timeout_s: float = 10.0) -> str:
    repo = _validate_repo(repository)
    if not isinstance(token, str) or not token.strip():
        raise ValueError("GitHub token is required")
    if not isinstance(timeout_s, (int, float)) or isinstance(timeout_s, bool) or timeout_s <= 0 or timeout_s > 30:
        raise ValueError("timeout_s must be within (0, 30]")
    request = Request(
        f"{API_ROOT}/repos/{repo}/branches/main",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motion-os-release-authority-guard/1",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=float(timeout_s)) as response:  # noqa: S310 - fixed GitHub API root + validated repo
            if getattr(response, "status", 200) != 200:
                raise RuntimeError(f"GitHub API returned unexpected status {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"live main lookup unavailable: {type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("live main lookup returned non-object payload")
    commit = payload.get("commit")
    if not isinstance(commit, dict):
        raise RuntimeError("live main payload missing commit object")
    return _validate_sha(commit.get("sha"))


def _read_state(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"project state unavailable: {type(exc).__name__}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed release authority guard for MOTION.OS")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--release-sha", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--state", type=Path, default=Path("state/project_state.json"))
    args = parser.parse_args(argv)

    try:
        repo = _validate_repo(args.repository)
        release_sha = _validate_sha(args.release_sha)
        state = _read_state(args.state)
        live_main_sha = fetch_live_main_sha(repository=repo, token=args.token)
        pulls = fetch_associated_pulls(repository=repo, commit_sha=live_main_sha, token=args.token)
        verdict = assess_release_authority(
            repository=repo,
            release_sha=release_sha,
            live_main_sha=live_main_sha,
            project_state=state,
            associated_pulls=pulls,
        )
        document = verdict.to_dict()
        code = 0 if verdict.ok else 2
    except Exception as exc:  # release authority always fails closed
        document = {
            "repository": args.repository,
            "release_sha": args.release_sha,
            "state": "RELEASE_AUTHORITY_DEGRADED",
            "authority": "BLOCKED",
            "matched_pr_numbers": [],
            "reason": type(exc).__name__,
            "ok": False,
        }
        code = 3
    print(json.dumps(document, sort_keys=True, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
