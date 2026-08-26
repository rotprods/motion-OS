from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping


DEFAULT_THRESHOLDS = {
    "extraction": 0.90,
    "evidence": 0.90,
    "normalization": 0.90,
    "compiler": 0.95,
    "reconstruction": 0.98,
    "grammar": 0.90,
    "creative": 0.90,
    "operations": 0.90,
}


@dataclass(frozen=True)
class VerticalResult:
    name: str
    score: float
    threshold: float
    passed: bool
    authority: str
    evidence: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


def evaluate_verticals(scores: Mapping[str, float], *, evidence: Mapping[str, list[str]] | None = None, authority: Mapping[str, str] | None = None, thresholds: Mapping[str, float] | None = None) -> list[VerticalResult]:
    evidence=evidence or {}; authority=authority or {}; merged=dict(DEFAULT_THRESHOLDS); merged.update(thresholds or {})
    results=[]
    for name, threshold in merged.items():
        score=float(scores.get(name,0.0))
        auth=authority.get(name,"fixture")
        ev=tuple(evidence.get(name,[]))
        passed=score >= threshold and bool(ev)
        # Creative/reconstruction promotion cannot rely on fixture-only authority.
        if name in {"creative","reconstruction"} and auth not in {"authoritative","ground_truth"}:
            passed=False
        results.append(VerticalResult(name,round(score,4),threshold,passed,auth,ev))
    return results


def promotion_decision(results: list[VerticalResult], *, required: set[str] | None = None) -> dict[str, Any]:
    required=required or set(DEFAULT_THRESHOLDS)
    relevant=[r for r in results if r.name in required]
    failed=[r.name for r in relevant if not r.passed]
    return {
        "decision":"PROMOTE" if not failed else "HOLD",
        "failed_verticals":failed,
        "passed_verticals":[r.name for r in relevant if r.passed],
        "all_required_evidence_bound":all(bool(r.evidence) for r in relevant),
        "results":[r.to_dict() for r in relevant],
    }


def learning_delta(before: Mapping[str,float], after: Mapping[str,float]) -> dict[str,Any]:
    keys=sorted(set(before)|set(after))
    deltas={k:round(float(after.get(k,0))-float(before.get(k,0)),4) for k in keys}
    return {
        "deltas":deltas,
        "improved":[k for k,v in deltas.items() if v>0],
        "regressed":[k for k,v in deltas.items() if v<0],
        "unchanged":[k for k,v in deltas.items() if v==0],
    }
