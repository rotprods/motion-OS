from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderPolicy:
    provider: str
    default_usage_class: str
    default_license_state: str
    allow_as_final_asset_without_review: bool
    attribution_default: bool | None
    notes: str


@dataclass(frozen=True)
class ProviderCandidate:
    asset_id: str
    provider: str
    source_ref: str
    asset_type: str
    usage_class: str
    license_state: str
    provenance: dict[str, Any]
    technical: dict[str, Any] = field(default_factory=dict)
    sha256: str | None = None
    attribution_required: bool | None = None
    notes: str | None = None

    def __post_init__(self):
        if not self.asset_id or not self.source_ref:
            raise ValueError('provider candidate requires asset_id and source_ref')
        if self.sha256 is not None and (len(self.sha256) != 64 or any(ch not in '0123456789abcdefABCDEF' for ch in self.sha256)):
            raise ValueError('invalid sha256')
