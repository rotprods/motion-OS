from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


TruthScalar = str | int | bool | None


@dataclass(frozen=True, slots=True)
class TruthClaim:
    surface: str
    key: str
    value: TruthScalar
    current: bool = True

    def __post_init__(self) -> None:
        if not self.surface or not self.key:
            raise ValueError("truth claim surface/key required")
        if not isinstance(self.current, bool):
            raise ValueError("truth claim current must be boolean")
        _normalized(self.value)


@dataclass(frozen=True, slots=True)
class TruthConflict:
    key: str
    authoritative_value: str
    conflicting_surface: str
    conflicting_value: str


@dataclass(frozen=True, slots=True)
class TruthConsistencyReport:
    ok: bool
    conflicts: tuple[TruthConflict, ...]
    stale_surfaces: tuple[str, ...]


LIVE_PREFIXES = ("main:", "pr:", "branch:", "commit:", "ci:")
MISSING_LIVE_AUTHORITY = "<MISSING_LIVE_AUTHORITY>"


def _normalized(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return value.strip()
    raise ValueError("truth values must be scalar string/int/bool/null")


def compile_truth_consistency(
    *,
    live_github: Mapping[str, Any],
    claims: Iterable[TruthClaim],
) -> TruthConsistencyReport:
    """Compare current-state claims against live executable lifecycle authority.

    Historical claims (`current=False`) remain evidence but never conflict with current
    truth. A current GitHub-lifecycle claim is never allowed to become current authority
    when the corresponding live fact is absent: missing live authority is an explicit
    conflict, not an implicit pass. Other authority domains require their own adapter.
    """
    authoritative: dict[str, str] = {}
    for key, value in live_github.items():
        if not isinstance(key, str) or not key.startswith(LIVE_PREFIXES):
            raise ValueError(f"unsupported live truth key: {key}")
        authoritative[key] = _normalized(value)

    conflicts: list[TruthConflict] = []
    stale: set[str] = set()
    for claim in claims:
        if not claim.current:
            continue
        if not claim.key.startswith(LIVE_PREFIXES):
            continue
        actual = _normalized(claim.value)
        if claim.key not in authoritative:
            conflicts.append(
                TruthConflict(
                    key=claim.key,
                    authoritative_value=MISSING_LIVE_AUTHORITY,
                    conflicting_surface=claim.surface,
                    conflicting_value=actual,
                )
            )
            stale.add(claim.surface)
            continue
        expected = authoritative[claim.key]
        if actual != expected:
            conflicts.append(
                TruthConflict(
                    key=claim.key,
                    authoritative_value=expected,
                    conflicting_surface=claim.surface,
                    conflicting_value=actual,
                )
            )
            stale.add(claim.surface)

    conflicts.sort(key=lambda row: (row.key, row.conflicting_surface, row.conflicting_value))
    return TruthConsistencyReport(
        ok=not conflicts,
        conflicts=tuple(conflicts),
        stale_surfaces=tuple(sorted(stale)),
    )


def require_truth_consistency(*, live_github: Mapping[str, Any], claims: Iterable[TruthClaim]) -> None:
    report = compile_truth_consistency(live_github=live_github, claims=claims)
    if not report.ok:
        details = "; ".join(
            f"{c.key}: live={c.authoritative_value} {c.conflicting_surface}={c.conflicting_value}"
            for c in report.conflicts
        )
        raise RuntimeError("canonical truth conflict: " + details)
