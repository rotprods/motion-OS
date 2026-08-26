from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Iterable
import hashlib
import re

INSTRUCTION_PATTERNS = (
    r"ignore (?:all |any )?(?:previous|prior) instructions",
    r"system prompt",
    r"developer message",
    r"do not cite",
    r"reveal (?:the )?(?:prompt|secret|token|key)",
    r"execute (?:this )?(?:command|code|tool)",
    r"render (?:this|now|immediately)",
)
SECRET_PATTERNS = (
    r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b",
    r"\bsk-[A-Za-z0-9_-]{20,}\b",
    r"\bAIza[0-9A-Za-z_-]{20,}\b",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
)
EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I)


@dataclass(frozen=True)
class SourceRisk:
    prompt_injection_hits: tuple[str, ...] = ()
    secret_hits: tuple[str, ...] = ()
    pii_hits: tuple[str, ...] = ()

    @property
    def quarantined(self) -> bool:
        return bool(self.secret_hits)


@dataclass(frozen=True)
class NormalizedClaim:
    claim_id: str
    proposition: str
    source_ref: str
    evidence_strength: str
    freshness: str = "UNKNOWN"
    verified_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def content_fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip()).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def scan_untrusted_source(text: str) -> SourceRisk:
    injection_hits: list[str] = []
    for pattern in INSTRUCTION_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            injection_hits.append(pattern)
    secret_hits: list[str] = []
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, text):
            secret_hits.append(pattern)
    pii_hits = tuple(sorted(set(EMAIL_RE.findall(text))))
    return SourceRisk(tuple(injection_hits), tuple(secret_hits), pii_hits)


def redact_source(text: str) -> str:
    out = text
    for pattern in SECRET_PATTERNS:
        out = re.sub(pattern, "[REDACTED_SECRET]", out)
    out = EMAIL_RE.sub("[REDACTED_EMAIL]", out)
    return out


def normalize_claim(*, proposition: str, source_ref: str, evidence_strength: str,
                    freshness: str = "UNKNOWN", verified_at: str | None = None) -> NormalizedClaim:
    allowed = {"DIRECT", "HIGH_CONFIDENCE", "INFERRED", "OPINION", "TIME_SENSITIVE", "UNSUPPORTED"}
    if evidence_strength not in allowed:
        raise ValueError(f"invalid evidence strength: {evidence_strength}")
    if not proposition.strip() or not source_ref.strip():
        raise ValueError("claim proposition and source_ref required")
    seed = f"{source_ref}\n{proposition}".encode("utf-8")
    claim_id = "CLM_" + hashlib.sha256(seed).hexdigest()[:16].upper()
    if verified_at is None and evidence_strength in {"DIRECT", "HIGH_CONFIDENCE", "TIME_SENSITIVE"}:
        verified_at = datetime.now(timezone.utc).isoformat()
    return NormalizedClaim(claim_id, proposition.strip(), source_ref.strip(), evidence_strength, freshness, verified_at)


def validate_claim_lineage(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    claims = {c.get("claim_id"): c for c in manifest.get("claims", []) if c.get("claim_id")}
    for beat in manifest.get("semantic_beats", []):
        if not beat.get("factual", False):
            continue
        refs = beat.get("claim_ids") or []
        if not refs:
            errors.append(f"{beat.get('id', '<unknown>')}: factual beat missing claim_ids")
            continue
        for claim_id in refs:
            claim = claims.get(claim_id)
            if claim is None:
                errors.append(f"{beat.get('id', '<unknown>')}: unknown claim_id {claim_id}")
            elif claim.get("evidence_strength") == "UNSUPPORTED":
                errors.append(f"{beat.get('id', '<unknown>')}: unsupported claim {claim_id} cannot be spoken as fact")
    return errors


def source_pack(raw_text: str, source_ref: str, claims: Iterable[NormalizedClaim] = ()) -> dict[str, Any]:
    risk = scan_untrusted_source(raw_text)
    return {
        "source_ref": source_ref,
        "trust_class": "UNTRUSTED_SOURCE_DATA",
        "content_fingerprint": content_fingerprint(raw_text),
        "redacted_text": redact_source(raw_text),
        "risk": asdict(risk),
        "quarantined": risk.quarantined,
        "claims": [c.to_dict() for c in claims],
    }
