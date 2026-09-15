#!/usr/bin/env python3
"""Bounded repository workflow policy, complementary to actionlint and zizmor.

This is NOT a general YAML parser or a shell security proof. It accepts the
repository's block-style configuration with simple single-line scalar values.
Unsupported syntax (flow mappings, aliases/tags, quoted keys, multi-documents,
multiline quoted scalars) fails closed instead of being silently skipped.
Use actionlint for full workflow validity and zizmor for additional analyses.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

MAX_BYTES = 1_048_576
MAX_FILES = 128
MAX_TOTAL_BYTES = 8 * MAX_BYTES
FULL_SHA_ACTION_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[^@\s]+)?@[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*):(?:\s+(.*)|$)")
PRIVILEGED_TRIGGERS = {'pull_request_target', 'workflow_run', 'issue_comment', 'repository_dispatch'}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    line: int
    message: str


@dataclass
class Entry:
    key: str | None
    indent: int
    line: int
    value: str = ''
    children: list[Entry] = field(default_factory=list)

    def get(self, key: str) -> Entry | None:
        return next((child for child in self.children if child.key == key), None)

    def scalar(self, key: str) -> str:
        child = self.get(key)
        return child.value if child is not None else ''


class UnsupportedSyntax(ValueError):
    def __init__(self, line: int):
        self.line = line
        super().__init__('unsupported or ambiguous workflow syntax')


def _scalar(raw: str, line: int) -> str:
    raw = raw.strip()
    if not raw or raw.startswith('#'):
        return ''
    if raw.startswith("'"):
        match = re.fullmatch(r"'((?:[^']|'')*)'\s*(?:#.*)?", raw)
        if not match:
            raise UnsupportedSyntax(line)
        return match[1].replace("''", "'")
    if raw.startswith('"'):
        match = re.fullmatch(r'("(?:[^"\\]|\\.)*")\s*(?:#.*)?', raw)
        if not match:
            raise UnsupportedSyntax(line)
        try:
            return json.loads(match[1])
        except ValueError:
            raise UnsupportedSyntax(line) from None
    value = re.split(r'\s+#', raw, maxsplit=1)[0].rstrip()
    if value.startswith(('&', '*', '!', '{')) or value in {'---', '...'}:
        raise UnsupportedSyntax(line)
    return value


def _document(text: str) -> Entry:
    """Scope-aware canonical block view; never infer fields from block content."""
    if len(text.encode('utf-8')) > MAX_BYTES or not text.strip():
        raise UnsupportedSyntax(1)
    text = text.replace('\r\n', '\n')
    if re.search(r'[\x00-\x08\x0b-\x1f\x7f]', text):
        raise UnsupportedSyntax(1)
    lines = text.split('\n')
    root = Entry('', -2, 1)
    stack = [root]
    i = 0
    count = 0
    while i < len(lines):
        line = lines[i]
        number = i + 1
        i += 1
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        indent = len(line) - len(line.lstrip(' '))
        body = line[indent:]
        if indent % 2 or '\t' in body[:1] or len(stack) > 48:
            raise UnsupportedSyntax(number)
        while stack[-1].indent >= indent:
            stack.pop()
        parent = stack[-1]
        if indent != parent.indent + 2 or parent.value:
            raise UnsupportedSyntax(number)
        if body.startswith('- '):
            item = Entry(None, indent, number)
            parent.children.append(item)
            stack.append(item)
            parent = item
            indent += 2
            body = body[2:]
            if not KEY_RE.match(body):
                item.value = _scalar(body, number)
                continue
        match = KEY_RE.match(body)
        if not match or parent.get(match[1]) is not None:
            raise UnsupportedSyntax(number)
        key, raw = match[1], match[2] or ''
        value = _scalar(raw, number)
        entry = Entry(key, indent, number, value)
        parent.children.append(entry)
        stack.append(entry)
        count += 1
        if count > 5000:
            raise UnsupportedSyntax(number)
        if value[:1] in {'|', '>'}:
            if value not in {'|', '|-', '|+', '>', '>-', '>+'}:
                raise UnsupportedSyntax(number)
            parts: list[str] = []
            while i < len(lines):
                next_line = lines[i]
                next_indent = len(next_line) - len(next_line.lstrip(' '))
                if next_line.strip() and next_indent <= indent:
                    break
                parts.append(next_line)
                i += 1
            entry.value = '\n'.join(parts)
    return root


def _matrix_versions(job: Entry, expression: str) -> list[str]:
    match = re.fullmatch(r'\$\{\{\s*matrix\.([A-Za-z0-9_-]+)\s*\}\}', expression)
    strategy = job.get('strategy')
    matrix = strategy.get('matrix') if strategy else None
    include = matrix.get('include') if matrix else None
    if not match or not include or not include.children:
        return []
    return [item.scalar(match[1]) for item in include.children]


def audit_text(path: str, text: str) -> list[Finding]:
    findings: list[Finding] = []

    def add(code: str, entry: Entry | None = None, severity: str = 'P1') -> None:
        findings.append(Finding(severity, code, path, entry.line if entry else 1,
                                code.lower().replace('_', ' ')))

    try:
        doc = _document(text)
    except (UnsupportedSyntax, UnicodeError) as exc:
        return [Finding('P1', 'WORKFLOW_SYNTAX_UNSUPPORTED', path,
                        getattr(exc, 'line', 1), 'unsupported, missing or ambiguous canonical block configuration')]

    def permissions(entry: Entry | None):
        if entry is None:
            add('MISSING_EXPLICIT_PERMISSIONS')
        elif entry.value in {'write-all', 'read-all'}:
            add('BROAD_TOKEN_PERMISSIONS', entry)
        elif entry.value or not entry.children:
            add('INVALID_PERMISSION_STRUCTURE', entry)
        else:
            for scope in entry.children:
                if scope.value == 'write':
                    add('WRITE_TOKEN_PERMISSION', scope)
                elif scope.value not in {'read', 'none'} or scope.children:
                    add('INVALID_PERMISSION_VALUE', scope)

    permissions(doc.get('permissions'))
    concurrency = doc.get('concurrency')
    if not concurrency or not concurrency.scalar('group') or concurrency.scalar('cancel-in-progress') not in {'true', 'false'}:
        add('MISSING_CONCURRENCY_POLICY', concurrency)
    triggers = doc.get('on')
    if not triggers or triggers.value or not triggers.children:
        add('INVALID_TRIGGER_STRUCTURE', triggers)
    elif any(event.key in PRIVILEGED_TRIGGERS for event in triggers.children):
        add('PRIVILEGED_UNTRUSTED_TRIGGER', triggers)
    elif any(event.key not in {'push', 'pull_request', 'merge_group', 'workflow_dispatch', 'schedule'} or event.value for event in triggers.children):
        add('UNSUPPORTED_TRIGGER_CONFIGURATION', triggers)
    jobs = doc.get('jobs')
    if not jobs or jobs.value or not jobs.children:
        add('INVALID_JOBS_STRUCTURE', jobs)
        return findings

    for job in jobs.children:
        if job.key is None or job.value:
            add('INVALID_JOB_STRUCTURE', job)
            continue
        if job.get('permissions') is not None:
            permissions(job.get('permissions'))
        runner = job.scalar('runs-on')
        if runner.endswith('-latest'):
            add('FLOATING_RUNNER_IMAGE', job.get('runs-on'))
        elif not re.fullmatch(r'ubuntu-\d{2}\.\d{2}', runner):
            add('UNSUPPORTED_RUNNER_OR_REUSABLE_JOB', job)
        timeout = job.scalar('timeout-minutes')
        if not timeout:
            add('JOB_TIMEOUT_MISSING', job)
        elif not timeout.isascii() or not timeout.isdigit() or not 1 <= int(timeout) <= 60:
            add('INVALID_JOB_TIMEOUT', job.get('timeout-minutes'))
        if job.get('continue-on-error') and job.scalar('continue-on-error') != 'false':
            add('CONTINUE_ON_ERROR', job.get('continue-on-error'))
        steps = job.get('steps')
        if not steps or steps.value or not steps.children:
            add('INVALID_STEPS_STRUCTURE', steps)
            continue
        for step in steps.children:
            if step.key is not None or step.value:
                add('INVALID_STEP_STRUCTURE', step)
                continue
            if step.get('continue-on-error') and step.scalar('continue-on-error') != 'false':
                add('CONTINUE_ON_ERROR', step.get('continue-on-error'))
            run, uses = step.get('run'), step.get('uses')
            if (run is None) == (uses is None):
                add('INVALID_STEP_EXECUTION', step)
                continue
            if run is not None:
                script = run.value
                if '${{' in script:
                    add('TEMPLATE_EXPRESSION_IN_SHELL', run)
                normalized = ' '.join(script.replace('\\\n', ' ').split())
                if re.search(r'pip\s+install\s+--upgrade\s+pip\b', normalized):
                    add('FLOATING_PIP_UPGRADE', run)
                if re.search(r'''pip\s+install\b.*(?:-e\s+['"]?\.\[|pip-audit(?!==))''', normalized):
                    add('BYPASS_FROZEN_PYTHON_ENV', run)
                if re.search(r'apt-get\s+install\b', normalized):
                    add('UNPINNED_OS_PACKAGE', run, 'P2')
                continue
            assert uses is not None
            ref = uses.value
            if ref.startswith('./'):
                add('LOCAL_ACTION_REQUIRES_SEPARATE_AUDIT', uses)
            elif ref.startswith('docker://'):
                if not re.fullmatch(r'docker://[^\s@]+@sha256:[0-9a-f]{64}', ref):
                    add('UNPINNED_DOCKER_ACTION', uses)
            elif not FULL_SHA_ACTION_RE.fullmatch(ref):
                add('UNPINNED_ACTION', uses)
            settings = step.get('with')
            if settings is None:
                settings = Entry('with', 0, step.line)
            if settings.value:
                add('INVALID_ACTION_INPUT_STRUCTURE', settings)
            if ref.startswith('actions/checkout@') and settings.scalar('persist-credentials') != 'false':
                add('CHECKOUT_PERSISTS_CREDENTIALS', uses)
            for name in ('python', 'node'):
                if ref.startswith(f'actions/setup-{name}@'):
                    value = settings.scalar(f'{name}-version')
                    versions = _matrix_versions(job, value) if '${{' in value else [value]
                    if not versions or not all(VERSION_RE.fullmatch(v) for v in versions):
                        add(f'FLOATING_{name.upper()}_VERSION', settings)
            if ref.startswith('actions/upload-artifact@'):
                if settings.scalar('if-no-files-found') != 'error':
                    add('EVIDENCE_UPLOAD_NOT_FAIL_CLOSED', uses)
                    if settings.scalar('if-no-files-found') == 'warn':
                        add('EVIDENCE_UPLOAD_WARN', uses)
                if '.artifacts/' in settings.scalar('path') and settings.scalar('include-hidden-files') != 'true':
                    add('HIDDEN_EVIDENCE_EXCLUDED', uses)
                retention = settings.scalar('retention-days')
                if not retention:
                    add('EVIDENCE_RETENTION_UNDECLARED', uses, 'P2')
                elif not retention.isascii() or not retention.isdigit() or not 1 <= int(retention) <= 30:
                    add('EVIDENCE_RETENTION_OUT_OF_POLICY', uses)
    return sorted(findings, key=lambda item: (item.path, item.line, item.code))


def _no_symlinks(root: Path, target: Path) -> None:
    current = root
    for part in target.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise OSError('symlink boundary')


def _audit(root: Path) -> tuple[list[Finding], dict[str, str]]:
    hashes: dict[str, str] = {}
    findings: list[Finding] = []
    folder = root / '.github/workflows'
    try:
        _no_symlinks(root, folder)
        if not folder.is_dir():
            raise OSError('missing workflow directory')
        files = []
        for index, candidate in enumerate(folder.iterdir()):
            if index >= 1024:
                raise OSError('directory entry bound')
            if candidate.suffix in {'.yml', '.yaml'}:
                files.append(candidate)
        files.sort()
        if not files or len(files) > MAX_FILES:
            raise OSError('invalid workflow count')
        total = 0
        for file in files:
            _no_symlinks(root, file)
            if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_NONBLOCK'):
                raise OSError('required safe file primitives unavailable')
            fd = os.open(file, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
            with os.fdopen(fd, 'rb') as handle:
                before = os.fstat(handle.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
                    raise OSError('invalid workflow input')
                raw = handle.read(MAX_BYTES + 1)
                after = os.fstat(handle.fileno())
            total += len(raw)
            identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            if len(raw) > MAX_BYTES or total > MAX_TOTAL_BYTES or identity_before != identity_after:
                raise OSError('workflow size or stability bound')
            name = file.relative_to(root).as_posix()
            hashes[name] = hashlib.sha256(raw).hexdigest()
            findings.extend(audit_text(name, raw.decode('utf-8')))
    except (OSError, UnicodeError, ValueError):
        findings.append(Finding('P1', 'WORKFLOW_INPUT_UNAVAILABLE', '.github/workflows', 1,
                                'input missing, unreadable, unsafe, unstable or over limit'))
    return findings, hashes


def audit_repository(root: Path) -> list[Finding]:
    return _audit(root.resolve())[0]


def _output(root: Path, value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or '..' in relative.parts or relative.suffix != '.json':
        raise OSError('invalid receipt destination')
    if relative.parts[0] in {'.git', '.github', 'scripts', 'tests', 'src', 'ci'}:
        raise OSError('receipt cannot replace configuration or code')
    target = root / relative
    _no_symlinks(root, target)
    if target.exists() and not target.is_file():
        raise OSError('receipt not a regular file')
    return target


def _write(root: Path, target: Path, report: dict) -> None:
    _no_symlinks(root, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.' + target.name + '.', suffix='.tmp', dir=target.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(report, handle, sort_keys=True, indent=2, allow_nan=False)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        _no_symlinks(root, target)
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--json-out')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report: dict = {'schema': 'motion-os.workflow-security/v2', 'status': 'RUNNING',
                    'root': str(root), 'promotion_authorized': False, 'workflow_count': 0,
                    'workflow_sha256': {}, 'blocking_count': 0, 'warning_count': 0,
                    'findings': [], 'syntax_scope': 'canonical-block-subset'}
    target: Path | None = None
    try:
        if args.json_out:
            target = _output(root, args.json_out)
            _write(root, target, report)  # invalidate previous PASS before reading inputs
        findings, hashes = _audit(root)
        report.update(workflow_count=len(hashes), workflow_sha256=hashes,
                      findings=[asdict(f) for f in findings],
                      blocking_count=sum(f.severity in {'P0', 'P1'} for f in findings),
                      warning_count=sum(f.severity not in {'P0', 'P1'} for f in findings))
        report['status'] = 'FAIL' if report['blocking_count'] else 'PASS'
        if any(f.code == 'WORKFLOW_INPUT_UNAVAILABLE' for f in findings):
            report['status'] = 'BLOCKED'
        if target:
            _write(root, target, report)
    except (OSError, ValueError, KeyboardInterrupt):
        report.update(status='BLOCKED', error_code='RECEIPT_OR_EXECUTION_UNAVAILABLE')
        if target:
            try:
                _write(root, target, report)
            except OSError:
                report['receipt_persistence_failed'] = True
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return {'PASS': 0, 'FAIL': 1}.get(report['status'], 2)


if __name__ == '__main__':
    raise SystemExit(main())
