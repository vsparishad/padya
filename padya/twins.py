"""Twin halves for the full-only metres (owner's twin rule, 2026-10-17).

A half of a full-only metre (indravajrā, upajāti, śālinī, …; profiles.yaml) whose two pādas
share one line is too easy for prose to match on weights alone (reports/strict_vrttas.md).
It is accepted when its twin is right beside it: the other half of the same stanza,
separated from it by a single daṇḍa, fits the same metre within TWIN_MAX_EDITS OCR edits.
Two adjacent near-matching halves are what a damaged stanza looks like and what prose
almost never produces. The damaged twin itself is then offered as a review-only typo half
(padya/ocr_suspects.py), never as a verse.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterator, Mapping

from padya.metres import sama
from padya.metres.registry import CompiledMetre
from padya.ocr_suspects import ANY, Shape, _fit
from padya.scanner import contextual_final_weight

TWIN_MAX_EDITS = 2  # per twin half; may fall in one pāda (e.g. a lost syllable plus a merge)
LENGTH_SLACK = TWIN_MAX_EDITS


def half_shapes(metre_id: str, metre: CompiledMetre, fixed: Mapping[str, CompiledMetre]) -> tuple[Shape, ...]:
    """The metre's half shapes (one per admitted pāda-length pair)."""
    return _half_shapes(metre_id, metre, tuple(sorted(fixed.items())))


@lru_cache(maxsize=None)
def _half_shapes(metre_id: str, metre: CompiledMetre, fixed_items: tuple) -> tuple[Shape, ...]:
    fixed = dict(fixed_items)
    odd_p, even_p = metre.pada_patterns(fixed)
    fin = metre.final_anceps
    odd_s = tuple(sorted({p[:-1] + ANY if fin else p for p in odd_p}))
    even_s = tuple(sorted({p[:-1] + ANY if fin else p for p in even_p}))
    out = []
    for lengths in sama.length_options(metre, fixed, 2):
        pats = tuple(tuple(x for x in (odd_s if i % 2 == 0 else even_s) if len(x) == n) for i, n in enumerate(lengths))
        out.append(Shape(metre_id, 2, lengths, pats, True, None))
    return tuple(out)


def _start_anchor(aks, t: int) -> bool:
    a = aks[t]
    return a.word_start and (a.line_start or a.para_start or bool(a.delim_before)
                             or (t > 0 and bool(aks[t - 1].verse_num_after)))


def _end_anchor(a) -> bool:
    return a.word_end and (bool(a.delim_after) or bool(a.verse_num_after))


def _hard_stop(a) -> bool:
    return a.delim_after == "D2" or bool(a.verse_num_after)


def twin_windows(aks, s: int, e: int, half_len: int) -> Iterator[tuple[int, int]]:
    """Windows that could be the other half of the stanza whose half is aks[s:e]: directly
    before it (ending at the single daṇḍa just before s) or directly after it (this half
    ending at a single daṇḍa), within LENGTH_SLACK syllables of the half length, never
    crossing ॥, a verse number or a paragraph break."""
    lo, hi = half_len - LENGTH_SLACK, half_len + LENGTH_SLACK
    if s > 0 and aks[s - 1].delim_after == "D1" and not aks[s].para_start:
        for t in range(s - 1, max(-1, s - hi - 1), -1):
            if t < s - 1 and _hard_stop(aks[t]):
                break
            if lo <= s - t <= hi and _start_anchor(aks, t):
                yield t, s
            if aks[t].para_start:
                break
    if aks[e - 1].delim_after == "D1" and e < len(aks) and not aks[e].para_start:
        for u in range(e + 1, min(len(aks), e + hi) + 1):
            if u - 1 > e and (_hard_stop(aks[u - 2]) or aks[u - 1].para_start):
                break
            if u - e >= lo and _end_anchor(aks[u - 1]):
                yield e, u


def fits(aks, t: int, u: int, shapes: tuple[Shape, ...], max_edits: int = TWIN_MAX_EDITS) -> int | None:
    """Fewest edits with which aks[t:u] fits one of the half shapes, or None."""
    ws = [a.weight for a in aks[t:u]]
    ws[-1] = contextual_final_weight(aks[u - 1])
    lg = "".join(ws)
    best = None
    for sh in shapes:
        if abs(sum(sh.lengths) - len(lg)) > max_edits:
            continue
        fit = _fit(lg, sh, t, aks, max_edits, max_edits)
        if fit and (best is None or fit[0] < best):
            best = fit[0]
    return best


def has_twin(aks, s: int, e: int, shapes: tuple[Shape, ...]) -> bool:
    """Does the half aks[s:e] have a twin half beside it that fits within TWIN_MAX_EDITS?"""
    return any(fits(aks, t, u, shapes) is not None for t, u in twin_windows(aks, s, e, e - s))


def twin_suspects(doc, stream, halves: list[tuple[int, int, str]], fixed: Mapping[str, CompiledMetre],
                  blocked: list[tuple[int, int]], run_id: str) -> list[dict]:
    """Review-only typo halves: the damaged twin beside each accepted one-line half of a
    full-only metre. `halves` are (start, end, metre_id) in akṣara indices; `blocked` are
    akṣara spans already covered by verses or other suspects."""
    from padya.ocr_suspects import _record  # local: ocr_suspects must not import this module
    aks = stream.aksharas
    taken = [False] * len(aks)
    for s, e in blocked:
        for i in range(s, e):
            taken[i] = True
    out = []
    for s, e, mid in halves:
        shapes = half_shapes(mid, fixed[mid], fixed)
        best = None
        for t, u in twin_windows(aks, s, e, e - s):
            if any(taken[t:u]):
                continue
            ws = [a.weight for a in aks[t:u]]
            ws[-1] = contextual_final_weight(aks[u - 1])
            lg = "".join(ws)
            for sh in shapes:
                if abs(sum(sh.lengths) - len(lg)) > TWIN_MAX_EDITS:
                    continue
                fit = _fit(lg, sh, t, aks, TWIN_MAX_EDITS, TWIN_MAX_EDITS)
                if fit and fit[0] >= 1 and (best is None or fit[0] < best[0]):
                    best = (fit[0], t, u, sh, fit[1])
        if best:
            cost, t, u, sh, segs = best
            for i in range(t, u):
                taken[i] = True
            out.append(_record(doc, stream, t, u, sh, segs, cost, run_id))
    return out
