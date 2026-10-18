"""Region partitions (§13.2, INV-6, DET-9, DEC-21, DEC-22, TEST6-9).

Partition (i): every akṣara gets exactly one label. Partition (ii): every code
point of `[0, len(text))` belongs to exactly one character region. Verse covers
are placed first (attachment policy §31.3); whitespace/punctuation runs touching a
verse cover become `separator`; everything else not verse/excluded/uncertain is prose.
"""
from __future__ import annotations

from typing import Sequence

from padya.scanner import AksharaStream
from padya.types import Span

PROSE, SEPARATOR = "prose", "separator"


def syllable_labels(stream: AksharaStream, verses: Sequence[tuple[str, int, int]],
                    uncertain: set[int]) -> list[str]:
    labels = ["excluded" if a.excluded else PROSE for a in stream.aksharas]
    for vid, s, e in verses:
        for i in range(s, e):
            labels[i] = f"verse:{vid}"
    for i in uncertain:
        if labels[i] == PROSE:
            labels[i] = "uncertain"
    return labels


def syllable_regions(stream: AksharaStream, labels: list[str], p_verse: Sequence[float | None],
                     alternatives: dict[int, list[str]]) -> list[dict]:
    regions, i, n = [], 0, len(labels)
    while i < n:
        j = i
        while j < n and labels[j] == labels[i]:
            j += 1
        probs = [p for p in p_verse[i:j] if p is not None]
        alts = sorted({c for k in range(i, j) for c in alternatives.get(k, [])})
        regions.append({
            "partition": "syllable", "start": stream.aksharas[i].src.start, "end": stream.aksharas[j - 1].src.end,
            "syllables": [i, j], "label": labels[i], "syllable_count": j - i,
            "p_verse_lattice_mean": round(sum(probs) / len(probs), 9) if probs else None,
            "p_verse_lattice_max": round(max(probs), 9) if probs else None,
            "alternatives": alts[:3],
        })
        i = j
    return regions


def char_regions(text: str, verse_covers: Sequence[tuple[str, Span]], excluded: Sequence[Span],
                 uncertain: Sequence[Span]) -> list[dict]:
    n = len(text)
    labels: list[str | None] = [None] * n
    for vid, cover in verse_covers:
        for i in range(cover.start, cover.end):
            labels[i] = f"verse:{vid}"
    for label, spans in (("excluded", excluded), ("uncertain", uncertain)):
        for span in spans:
            for i in range(span.start, span.end):
                if labels[i] is None:
                    labels[i] = label
    for i in range(n):
        if labels[i] is None:
            labels[i] = PROSE
    _mark_separators(text, labels)
    regions, i = [], 0
    while i < n:
        j = i
        while j < n and labels[j] == labels[i]:
            j += 1
        regions.append({"partition": "char", "start": i, "end": j, "label": labels[i]})
        i = j
    return regions


def _is_sep(ch: str) -> bool:
    return ch.isspace() or ch in "।॥,;:.!?\"'‘’“”-—–()[]{}|" or ch.isdigit()


def _mark_separators(text: str, labels: list) -> None:
    """Whitespace/punctuation runs directly touching a verse cover → separator."""
    n, i = len(text), 0
    while i < n:
        if labels[i] != PROSE or not _is_sep(text[i]):
            i += 1
            continue
        j = i
        while j < n and labels[j] == PROSE and _is_sep(text[j]):
            j += 1
        touches = (i > 0 and str(labels[i - 1]).startswith("verse:")) or \
                  (j < n and str(labels[j]).startswith("verse:"))
        if touches:
            for k in range(i, j):
                labels[k] = SEPARATOR
        i = j


def check_partition(regions: Sequence[dict], total: int) -> None:
    """INV-6: complete and overlap-free cover of [0, total)."""
    from padya.errors import ValidationError

    pos = 0
    for r in regions:
        if r["start"] != pos or r["end"] <= r["start"]:
            raise ValidationError(f"INV-6: char partition gap/overlap at {pos}")
        pos = r["end"]
    if pos != total:
        raise ValidationError(f"INV-6: char partition ends at {pos}, text length {total}")
