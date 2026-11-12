"""Text normalisation + n-gram shingles for near-duplicate detection.

Normalisation is deterministic: whitespace and punctuation are removed and every
digit collapses to ``0`` so syndicated copies with different timestamps still
share shingles. Shingles are character n-grams (default 4) which is a practical
approximation for Chinese without a tokenizer.
"""
import re
import unicodedata

_WS = re.compile(r"\s+")
_DIGIT = re.compile(r"\d+")


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).lower()
    text = _DIGIT.sub("0", text)
    text = _WS.sub("", text)
    dropped = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat.startswith("P") or cat.startswith("S") or cat.startswith("Z") or cat.startswith("C"):
            continue
        dropped.append(ch)
    return "".join(dropped)


def shingles(normalized: str, size: int = 4) -> set[str]:
    if not normalized:
        return set()
    if len(normalized) <= size:
        return {normalized}
    return {normalized[i : i + size] for i in range(len(normalized) - size + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def chinese_char_count(text: str) -> int:
    return len([ch for ch in (text or "") if not ch.isspace()])
