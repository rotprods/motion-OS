from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Protocol


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,255}$")
_ALLOWED_PURPOSES = {"temporal_multimodal", "creative_review"}


class ProviderAuthorityVerificationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderAuthorityClaim:
    purpose: str
    provider: str
    provider_run_id: str
    media_sha256: str
    full_video_scope: bool
    provider_attestation_id: str

    def __post_init__(self) -> None:
        if self.purpose not in _ALLOWED_PURPOSES:
            raise ProviderAuthorityVerificationError("unsupported provider authority purpose")
        for field_name in ("provider", "provider_run_id", "provider_attestation_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
                raise ProviderAuthorityVerificationError(f"{field_name} malformed")
        if not isinstance(self.media_sha256, str) or _SHA256_RE.fullmatch(self.media_sha256) is None:
            raise ProviderAuthorityVerificationError("media_sha256 malformed")
        if self.full_video_scope is not True:
            raise ProviderAuthorityVerificationError("full_video_scope must be literal true")

    def canonical_payload(self) -> dict[str, object]:
        return asdict(self)


class ProviderAuthorityVerifier(Protocol):
    """Trusted adapter for an authority source outside the untrusted provider payload.

    Implementations may verify a signed receipt, look up an immutable provider run,
    validate a webhook/event receipt, or query another independently authenticated
    evidence source. Returning truthy non-bool values is deliberately insufficient.
    """

    verifier_id: str

    def verify(self, claim: ProviderAuthorityClaim) -> bool: ...


@dataclass(frozen=True, slots=True)
class VerifiedProviderAuthority:
    claim: ProviderAuthorityClaim
    verifier_id: str
    receipt_sha256: str


def _verifier_id(verifier: ProviderAuthorityVerifier) -> str:
    value = getattr(verifier, "verifier_id", None)
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise ProviderAuthorityVerificationError("authority verifier_id malformed")
    return value


def verify_provider_authority(
    claim: ProviderAuthorityClaim,
    verifier: ProviderAuthorityVerifier | None,
) -> VerifiedProviderAuthority:
    if verifier is None:
        raise ProviderAuthorityVerificationError("independent provider authority verifier required")
    verifier_id = _verifier_id(verifier)
    verify = getattr(verifier, "verify", None)
    if not callable(verify):
        raise ProviderAuthorityVerificationError("authority verifier missing verify capability")
    try:
        result = verify(claim)
    except Exception as exc:
        raise ProviderAuthorityVerificationError("independent provider authority verification failed") from exc
    if result is not True:
        raise ProviderAuthorityVerificationError("provider authority claim was not independently verified")
    receipt_payload = {
        "claim": claim.canonical_payload(),
        "verifier_id": verifier_id,
    }
    receipt_sha256 = hashlib.sha256(
        json.dumps(receipt_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return VerifiedProviderAuthority(
        claim=claim,
        verifier_id=verifier_id,
        receipt_sha256=receipt_sha256,
    )
