from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable
import re

TOKEN_PATTERNS = {
    "PERCENT": re.compile(r"\b\d+(?:[.,]\d+)?\s?%"),
    "CURRENCY": re.compile(r"(?:[$€£]\s?\d[\d.,]*|\b\d[\d.,]*\s?(?:USD|EUR|GBP|d[oó]lares?|euros?)\b)", re.I),
    "DATE_OR_YEAR": re.compile(r"\b(?:19|20)\d{2}\b"),
    "DECIMAL": re.compile(r"\b\d+[.,]\d+\b"),
    "VERSION": re.compile(r"\b[A-Za-z][A-Za-z0-9_-]*[- ]?\d+(?:\.\d+)+\b"),
    "URL": re.compile(r"https?://[^\s]+", re.I),
}

NUMBER_WORDS_ES = {
    "cero":"0","uno":"1","una":"1","dos":"2","tres":"3","cuatro":"4","cinco":"5","seis":"6","siete":"7","ocho":"8","nueve":"9",
    "diez":"10","once":"11","doce":"12","trece":"13","catorce":"14","quince":"15","dieciséis":"16","dieciseis":"16",
}

@dataclass(frozen=True)
class ProtectedToken:
    kind: str
    original: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def extract_protected_tokens(text: str) -> list[ProtectedToken]:
    spans: list[tuple[int, int, ProtectedToken]] = []
    for kind, pattern in TOKEN_PATTERNS.items():
        for match in pattern.finditer(text):
            spans.append((match.start(), match.end(), ProtectedToken(kind, match.group(0))))
    spans.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    accepted: list[tuple[int, int, ProtectedToken]] = []
    for candidate in spans:
        if any(candidate[0] < end and candidate[1] > start for start, end, _ in accepted):
            continue
        accepted.append(candidate)
    return [x[2] for x in accepted]


def _digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def _semantic_token_present(token: ProtectedToken, tts_text: str) -> bool:
    if token.kind == "URL":
        return token.original in tts_text
    if token.kind in {"DATE_OR_YEAR", "DECIMAL", "PERCENT", "CURRENCY", "VERSION"}:
        digits = _digits(token.original)
        if digits and digits in _digits(tts_text):
            return True
        # Small-number phonetic fallback; intentionally conservative.
        normalized = tts_text.casefold()
        for word, value in NUMBER_WORDS_ES.items():
            normalized = re.sub(rf"\b{re.escape(word)}\b", value, normalized)
        return digits and digits in _digits(normalized)
    return token.original.casefold() in tts_text.casefold()


def tts_integrity_errors(display_text: str, tts_text: str, *, extra_protected: Iterable[str] = ()) -> list[str]:
    errors: list[str] = []
    for token in extract_protected_tokens(display_text):
        if not _semantic_token_present(token, tts_text):
            errors.append(f"protected {token.kind} token changed or missing in TTS: {token.original}")
    for token in extra_protected:
        if token and token.casefold() not in tts_text.casefold():
            errors.append(f"protected proper token changed or missing in TTS: {token}")
    return errors
