"""Typed verse and pāda boundaries (OFF-7…OFF-12, §31, §41 EDGE-1…EDGE-8).

An offset is emitted only when the boundary is exactly between code points and
graphemes. Fused closers (SC-12, §31.1) follow the §31.3 attachment policy: a
grapheme shared with the closer is attached to the verse cover and typed
`inside_grapheme`; a vowel realising both sides is `shared_surface`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from padya.graphemes import is_grapheme_boundary
from padya.scanner import Akshara, AksharaStream
from padya.types import BoundaryAnchor, Span

_VOWEL_CHARS = set("aAiIuUfFxXeEoO")
# §31.1 consonant-sharing fused closers: (surface suffix after the verse's last akṣara, transformation)
_CONSONANT_FUSED = {"मिति": "m+i→mi", "दिति": "t+i→di", "निति": "n+i→ni", "रिति": "iH+i→ri"}
# §31.1 vowel coalescence: (verse-final vowel sign, rest of word, transformation)
_VOWEL_FUSED = {("े", "ति"): "a+i→e", ("ी", "ति"): "i+i→I"}


@dataclass(slots=True, frozen=True)
class EndTyping:
    cover_end: int
    anchor: BoundaryAnchor
    frame_overlap: Mapping | None


def _exact(text: str, offset: int, analysis_left: int | None, analysis_right: int | None,
           evidence: tuple[str, ...]) -> BoundaryAnchor:
    if is_grapheme_boundary(text, offset):
        return BoundaryAnchor("exact_between_codepoints", offset, None, analysis_left, analysis_right, None, evidence)
    return BoundaryAnchor("inside_grapheme", None, Span(max(0, offset - 1), offset + 1), analysis_left,
                          analysis_right, None, evidence + ("EDGE-1:not_grapheme_boundary",))


def start_anchor(text: str, stream: AksharaStream, s: int) -> BoundaryAnchor:
    a = stream.aksharas[s]
    prev = stream.aksharas[s - 1] if s > 0 else None
    if a.soft_start and prev is not None and not a.word_start and "'" in _avagraha_slp(text, prev):
        # §31.2 aH+a→o': the verse's initial a has no surface; the avagraha marks it
        return BoundaryAnchor("shared_surface", None, prev.src, None, s, "aH+a→o'", ("SC-9", "F-5"))
    return _exact(text, a.src.start, None, s, ("word_start" if a.word_start else "soft_start",))


def _avagraha_slp(text: str, a: Akshara) -> str:
    return "'" if "ऽ" in text[a.src.start:a.src.end] else ""


def _word_rest(stream: AksharaStream, e: int) -> tuple[Akshara, ...]:
    out = []
    aks = stream.aksharas
    for k in range(e, len(aks)):  # index loop: no O(n) tuple slice per verse
        a = aks[k]
        if a.word_start or a.soft_start:
            break
        out.append(a)
        if a.word_end:
            break
    return tuple(out)


def end_anchor(text: str, stream: AksharaStream, e: int, sc12: bool) -> EndTyping:
    last = stream.aksharas[e - 1]
    rest = _word_rest(stream, e)
    if last.word_end or not rest:
        return EndTyping(last.src.end, _exact(text, last.src.end, e - 1, None, ("word_end",)), None)
    surface_rest = text[rest[0].src.start:rest[-1].src.end]
    if sc12 and surface_rest in _CONSONANT_FUSED:
        shared = rest[0].src
        transformation = _CONSONANT_FUSED[surface_rest]
        overlap = {"closer": "इति", "surface": surface_rest, "covering_src": shared.as_list(),
                   "transformation": transformation}
        anchor = BoundaryAnchor("inside_grapheme", None, shared, e - 1, e, transformation, ("SC-12", "§31.1"))
        return EndTyping(shared.end, anchor, overlap)
    final_sign = text[last.src.end - 1]
    if sc12 and (final_sign, surface_rest) in _VOWEL_FUSED:
        shared = Span(last.src.end - 1, last.src.end)
        transformation = _VOWEL_FUSED[(final_sign, surface_rest)]
        overlap = {"closer": "इति", "surface": final_sign + surface_rest, "covering_src": shared.as_list(),
                   "transformation": transformation}
        anchor = BoundaryAnchor("shared_surface", None, shared, e - 1, e, transformation, ("SC-12", "§31.1"))
        return EndTyping(last.src.end, anchor, overlap)
    covering = Span(last.src.start, rest[0].src.end)
    anchor = BoundaryAnchor("unresolved", None, covering, e - 1, e, None, ("mid_word_end",))
    return EndTyping(last.src.end, anchor, None)


def onset_length(a: Akshara) -> int:
    for i, ch in enumerate(a.slp1):
        if ch in _VOWEL_CHARS:
            return i
    return len(a.slp1)


def pada_anchor(text: str, stream: AksharaStream, idx: int) -> BoundaryAnchor:
    """Boundary before akṣara `idx` (start of a non-initial pāda)."""
    a = stream.aksharas[idx]
    if a.word_start or a.soft_start:
        return _exact(text, a.src.start, idx - 1, idx, ("word_boundary",))
    if onset_length(a) <= 1:
        return _exact(text, a.src.start, idx - 1, idx, ("mid_word_single_onset",))
    # a consonant cluster straddles the pāda junction: part of it closes the previous pāda
    return BoundaryAnchor("inside_grapheme", None, a.src, idx - 1, idx, "cluster_split", ("mid_word_cluster",))
