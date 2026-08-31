#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".artifacts", ".pytest_cache", "__pycache__", "node_modules", "out", "dist", "build", ".venv", "venv"}
TEXT_SUFFIXES = {".py", ".json", ".toml", ".yaml", ".yml", ".md", ".txt", ".js", ".ts", ".tsx", ".jsx", ".sh"}


@dataclass(frozen=True, order=True)
class Finding:
    rule: str
    path: str
    line: int
    message: str
    severity: str = "HIGH"


DANGEROUS_CALLS = {
    "eval": ("PY_DYNAMIC_EVAL", "dynamic eval() execution is forbidden"),
    "exec": ("PY_DYNAMIC_EXEC", "dynamic exec() execution is forbidden"),
    "os.system": ("PY_OS_SYSTEM", "os.system() shell execution is forbidden"),
    "os.popen": ("PY_OS_POPEN", "os.popen() shell execution is forbidden"),
    "tempfile.mktemp": ("PY_INSECURE_MKTEMP", "tempfile.mktemp() is race-prone; use NamedTemporaryFile/mkdtemp"),
    "pickle.load": ("PY_UNSAFE_PICKLE", "pickle deserialization is forbidden for untrusted artifacts"),
    "pickle.loads": ("PY_UNSAFE_PICKLE", "pickle deserialization is forbidden for untrusted artifacts"),
    "yaml.load": ("PY_UNSAFE_YAML_LOAD", "yaml.load() is forbidden; require safe_load/SafeLoader semantics"),
}
SUBPROCESS_CALLS = {
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
}

# High-confidence secret forms only. Expressions are assembled to avoid embedding
# token-shaped literals in this scanner's own source.
SECRET_PATTERNS = (
    ("SECRET_PRIVATE_KEY", re.compile("-----BEGIN " + r"(?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"), "private key material committed to source"),
    ("SECRET_GITHUB_TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"), "GitHub token-shaped credential committed to source"),
    ("SECRET_OPENAI_KEY", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "API key-shaped credential committed to source"),
    ("SECRET_SLACK_TOKEN", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"), "Slack token-shaped credential committed to source"),
    ("SECRET_AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access-key-shaped credential committed to source"),
)


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def scan_python(path: Path, *, root: Path = ROOT) -> list[Finding]:
    rel = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        return [Finding("PY_SOURCE_UNREADABLE", rel, 0, f"Python source could not be read: {type(exc).__name__}")]
    try:
        tree = ast.parse(text, filename=rel)
    except SyntaxError as exc:
        return [Finding("PY_PARSE_FAILURE", rel, int(exc.lineno or 0), "Python source failed AST parsing; security analysis cannot proceed")]

    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if name in DANGEROUS_CALLS:
            rule, message = DANGEROUS_CALLS[name]
            findings.append(Finding(rule, rel, int(getattr(node, "lineno", 0)), message))
        if name in SUBPROCESS_CALLS:
            for keyword in node.keywords:
                if keyword.arg != "shell":
                    continue
                # Only literal False is accepted. True or a dynamic expression is
                # fail-closed because runtime shell activation cannot be proven absent.
                literal_false = isinstance(keyword.value, ast.Constant) and keyword.value.value is False
                if not literal_false:
                    findings.append(Finding(
                        "PY_SUBPROCESS_SHELL_UNSAFE",
                        rel,
                        int(getattr(node, "lineno", 0)),
                        "subprocess shell must be omitted or literal False; pass an argv list without a shell",
                    ))
    return findings


def scan_secrets(path: Path, *, root: Path = ROOT) -> list[Finding]:
    rel = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for rule, pattern, message in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(Finding(rule, rel, line_no, message))
    return findings


def iter_files(roots: Iterable[Path], *, root: Path = ROOT) -> tuple[Path, ...]:
    files: set[Path] = set()
    for item in roots:
        path = item if item.is_absolute() else root / item
        if path.is_file():
            files.add(path)
            continue
        if not path.exists():
            continue
        for candidate in path.rglob("*"):
            if not candidate.is_file():
                continue
            if any(part in SKIP_DIRS for part in candidate.relative_to(root).parts):
                continue
            if candidate.suffix.lower() not in TEXT_SUFFIXES:
                continue
            files.add(candidate)
    return tuple(sorted(files))


def scan_repository(roots: Iterable[Path], *, root: Path = ROOT) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    for path in iter_files(roots, root=root):
        if path.suffix.lower() == ".py":
            findings.extend(scan_python(path, root=root))
        findings.extend(scan_secrets(path, root=root))
    return tuple(sorted(set(findings)))


def report(findings: tuple[Finding, ...], roots: Iterable[Path]) -> dict[str, object]:
    return {
        "schema": "motion-os.static-security/v1",
        "roots": [str(path) for path in roots],
        "status": "FAIL" if findings else "PASS",
        "finding_count": len(findings),
        "findings": [asdict(item) for item in findings],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic high-signal MOTION.OS static security gate")
    parser.add_argument("roots", nargs="*", default=["src", "scripts", "config", ".github", "runtime"])
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    roots = tuple(Path(value) for value in args.roots)
    findings = scan_repository(roots)
    payload = report(findings, roots)
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
