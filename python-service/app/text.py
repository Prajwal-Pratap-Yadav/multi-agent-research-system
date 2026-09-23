"""Lightweight text utilities used by the heuristic agent paths."""

from __future__ import annotations

import re

STOPWORDS = frozenset(
    """a an and are as at be by can do does for from has have how in is it its of on or
    that the their this to was were what when where which who why will with about into
    than then there these those they vs versus between""".split()
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_WORD = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9\-]*")


def keywords(text: str) -> list[str]:
    """Return lowercase, de-duplicated, non-stopword tokens in order of appearance."""
    seen: dict[str, None] = {}
    for token in _WORD.findall(text.lower()):
        if token not in STOPWORDS and len(token) > 1:
            seen.setdefault(token, None)
    return list(seen)


def split_sentences(text: str) -> list[str]:
    """Split prose into sentences, dropping fragments shorter than 30 characters."""
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if len(s.strip()) >= 30]


def relevance(sentence: str, terms: list[str]) -> float:
    """Score a sentence by the fraction of ``terms`` it contains (0.0 - 1.0)."""
    if not terms:
        return 0.0
    tokens = set(_WORD.findall(sentence.lower()))
    return sum(1 for t in terms if t in tokens) / len(terms)
