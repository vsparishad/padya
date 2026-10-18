"""Extended-grapheme safety (EDGE-1, OFF-2, OFF-10, EDGE-10) using pinned `regex` \\X."""
from __future__ import annotations

import regex

_GRAPHEME = regex.compile(r"\X")
_WINDOW = 32  # far longer than any realistic Devanagari cluster


def is_grapheme_boundary(text: str, offset: int) -> bool:
    """True iff `offset` is both a code-point and an extended-grapheme boundary."""
    if offset <= 0 or offset >= len(text):
        return 0 <= offset <= len(text)
    lo = offset - _WINDOW
    # restart segmentation at a guaranteed boundary: a newline or the text start
    nl = text.rfind("\n", max(0, lo), offset)
    start = 0 if lo <= 0 else (nl + 1 if nl >= 0 else lo)
    pos = start
    for m in _GRAPHEME.finditer(text, start, min(len(text), offset + _WINDOW)):
        if m.start() == offset:
            return True
        if m.start() > offset:
            return False
        pos = m.end()
    return pos == offset


def utf16_offset(text: str, offset: int) -> int:
    """Derived UTF-16 index of a code-point offset (OFF-6, EDGE-10)."""
    return offset + sum(1 for ch in text[:offset] if ord(ch) > 0xFFFF)


def utf8_offset(text: str, offset: int) -> int:
    return len(text[:offset].encode("utf-8"))
