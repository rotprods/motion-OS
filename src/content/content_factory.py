from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable
import re

from src.content.source_security import validate_claim_lineage
from src.content.tts_integrity import tts_integrity_errors

DRIVERS = ("MONEY", "LOVE", "HEALTH", "PERSONAL_GROWTH")
HOOK_FAMILIES = (
    "LOSS", "GAIN", "CONTRADICTION", "FUTURE_SHOCK", "SOCIAL_PROOF",
    "STATUS", "HIDDEN_MECHANISM", "EXTREME_SIMPLICITY", "CURIOSITY_GAP",
    "DIRECT_CHALLENGE", "IDENTITY_THREAT",
)
ATTENTION_REFRESH_TYPES = (
    "NEW_FACT", "QUESTION", "CONTRAST", "EXAMPLE", "PAUSE", "VISUAL_PAYOFF",
    "EMOTIONAL_SHIFT", "REFRAME", "PROOF", "CTA", "MORAL",
)


@dataclass(frozen=True)
class AngleCandidate:
    id: str
    text: str
    score: float
    rationale: str = ""


@dataclass(frozen=True)
class HookCandidate:
    id: str
    family: str
    text: str
    score: float


@dataclass(frozen=True)
class Beat:
    id: str
    function: str
    text: str
    target_duration_s: float
    new_information: bool = True
    emotional_delta: str = ""
    edit_cues: tuple[str, ...] = ()
    attention_refresh: str = "NEW_FACT"
    cognitive_load: float = 0.5
    factual: bool = False
    claim_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    estimated_duration_s: float
    decision: str = "PASS"


def choose_primary_driver(scores: dict[str, float]) -> str:
    unknown = set(scores) - set(DRIVERS)
    if unknown:
        raise ValueError(f"unknown drivers: {sorted(unknown)}")
    if not scores:
        raise ValueError("driver scores required")
    return max(DRIVERS, key=lambda d: scores.get(d, float("-inf")))


def rank_angles(candidates: Iterable[AngleCandidate]) -> list[AngleCandidate]:
    return sorted(candidates, key=lambda x: (-x.score, x.id))


def rank_hooks(candidates: Iterable[HookCandidate]) -> list[HookCandidate]:
    for hook in candidates:
        if hook.family not in HOOK_FAMILIES:
            raise ValueError(f"unknown hook family: {hook.family}")
    return sorted(candidates, key=lambda x: (-x.score, x.id))


def build_retention_beats(items: list[tuple[str, str]], target_duration_s: float) -> list[Beat]:
    if not items:
        raise ValueError("at least one semantic item is required")
    per = target_duration_s / len(items)
    beats = []
    for idx, (function, text) in enumerate(items):
        slug = re.sub(r"[^A-Z0-9]+", "_", function.upper()).strip("_") or "BEAT"
        beats.append(Beat(id=f"B{idx:02d}_{slug}", function=function, text=text,
                          target_duration_s=round(per, 3)))
    return beats


def stable_beat_ids(beats: Iterable[Beat]) -> bool:
    ids = [b.id for b in beats]
    return len(ids) == len(set(ids)) and all(re.match(r"^B\d{2}_[A-Z0-9_]+$", x) for x in ids)


def attention_cadence_errors(beats: Iterable[Beat], max_span_s: float = 3.5) -> list[str]:
    errors: list[str] = []
    for b in beats:
        if b.attention_refresh not in ATTENTION_REFRESH_TYPES:
            errors.append(f"{b.id}: invalid attention refresh {b.attention_refresh}")
        if b.target_duration_s > max_span_s and b.attention_refresh == "PAUSE" and not b.text.strip():
            errors.append(f"{b.id}: empty attention span {b.target_duration_s:.2f}s exceeds limit")
        if not 0 <= float(b.cognitive_load) <= 1:
            errors.append(f"{b.id}: cognitive_load must be 0..1")
    return errors


def cognitive_load_warnings(beats: Iterable[Beat], high_threshold: float = .82, max_high_run: int = 3) -> list[str]:
    warnings: list[str] = []
    run = 0
    for b in beats:
        run = run + 1 if float(b.cognitive_load) >= high_threshold else 0
        if run > max_high_run:
            warnings.append(f"{b.id}: sustained high cognitive load; insert explanation/example/pause")
            break
    return warnings


def semantic_dead_span_errors(beats: Iterable[Beat], max_dead_span_s: float = 3.5) -> list[str]:
    # Backward-compatible alias. Attention refresh, not raw novelty, is the actual invariant.
    return attention_cadence_errors(beats, max_dead_span_s)


def simple_language_warnings(text: str, max_sentence_words: int = 22) -> list[str]:
    warnings: list[str] = []
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    for i, sentence in enumerate(sentences):
        words = re.findall(r"\b[\wÁÉÍÓÚÜÑáéíóúüñ-]+\b", sentence)
        if len(words) > max_sentence_words:
            warnings.append(f"sentence {i + 1} has {len(words)} words")
    jargon = re.findall(r"\b(?:orquestaci[oó]n|consistencia|asincr[oó]n|infraestructura|arquitectura|pipeline|framework)\w*\b", text, re.I)
    if len(jargon) >= 4:
        warnings.append("high jargon density; simplify or explain terms")
    return warnings


def estimate_duration(text: str, words_per_second: float = 2.55,
                      comma_cost_s: float = .10, sentence_cost_s: float = .22,
                      ellipsis_cost_s: float = .32, colon_cost_s: float = .16) -> float:
    words = re.findall(r"\b[\wÁÉÍÓÚÜÑáéíóúüñ-]+\b", text)
    base = len(words) / max(words_per_second, .1)
    pauses = (text.count(",") * comma_cost_s +
              sum(text.count(x) for x in (".", "?", "!")) * sentence_cost_s +
              text.count("…") * ellipsis_cost_s + text.count(":") * colon_cost_s)
    return round(base + pauses, 3)


def compile_tts_text(display_text: str, overrides: dict[str, str]) -> str:
    out = display_text
    for source in sorted(overrides, key=len, reverse=True):
        out = re.sub(re.escape(source), overrides[source], out, flags=re.IGNORECASE)
    return out


def _beat_from_dict(raw: dict[str, Any]) -> Beat:
    normalized = dict(raw)
    normalized["edit_cues"] = tuple(raw.get("edit_cues", []))
    normalized["claim_ids"] = tuple(raw.get("claim_ids", []))
    allowed = Beat.__dataclass_fields__.keys()
    return Beat(**{k: v for k, v in normalized.items() if k in allowed})


def preflight_manifest(manifest: dict[str, Any], profile: dict[str, Any]) -> PreflightResult:
    errors: list[str] = []
    warnings: list[str] = []
    display = manifest.get("script_display_text", "")
    tts = manifest.get("script_tts_text", "")
    beats = [_beat_from_dict(b) for b in manifest.get("semantic_beats", [])]
    if not display or not tts:
        errors.append("display and TTS script are required and must remain separate fields")
    if not manifest.get("source_refs"):
        errors.append("source provenance required")
    if manifest.get("viral_driver") not in DRIVERS:
        errors.append("invalid primary viral driver")
    if not manifest.get("moral"):
        errors.append("moral/payoff required")
    if not manifest.get("cta"):
        errors.append("CTA contract required")
    if not stable_beat_ids(beats):
        errors.append("semantic beat IDs must be unique and stable")
    errors.extend(attention_cadence_errors(beats))
    errors.extend(validate_claim_lineage(manifest))
    extra_protected = manifest.get("tts_protected_tokens", [])
    errors.extend(tts_integrity_errors(display, tts, extra_protected=extra_protected))
    warnings.extend(simple_language_warnings(display))
    warnings.extend(cognitive_load_warnings(beats))
    estimate = estimate_duration(
        tts,
        words_per_second=float(profile.get("initial_words_per_second", 2.55)),
        comma_cost_s=float(profile.get("pause_cost_s", {}).get("comma", .10)),
        sentence_cost_s=float(profile.get("pause_cost_s", {}).get("sentence", .22)),
        ellipsis_cost_s=float(profile.get("pause_cost_s", {}).get("ellipsis", .32)),
        colon_cost_s=float(profile.get("pause_cost_s", {}).get("colon", .16)),
    )
    if estimate < float(profile.get("duration_hard_min_s", 30)) or estimate > float(profile.get("duration_hard_max_s", 45)):
        errors.append(f"estimated duration {estimate:.2f}s outside hard range")
    decision = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return PreflightResult(ok=not errors, errors=tuple(errors), warnings=tuple(warnings), estimated_duration_s=estimate, decision=decision)


def serialize_strategy(primary_driver: str, angles: list[AngleCandidate], hooks: list[HookCandidate], beats: list[Beat]) -> dict[str, Any]:
    return {
        "primary_driver": primary_driver,
        "angles": [asdict(x) for x in rank_angles(angles)],
        "hooks": [asdict(x) for x in rank_hooks(hooks)],
        "beats": [asdict(x) for x in beats],
    }
