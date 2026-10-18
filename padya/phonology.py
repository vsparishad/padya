"""Phonological item stream and SLP1 analysis view (SV-9, OFF-1, OFF-9, EDGE-3…5).

Every source code point is covered by exactly one item (items tile the text), so
nothing is silently dropped (TEST6-8). The SLP1 analysis view is derived from the
items with many-to-many origin edges; it is disposable and never canonical.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from padya.devanagari import CONSONANTS, MATRAS, MODIFIERS, VOWELS, CharClass, classify
from padya.types import OriginEdge, Span

ItemKind = Literal["C", "V", "M", "AVA", "SEP", "PAUSE", "BARRIER"]

_SEP_CLASSES = {
    CharClass.SPACE: "space", CharClass.NEWLINE: "newline", CharClass.HYPHEN: "hyphen",
    CharClass.PUNCT: "punct", CharClass.DIGIT: "digit",
}


@dataclass(slots=True, frozen=True)
class Item:
    """One phonological or separator unit with its source span.

    kind C = consonant (dead when `dead`), V = vowel nucleus (implicit inherent `a`
    when `implicit`), M = modifier (anusvāra, visarga, candrabindu …), AVA =
    avagraha (silent, SC-9), SEP = word separator, PAUSE = daṇḍa, BARRIER = foreign
    script. An implicit vowel shares its consonant's source span (one-to-many).
    """

    kind: ItemKind
    slp1: str
    src: Span
    dead: bool = False
    implicit: bool = False
    detail: str = ""  # SEP: space/newline/hyphen/punct/digit; PAUSE: D1/D2; flags otherwise


def _absorb_marks(text: str, i: int) -> int:
    """Return the index after any combining marks starting at i (attach-to-previous policy)."""
    n = len(text)
    while i < n and classify(text[i]) is CharClass.MARK:
        i += 1
    return i


def _consonant(text: str, i: int, out: list[Item]) -> int:
    start, slp = i, CONSONANTS[text[i]]
    i = _absorb_marks(text, i + 1)
    cons_end = i
    nxt = classify(text[i]) if i < len(text) else None
    if nxt is CharClass.VIRAMA:
        i = _absorb_marks(text, i + 1)
        out.append(Item("C", slp, Span(start, i), dead=True))
    elif nxt is CharClass.MATRA:
        out.append(Item("C", slp, Span(start, cons_end)))
        m_end = _absorb_marks(text, i + 1)
        slp = MATRAS[text[i]]
        out.append(Item("V", slp, Span(i, m_end), detail="nonstandard_vowel" if slp == "?" else ""))
        i = m_end
    else:
        out.append(Item("C", slp, Span(start, cons_end)))
        out.append(Item("V", "a", Span(start, cons_end), implicit=True))
    return i


def _single(text: str, i: int, out: list[Item]) -> int:
    ch, cls = text[i], classify(text[i])
    end = _absorb_marks(text, i + 1)
    span = Span(i, end)
    if cls is CharClass.VOWEL:
        out.append(Item("V", VOWELS[ch], span, detail="nonstandard_vowel" if VOWELS[ch] == "?" else ""))
    elif cls is CharClass.MATRA:  # orphan vowel sign: keep it, flag it
        out.append(Item("V", MATRAS[ch], span, detail="orphan_matra"))
    elif cls is CharClass.MODIFIER:
        out.append(Item("M", MODIFIERS[ch], span))
    elif cls is CharClass.OM:  # ॐ = o + anusvāra realised by one code point
        out.append(Item("V", "o", span))
        out.append(Item("M", "M", span))
    elif cls is CharClass.AVAGRAHA:
        out.append(Item("AVA", "'", span))
    elif cls is CharClass.VIRAMA:  # orphan virama: non-syllabic, kept as punctuation
        out.append(Item("SEP", "", span, detail="punct"))
    elif cls is CharClass.DANDA:
        out.append(Item("PAUSE", "|", span, detail="D1"))
    elif cls is CharClass.DOUBLE_DANDA:
        out.append(Item("PAUSE", "||", span, detail="D2"))
    elif cls in _SEP_CLASSES:
        out.append(Item("SEP", " " if cls in (CharClass.SPACE, CharClass.NEWLINE) else "",
                        span, detail=_SEP_CLASSES[cls]))
    elif cls is CharClass.MARK:  # mark with nothing to attach to
        out.append(Item("SEP", "", span, detail="punct"))
    else:
        out.append(Item("BARRIER", "", span, detail="foreign"))
    return end


def tokenize(text: str) -> tuple[Item, ...]:
    """Split text into items that tile [0, len(text)) in order."""
    out: list[Item] = []
    i, n = 0, len(text)
    while i < n:
        if classify(text[i]) is CharClass.CONSONANT:
            i = _consonant(text, i, out)
        else:
            i = _single(text, i, out)
    return tuple(out)


@dataclass(slots=True, frozen=True)
class AnalysisView:
    """SLP1 analysis string with many-to-many origin edges (SV-9, OFF-1)."""

    slp1: str
    edges: tuple[OriginEdge, ...]
    edge_src_starts: tuple[int, ...]  # sorted index for bisect (OPS-2: precompute once)


def analysis_view(items: tuple[Item, ...]) -> AnalysisView:
    parts: list[str] = []
    edges: list[OriginEdge] = []
    pos = 0
    for item in items:
        out = item.slp1
        if not out:
            edges.append(OriginEdge(item.src, None, f"SV-9.tombstone.{item.detail}", "zero_analysis"))
            continue
        analysis = Span(pos, pos + len(out))
        if item.implicit:
            edges.append(OriginEdge(item.src, analysis, "SV-9.inherent_a", "expand"))
        else:
            kind = "copy" if len(out) == item.src.end - item.src.start else "contract"
            edges.append(OriginEdge(item.src, analysis, f"SV-9.{item.kind}", kind))
        parts.append(out)
        pos += len(out)
    return AnalysisView("".join(parts), tuple(edges), tuple(e.src.start for e in edges))
