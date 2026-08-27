from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping


_SECRET_KEY = re.compile(r"(?:api[_-]?key|token|password|secret|authorization|cookie|credential)", re.I)
_CONTROL_TEXT = re.compile(
    r"(?:ignore\s+(?:all\s+)?previous|system\s+prompt|developer\s+message|"
    r"tool\s*call|act\s+as\s+(?:system|developer)|override\s+(?:policy|instructions?))",
    re.I,
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sanitize(value: Any, *, path: str, findings: list[str]) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key in sorted(value, key=lambda item: str(item)):
            key = str(raw_key)
            child_path = f"{path}.{key}" if path else key
            if _SECRET_KEY.search(key):
                result[key] = "[REDACTED]"
                findings.append(f"SECRET_REDACTED:{child_path}")
                continue
            result[key] = _sanitize(value[raw_key], path=child_path, findings=findings)
        return result
    if isinstance(value, list):
        return [_sanitize(item, path=f"{path}[{idx}]", findings=findings) for idx, item in enumerate(value)]
    if isinstance(value, tuple):
        return [_sanitize(item, path=f"{path}[{idx}]", findings=findings) for idx, item in enumerate(value)]
    if isinstance(value, str):
        if _CONTROL_TEXT.search(value):
            findings.append(f"CONTROL_INSTRUCTION_TEXT:{path or '$'}")
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    findings.append(f"UNSUPPORTED_TYPE_STRINGIFIED:{path or '$'}")
    return str(value)


@dataclass(frozen=True, slots=True)
class UntrustedContextEnvelope:
    source_uri: str
    source_sha256: str
    sanitized_payload: Any
    findings: tuple[str, ...]
    trust_level: str = "UNTRUSTED_DATA"

    def __post_init__(self) -> None:
        if not self.source_uri:
            raise ValueError("source_uri required")
        if len(self.source_sha256) != 64:
            raise ValueError("source_sha256 must be SHA-256 hex")
        if self.trust_level != "UNTRUSTED_DATA":
            raise ValueError("external context cannot self-promote trust level")

    @property
    def contains_control_instruction_text(self) -> bool:
        return any(item.startswith("CONTROL_INSTRUCTION_TEXT:") for item in self.findings)

    @property
    def redacted(self) -> bool:
        return any(item.startswith("SECRET_REDACTED:") for item in self.findings)


def envelope_untrusted_context(*, source_uri: str, payload: Any) -> UntrustedContextEnvelope:
    original = _canonical_json(payload)
    source_sha256 = hashlib.sha256(original.encode("utf-8")).hexdigest()
    findings: list[str] = []
    sanitized = _sanitize(payload, path="", findings=findings)
    return UntrustedContextEnvelope(
        source_uri=source_uri,
        source_sha256=source_sha256,
        sanitized_payload=sanitized,
        findings=tuple(sorted(set(findings))),
    )
