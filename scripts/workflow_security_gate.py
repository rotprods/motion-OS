#!/usr/bin/env python3
"""Fail-closed GitHub Actions policy gate for MOTION.OS.

This intentionally uses only the Python standard library so the policy that
selects trusted CI dependencies does not itself require another package parser.
It is a conservative source-policy scanner, not a replacement for actionlint or
zizmor.  Those tools remain independent analyzers.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ACTION_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)")
FULL_SHA_ACTION_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[^@\s]+)?@[0-9a-f]{40}$")
JOB_RE = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
UNSAFE_SHELL_CONTEXT_RE = re.compile(
    r"\$\{\{\s*(?:github\.event\.|github\.head_ref\b|github\.ref_name\b)"
)
PRIVILEGED_TRIGGERS = ("pull_request_target:", "workflow_run:", "issue_comment:", "repository_dispatch:")
AUTHORITY_UPLOAD = "actions/upload-artifact@"


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    line: int
    message: str


def _step_end(lines: list[str], start: int) -> int:
    indent = len(lines[start]) - len(lines[start].lstrip())
    for idx in range(start + 1, len(lines)):
        line = lines[idx]
        stripped = line.lstrip()
        current = len(line) - len(stripped)
        if current == indent and stripped.startswith("- "):
            return idx
    return len(lines)


def _literal_versions(value: str) -> list[str]:
    if "${{" in value:
        return []
    return re.findall(r"['\"]?(\d+\.\d+(?:\.\d+)?)['\"]?", value)


def audit_text(path: str, text: str) -> list[Finding]:
    lines = text.splitlines()
    findings: list[Finding] = []

    def add(severity: str, code: str, line: int, message: str) -> None:
        findings.append(Finding(severity, code, path, line + 1, message))

    jobs_index = next((i for i, line in enumerate(lines) if line.strip() == "jobs:"), len(lines))
    permissions_index = next((i for i, line in enumerate(lines[:jobs_index]) if line.startswith("permissions:")), None)
    if permissions_index is None:
        add("P1", "MISSING_EXPLICIT_PERMISSIONS", 0, "workflow must declare top-level permissions explicitly")

    for i, line in enumerate(lines):
        stripped = line.strip()

        if any(stripped == trigger for trigger in PRIVILEGED_TRIGGERS):
            add("P1", "PRIVILEGED_UNTRUSTED_TRIGGER", i, f"forbidden privileged trigger: {stripped[:-1]}")

        if re.search(r"\b(?:write-all|read-all)\b", stripped) and stripped.startswith("permissions:"):
            add("P1", "BROAD_TOKEN_PERMISSIONS", i, "broad permissions aliases are forbidden")
        if re.match(r"^[A-Za-z0-9_-]+:\s*write\s*$", stripped):
            add("P1", "WRITE_TOKEN_PERMISSION", i, "steady-state CI must not request write-capable GITHUB_TOKEN scopes")

        if "continue-on-error:" in stripped and re.search(r"continue-on-error:\s*true\b", stripped, re.I):
            add("P1", "CONTINUE_ON_ERROR", i, "required CI steps may not convert failure into success")

        if re.search(r"runs-on:\s*[^#]*-latest\b", stripped):
            add("P1", "FLOATING_RUNNER_IMAGE", i, "runner image must use a fixed OS release, not *-latest")

        if stripped.startswith("python-version:"):
            value = stripped.split(":", 1)[1].strip()
            versions = _literal_versions(value)
            for version in versions:
                if not VERSION_RE.fullmatch(version):
                    add("P1", "FLOATING_PYTHON_VERSION", i, f"Python version must be an exact patch release: {version}")

        if stripped.startswith("node-version:"):
            value = stripped.split(":", 1)[1].strip()
            versions = _literal_versions(value)
            for version in versions:
                if not VERSION_RE.fullmatch(version):
                    add("P1", "FLOATING_NODE_VERSION", i, f"Node version must be an exact patch release: {version}")

        if re.search(r"(?:python\s+-m\s+)?pip\s+install\s+--upgrade\s+pip\b", stripped):
            add("P1", "FLOATING_PIP_UPGRADE", i, "pip must be pinned by the canonical environment contract, never upgraded to latest")
        if re.search(r"(?:python\s+-m\s+)?pip\s+install\b.*(?:-e\s+['\"]?\.\[|pip-audit(?!==))", stripped):
            add("P1", "BYPASS_FROZEN_PYTHON_ENV", i, "project/audit dependencies must come from canonical frozen pylocks")

        if stripped == "if-no-files-found: warn":
            add("P1", "EVIDENCE_UPLOAD_WARN", i, "required evidence upload must fail when files are missing")

        if UNSAFE_SHELL_CONTEXT_RE.search(line):
            # Only meaningful inside a run block; conservative source policy still
            # blocks direct template insertion anywhere on a run line/body.
            prior = "\n".join(lines[max(0, i - 30): i + 1])
            if re.search(r"(?:^|\n)\s*run:\s*(?:\||>|[^\n]+)", prior):
                add("P1", "UNTRUSTED_CONTEXT_IN_SHELL", i, "potentially attacker-controlled GitHub context must enter shell through env/argv, not template expansion")

        if re.search(r"sudo\s+apt-get\s+install\b", stripped):
            add("P2", "UNPINNED_OS_PACKAGE", i, "OS package repository resolution is not content-addressed; retain as explicit media-toolchain residual")

        action = ACTION_RE.match(line)
        if action:
            ref = action.group(1).strip("'\"")
            if ref.startswith("./"):
                continue
            if ref.startswith("docker://"):
                if "@sha256:" not in ref:
                    add("P1", "UNPINNED_DOCKER_ACTION", i, "docker action must be pinned by digest")
                continue
            if not FULL_SHA_ACTION_RE.fullmatch(ref):
                add("P1", "UNPINNED_ACTION", i, f"third-party action must use a full 40-character commit SHA: {ref}")

            if ref.startswith("actions/checkout@"):
                block = "\n".join(lines[i:_step_end(lines, i)])
                if not re.search(r"persist-credentials:\s*false\b", block):
                    add("P1", "CHECKOUT_PERSISTS_CREDENTIALS", i, "actions/checkout must set persist-credentials: false")

            if ref.startswith(AUTHORITY_UPLOAD):
                block = "\n".join(lines[i:_step_end(lines, i)])
                if not re.search(r"if-no-files-found:\s*error\b", block):
                    add("P1", "EVIDENCE_UPLOAD_NOT_FAIL_CLOSED", i, "upload-artifact must use if-no-files-found: error")
                if ".artifacts/" in block and not re.search(r"include-hidden-files:\s*true\b", block):
                    add("P1", "HIDDEN_EVIDENCE_EXCLUDED", i, "uploads containing .artifacts/ must explicitly include hidden files")
                retention = re.search(r"retention-days:\s*(\d+)\b", block)
                if retention is None:
                    add("P2", "EVIDENCE_RETENTION_UNDECLARED", i, "evidence upload should declare bounded retention-days")
                elif not 1 <= int(retention.group(1)) <= 30:
                    add("P1", "EVIDENCE_RETENTION_OUT_OF_POLICY", i, "evidence retention must be between 1 and 30 days")

    # Every job with a runner must carry a finite timeout.
    jobs: list[tuple[str, int, int]] = []
    for i in range(jobs_index + 1, len(lines)):
        match = JOB_RE.match(lines[i])
        if match:
            end = next((j for j in range(i + 1, len(lines)) if JOB_RE.match(lines[j])), len(lines))
            jobs.append((match.group(1), i, end))
    for name, start, end in jobs:
        block = "\n".join(lines[start:end])
        if "runs-on:" in block and "timeout-minutes:" not in block:
            add("P1", "JOB_TIMEOUT_MISSING", start, f"job {name!r} must define timeout-minutes")

    return sorted(findings, key=lambda item: (item.path, item.line, item.code))


def audit_repository(root: Path) -> list[Finding]:
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.is_dir():
        return [Finding("P1", "WORKFLOW_DIRECTORY_MISSING", str(workflow_dir), 1, "workflow directory is missing")]
    files = sorted([*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")])
    if not files:
        return [Finding("P1", "NO_WORKFLOWS", str(workflow_dir), 1, "no workflow files discovered")]
    findings: list[Finding] = []
    for file in files:
        findings.extend(audit_text(file.relative_to(root).as_posix(), file.read_text(encoding="utf-8")))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    findings = audit_repository(root)
    blocking = [item for item in findings if item.severity in {"P0", "P1"}]
    report = {
        "schema": "motion-os.workflow-security/v1",
        "status": "FAIL" if blocking else "PASS",
        "root": str(root),
        "workflow_count": len(list((root / ".github" / "workflows").glob("*.y*ml"))) if (root / ".github" / "workflows").is_dir() else 0,
        "blocking_count": len(blocking),
        "warning_count": len(findings) - len(blocking),
        "findings": [asdict(item) for item in findings],
    }
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        out = Path(args.json_out)
        if out.is_absolute() or ".." in out.parts:
            raise SystemExit("unsafe json output path")
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_name(out.name + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(out)
    print(json.dumps(report, sort_keys=True))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
