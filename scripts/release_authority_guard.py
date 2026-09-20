#!/usr/bin/env python3
"""Donor #104 release-lineage preflight; PASS is not permission to publish."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from scripts.main_lineage_sentinel import (MAX_BYTES, _emit, _github_json, _strict_json,
    _validate_repo, _validate_sha, assess_lineage, fetch_associated_pulls)


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
        return self.state == "RELEASE_LINEAGE_VERIFIED"

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out.update(matched_pr_numbers=list(self.matched_pr_numbers), ok=self.ok,
                   authority_scope="release-state-and-pr-lineage-only", promotion_authorized=False)
        return out


def validate_release_state(document: object) -> None:
    if not isinstance(document, dict):
        raise ValueError("invalid_project_state")
    blockers = document.get("p0_blockers")
    if document.get("release_status") != "RELEASED":
        raise ValueError("state_not_released")
    if not isinstance(blockers, list) or any(not isinstance(v, str) or not v.strip() for v in blockers):
        raise ValueError("invalid_p0_blockers")
    if blockers:
        raise ValueError("p0_blockers_remain")


def assess_release_authority(*, repository: str, release_sha: str, live_main_sha: str,
        live_main_sha_after: str, project_state: object, associated_pulls: object) -> ReleaseAuthorityVerdict:
    repo, release, before, after = (_validate_repo(repository), _validate_sha(release_sha),
                                   _validate_sha(live_main_sha), _validate_sha(live_main_sha_after))
    validate_release_state(project_state)
    if before != after:
        state, reason, numbers = "LIVE_MAIN_DRIFTED_DURING_CHECK", "live_main_changed", ()
    elif release != before:
        state, reason, numbers = "RELEASE_TARGET_NOT_CURRENT_MAIN", "noncurrent_release_target", ()
    else:
        lineage = assess_lineage(repository=repo, commit_sha=before, target_branch="main", pulls=associated_pulls)
        state = "RELEASE_LINEAGE_VERIFIED" if lineage.ok else "MAIN_LINEAGE_UNVERIFIED"
        reason, numbers = lineage.reason, lineage.matched_pr_numbers
    return ReleaseAuthorityVerdict(repo, release, after, state,
        "VERIFIED" if state == "RELEASE_LINEAGE_VERIFIED" else "BLOCKED", numbers, reason)


def fetch_live_main_sha(*, repository: str, token: str, timeout_s: float = 10.0) -> str:
    payload = _github_json(repository=repository, resource="branches/main", token=token, timeout_s=timeout_s)
    if not isinstance(payload, dict) or payload.get("name") != "main" or not isinstance(payload.get("commit"), dict):
        raise ValueError("invalid_main_response")
    return _validate_sha(payload["commit"].get("sha"))


def _git(*args: str) -> str:
    cp = subprocess.run(["git", *args], text=True, capture_output=True, timeout=10, shell=False)
    if cp.returncode:
        raise ValueError("git_identity_unavailable")
    return cp.stdout.strip()


def _read_bound_state(path: Path, release_sha: str) -> tuple[object, str]:
    """Bind checked-out bytes to the exact commit, never a mutable override file."""
    release = _validate_sha(release_sha)
    root = Path(_git("rev-parse", "--show-toplevel")).resolve()
    if Path.cwd().resolve() != root or _validate_sha(_git("rev-parse", "--verify", "HEAD^{commit}")) != release:
        raise ValueError("checkout_identity_mismatch")
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError("invalid_state_path")
    target = root
    for part in path.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError("symlink_state_path")
    if not target.is_file():
        raise ValueError("state_unavailable")
    with target.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    document = _strict_json(raw)
    expected = _validate_sha(_git("rev-parse", "--verify", f"{release}:{path.as_posix()}"))
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if blob != expected:
        raise ValueError("uncommitted_state_bytes")
    return document, hashlib.sha256(raw).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--release-sha", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--state", type=Path, default=Path("state/project_state.json"))
    parser.add_argument("--json-out", type=Path, default=Path(".artifacts/release-lineage.json"))
    args = parser.parse_args(argv)
    document = {"schema": "motion-os.release-lineage/v2", "state": "RUNNING", "authority": "BLOCKED",
                "ok": False, "promotion_authorized": False}
    code = 3
    try:
        _emit(args.json_out, document)
        repo, release = _validate_repo(args.repository), _validate_sha(args.release_sha)
        state, digest = _read_bound_state(args.state, release)
        # Fail before requesting credentials/metadata when the committed state blocks release.
        validate_release_state(state)
        token = os.environ.get("GITHUB_TOKEN")
        before = fetch_live_main_sha(repository=repo, token=token)
        pulls = fetch_associated_pulls(repository=repo, commit_sha=before, token=token)
        after = fetch_live_main_sha(repository=repo, token=token)
        _, final_digest = _read_bound_state(args.state, release)
        if digest != final_digest:
            raise ValueError("state_changed_during_check")
        document.update(assess_release_authority(repository=repo, release_sha=release,
            live_main_sha=before, live_main_sha_after=after, project_state=state,
            associated_pulls=pulls).to_dict())
        document["state_sha256"] = digest
        code = 0 if document["ok"] else 2
    except Exception as exc:
        document.update(state="RELEASE_LINEAGE_DEGRADED", authority="BLOCKED", ok=False,
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
