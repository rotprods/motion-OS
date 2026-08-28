from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from typing import Iterable
import re

VERSION_PATTERN = re.compile(
    r"\b(?:"
    r"[A-Za-z][A-Za-z0-9_-]*-?\d+(?:\.\d+)+"
    r"|[A-Z][A-Za-z0-9_-]+\s+\d+(?:\.\d+)+"
    r"|(?i:versi[oó]n)\s+\d+(?:\.\d+)+"
    r")\b"
)

TOKEN_PATTERNS = {
    "PERCENT": re.compile(r"\b\d+(?:[.,]\d+)?\s?%"),
    "CURRENCY": re.compile(r"(?:[$€£]\s?\d[\d.,]*|\b\d[\d.,]*\s?(?:USD|EUR|GBP|d[oó]lares?|euros?|libras?)\b)", re.I),
    "DATE_OR_YEAR": re.compile(r"\b(?:19|20)\d{2}\b"),
    "DECIMAL": re.compile(r"\b\d+[.,]\d+\b"),
    "VERSION": VERSION_PATTERN,
    "URL": re.compile(r"https?://[^\s]+", re.I),
}

NUMBER_WORDS_ES = {
    "cero":"0","uno":"1","una":"1","dos":"2","tres":"3","cuatro":"4","cinco":"5","seis":"6","siete":"7","ocho":"8","nueve":"9",
    "diez":"10","once":"11","doce":"12","trece":"13","catorce":"14","quince":"15","dieciséis":"16","dieciseis":"16",
}

_SPOKEN_NUMBER = "|".join(sorted((re.escape(word) for word in NUMBER_WORDS_ES), key=len, reverse=True))
SPOKEN_PERCENT_PATTERN = re.compile(
    rf"\b(?P<number>\d+(?:[.,]\d+)?|{_SPOKEN_NUMBER})\s+(?:por\s+ciento|porcentaje)\b",
    re.I,
)
SPOKEN_CURRENCY_PATTERN = re.compile(
    rf"\b(?P<number>\d+(?:[.,]\d+)?|{_SPOKEN_NUMBER})\s+(?P<currency>d[oó]lares?|euros?|libras?)\b",
    re.I,
)

_CURRENCY_FAMILIES = {
    "USD": {"$", "usd", "dolar", "dólar", "dolares", "dólares"},
    "EUR": {"€", "eur", "euro", "euros"},
    "GBP": {"£", "gbp", "libra", "libras"},
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


def _numeric_value(text: str) -> Decimal | None:
    digit_match = re.search(r"\d+(?:[.,]\d+)?", text)
    if digit_match:
        raw = digit_match.group(0).replace(",", ".")
        try:
            return Decimal(raw)
        except InvalidOperation:
            return None
    normalized = text.casefold()
    for word, value in NUMBER_WORDS_ES.items():
        if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", normalized):
            return Decimal(value)
    return None


def _currency_family(text: str) -> str | None:
    normalized = text.casefold()
    words = set(re.findall(r"[$€£]|[a-záéíóú]+", normalized, re.I))
    for family, aliases in _CURRENCY_FAMILIES.items():
        if words & aliases:
            return family
    return None


def _version_signature(text: str) -> tuple[str, tuple[int, ...]] | None:
    if VERSION_PATTERN.fullmatch(text.strip()) is None:
        return None
    version_match = re.search(r"\d+(?:\.\d+)+", text)
    if not version_match:
        return None
    label = text[:version_match.start()].rstrip(" -").casefold()
    if not label:
        return None
    components = tuple(int(part) for part in version_match.group(0).split("."))
    return label, components


def _semantic_signature(token: ProtectedToken) -> object | None:
    if token.kind == "URL":
        return token.original
    if token.kind == "PERCENT":
        return _numeric_value(token.original)
    if token.kind == "CURRENCY":
        return (_numeric_value(token.original), _currency_family(token.original))
    if token.kind == "DATE_OR_YEAR":
        match = re.search(r"\b(?:19|20)\d{2}\b", token.original)
        return int(match.group(0)) if match else None
    if token.kind == "DECIMAL":
        return _numeric_value(token.original)
    if token.kind == "VERSION":
        return _version_signature(token.original)
    return token.original.casefold()


def _candidate_tokens(tts_text: str, kind: str) -> list[ProtectedToken]:
    candidates = [token for token in extract_protected_tokens(tts_text) if token.kind == kind]
    if kind == "PERCENT":
        candidates.extend(ProtectedToken("PERCENT", match.group(0)) for match in SPOKEN_PERCENT_PATTERN.finditer(tts_text))
    elif kind == "CURRENCY":
        candidates.extend(ProtectedToken("CURRENCY", match.group(0)) for match in SPOKEN_CURRENCY_PATTERN.finditer(tts_text))
    return candidates


def _semantic_token_present(token: ProtectedToken, tts_text: str) -> bool:
    if token.kind == "URL":
        return token.original in tts_text
    expected = _semantic_signature(token)
    if expected is None:
        return False
    for candidate in _candidate_tokens(tts_text, token.kind):
        if _semantic_signature(candidate) == expected:
            return True
    return False


def _proper_token_present(token: str, tts_text: str) -> bool:
    if not token:
        return True
    return re.search(rf"(?<!\w){re.escape(token)}(?!\w)", tts_text, re.I) is not None


def tts_integrity_errors(display_text: str, tts_text: str, *, extra_protected: Iterable[str] = ()) -> list[str]:
    errors: list[str] = []
    for token in extract_protected_tokens(display_text):
        if not _semantic_token_present(token, tts_text):
            errors.append(f"protected {token.kind} token changed or missing in TTS: {token.original}")
    for token in extra_protected:
        if not _proper_token_present(token, tts_text):
            errors.append(f"protected proper token changed or missing in TTS: {token}")
    return errors
