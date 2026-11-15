"""Formatting-only matching with a character map into the untouched source.

No case folding, punctuation substitution, numeric repair or approximate search.
Line-break hyphens are removed only when the joined alphabetic word is also
attested unbroken in the declared source chunk. Ordinary compounds keep '-'.
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class QuoteMatch:
    start: int
    end: int
    text: str


def _normalize(text: str, attested: set[str]):
    chars, spans = [], []
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\u00ad":
            i += 1
            continue
        if c == "-":
            split = re.match(r"-[ \t]*\r?\n[ \t]*([A-Za-z]+)", text[i:])
            left = re.search(r"([A-Za-z]+)$", text[:i])
            if split and left:
                joined = left[1] + split[1]
                if joined not in attested:
                    chars.append("-")
                    spans.append((i, i + 1))
                i += split.start(1)
                continue
        if c.isspace():
            end = i + 1
            while end < len(text) and text[end].isspace():
                end += 1
            if chars and chars[-1] != " ":
                chars.append(" ")
                spans.append((i, end))
            i = end
            continue
        chars.append(c)
        spans.append((i, i + 1))
        i += 1
    if chars and chars[-1] == " ":
        chars.pop()
        spans.pop()
    return "".join(chars), spans


def resolve_quote(source: str, quote: str) -> tuple[QuoteMatch | None, str | None]:
    """Return a unique source slice, or 'missing' / 'ambiguous'."""
    attested = set(re.findall(r"\b[A-Za-z]+\b", source))
    normalized, mapping = _normalize(source, attested)
    needle, _ = _normalize(quote, attested)
    if not needle:
        return None, "missing"
    locations, cursor = set(), 0
    while (found := normalized.find(needle, cursor)) >= 0:
        locations.add((mapping[found][0], mapping[found + len(needle) - 1][1]))
        cursor = found + 1
    if len(locations) != 1:
        return None, "ambiguous" if locations else "missing"
    start, end = next(iter(locations))
    return QuoteMatch(start, end, source[start:end]), None
