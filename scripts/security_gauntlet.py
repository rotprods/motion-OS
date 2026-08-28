#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Finding:
    rule_id: str
    path: str
    line: int
    severity: str
    detail: str


def _iter_python_files(root: Path) -> Iterable[Path]:
    for base in (root / "src", root / "scripts"):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if any(part in {".venv", "venv", "node_modules", "__pycache__"} for part in path.parts):
                continue
            yield path


def _call_name(node: ast.Call) -> str:
    fn = node.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        parts: list[str] = [fn.attr]
        cur = fn.value
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


def _kw_bool(call: ast.Call, name: str) -> bool | None:
    for kw in call.keywords:
        if kw.arg == name:
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, bool):
                return kw.value.value
            return None
    return False


def scan_python(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    dangerous_exact = {
        "eval": ("PY-EVAL", "HIGH"),
        "exec": ("PY-EXEC", "HIGH"),
        "os.system": ("PY-OS-SYSTEM", "HIGH"),
        "pickle.load": ("PY-PICKLE", "HIGH"),
        "pickle.loads": ("PY-PICKLE", "HIGH"),
        "yaml.load": ("PY-YAML-LOAD", "HIGH"),
    }
    subprocess_names = {"subprocess.run", "subprocess.call", "subprocess.Popen", "subprocess.check_call", "subprocess.check_output"}
    for path in _iter_python_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except (SyntaxError, UnicodeDecodeError) as exc:
            findings.append(Finding("PY-PARSE", rel, getattr(exc, "lineno", 0) or 0, "HIGH", str(exc)))
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            if name in dangerous_exact:
                rule, sev = dangerous_exact[name]
                findings.append(Finding(rule, rel, node.lineno, sev, f"dangerous call: {name}"))
            if name in subprocess_names:
                shell = _kw_bool(node, "shell")
                if shell is True:
                    findings.append(Finding("PY-SUBPROCESS-SHELL", rel, node.lineno, "HIGH", f"{name}(..., shell=True)"))
                elif shell is None:
                    findings.append(Finding("PY-SUBPROCESS-SHELL-DYNAMIC", rel, node.lineno, "MEDIUM", f"{name} shell= is dynamic; review required"))
    return findings


def scan_workflow_pinning(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    wf_dir = root / ".github" / "workflows"
    if not wf_dir.exists():
        return findings
    uses_re = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)")
    sha_re = re.compile(r"^[0-9a-f]{40}$")
    for path in sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")):
        rel = path.relative_to(root).as_posix()
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = uses_re.match(line)
            if not match:
                continue
            target = match.group(1)
            if target.startswith("./") or target.startswith("docker://"):
                continue
            if "@" not in target:
                findings.append(Finding("GH-ACTION-UNPINNED", rel, line_no, "HIGH", f"action has no immutable ref: {target}"))
                continue
            _, ref = target.rsplit("@", 1)
            if not sha_re.fullmatch(ref):
                findings.append(Finding("GH-ACTION-MUTABLE-REF", rel, line_no, "HIGH", f"action ref is not a 40-char commit SHA: {target}"))
    return findings


def scan_secrets(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    patterns = [
        ("SECRET-OPENAI", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
        ("SECRET-GITHUB", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
        ("SECRET-AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("SECRET-PRIVATE-KEY", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ]
    excluded = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}
    allowed_suffixes = {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt", ".ts", ".tsx", ".js", ".jsx"}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue
        if any(part in excluded for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(lines, start=1):
            for rule_id, pattern in patterns:
                if pattern.search(line):
                    findings.append(Finding(rule_id, rel, line_no, "CRITICAL", "credential-like material detected"))
    return findings


def run_gauntlet(root: Path) -> dict:
    findings = scan_python(root) + scan_workflow_pinning(root) + scan_secrets(root)
    blockers = [f for f in findings if f.severity in {"CRITICAL", "HIGH"}]
    return {
        "schema": "motion-os.security-gauntlet/v1",
        "root": str(root),
        "status": "FAIL" if blockers else "PASS",
        "blocker_count": len(blockers),
        "finding_count": len(findings),
        "findings": [asdict(f) for f in findings],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic MOTION.OS repository security gauntlet")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = run_gauntlet(args.root.resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
