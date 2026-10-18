"""Stage 4: candidate generation (§6.2 B1/B2/B4/B5, §40 BASE-2, OPS-6, M2.5, BASE-7).

BASE-A proposes full 32-syllable pathyā windows at hard/soft word starts only.
A mode that lists vipulās (BASE-C) tries the same windows under the wider grammar,
passing visible word ends to the gate as caesura evidence. A mode whose
`pada_counts` include 2 also proposes **anchored** 16-syllable halves (AN-6, NEG-3,
DET-7): the half must start at a hard word start and end at a daṇḍa or verse number;
isolated halves without such an anchor are never proposed (BASE-8).
Each window passes the bitmask prefilter (reject-only) and then the full gate.
A candidate is not yet a verse: scoring and decoding decide (§40.2).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Mapping

from padya.config import Config
from padya.metres import anustubh
from padya.metres.anustubh import GateResult, Profile
from padya.metres import sama
from padya.metres.bitmask import masks_for, mismatch_lower_bound
from padya.metres.registry import CompiledMetre
from padya.scanner import AksharaStream
from padya.twins import half_shapes, has_twin


@dataclass(slots=True, frozen=True)
class Candidate:
    cand_id: str
    s: int  # akṣara index, inclusive
    e: int  # akṣara index, exclusive
    metre_id: str
    variant: tuple[str, ...]
    k: int
    origin: str
    tier_rule: str
    lg: str
    gate: GateResult
    cues: tuple[tuple[str, float], ...]  # observed only; not scored under BASE-A
    anchor: str = "none"  # for halves: "delimiter" | "verse_number" | "quote_close" | "iti_closer"
    pada_lengths: tuple[int, ...] = (8, 8, 8, 8)


@dataclass(slots=True, frozen=True)
class GenerationResult:
    candidates: tuple[Candidate, ...]
    counters: Mapping[str, int]
    search_incomplete: bool


def tier_budget(config: Config, noise: float | None) -> float:
    """§5.5: budget per 32 syllables; tier T is strict. `?` costs count against it."""
    tiers = config.weights["tiers"]
    if config.tier in ("T", "unspecified"):
        return float(tiers["T"]["budget32"])
    lo, hi = (("P_lo", "P_hi") if config.tier == "P" else ("R_lo", "R_mid"))
    band = lo if noise is None or noise < tiers[lo]["noise_max"] else hi
    return float(tiers[band]["budget32"])


def candidate_id(source_sha: str, s: int, e: int, metre: str, variant: tuple[str, ...], parse: str) -> str:
    """B5/OPS-4/INV-8: canonical key from source hash and observation, not detection order."""
    key = f"{source_sha}|{s}|{e}|{metre}|{','.join(variant)}|{parse}"
    return "c_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def _observed_cues(stream: AksharaStream, s: int, e: int) -> tuple[tuple[str, float], ...]:
    """C-2/C-3/C-5/C-6/C-8 observations recorded for BASE-B ablation (not scored)."""
    aks = stream.aksharas
    first, last = aks[s], aks[e - 1]
    internal_d2 = sum(1 for a in aks[s + 1:e] if a.delim_before == "D2")
    pada_breaks = sum(1 for p in range(8, e - s, 8) if aks[s + p].word_start or aks[s + p].soft_start)  # anuṣṭubh grid
    return (
        ("start_at_delimiter_or_line", float(bool(first.delim_before or first.line_start))),
        ("end_at_word_end", float(last.word_end)),
        ("end_at_delimiter", float(bool(last.delim_after))),
        ("verse_number_after_end", last.verse_num_conf if last.verse_num_after else 0.0),
        ("pada_breaks_on_word_boundary", float(pada_breaks)),
        ("internal_d2", float(internal_d2)),
    )


def crosses_structure(aks, s: int, e: int, pada_lengths) -> bool:
    """B3 as a hard rule (BASE-C `reject_crossing`): a verse window may not contain a ॥, a
    verse number, or a single daṇḍa that is not at one of its pāda boundaries. Such windows
    are the half-shifted errors (end of one stanza + start of the next) or prose labels
    (`वसिष्ठः ।`) glued to a verse."""
    bounds, acc = set(), 0
    for n in pada_lengths[:-1]:
        acc += n
        bounds.add(s + acc)
    for i in range(s + 1, e):
        d = aks[i].delim_before
        if d == "D2" or (d == "D1" and i not in bounds) or aks[i - 1].verse_num_after:
            return True
    return False


CLOSING_QUOTES = ("’", "”", "\"", "'", "»")
ITI_FORMS = ("इति", "इत्यादि", "इत्येव", "इत्युक्त")


def _half_window_ok(aks, s: int, e: int) -> bool:
    """Cheap precondition for the twin search: the half is anchored at both ends."""
    return aks[s].word_start and aks[e - 1].word_end and bool(aks[e - 1].delim_after or aks[e - 1].verse_num_after)


def _half_anchor(aks, s: int, e: int, text: str | None) -> str | None:
    """NEG-3/DET-7/AN-7 anchor for a 16-syllable window, or None if it has none.

    Anchors, in priority order: a verse number after the half (SV-4); a daṇḍa right
    after it; a closing quotation mark or an `इति` closer immediately after it (§31
    citation frame, minimal form). A half followed by more quoted prose has none.
    """
    first, last = aks[s], aks[e - 1]
    if not first.word_start or not last.word_end:
        return None
    if any(a.delim_before == "D2" or a.para_start for a in aks[s + 1:e]):
        return None  # a half never crosses a double daṇḍa or a paragraph break (B3, NEG-3)
    if last.verse_num_after:
        return "verse_number"
    if last.delim_after in ("D1", "D2"):
        return "delimiter"
    if text is not None:
        after = text[last.src.end:last.src.end + 16].lstrip(" \t\n")
        if after.startswith(CLOSING_QUOTES):
            return "quote_close"
        if after.startswith(ITI_FORMS):
            return "iti_closer"
    return None


def generate(stream: AksharaStream, source_sha: str, config: Config, noise: float | None,
             text: str | None = None, fixed_metres: Mapping[str, CompiledMetre] | None = None) -> GenerationResult:
    """`fixed_metres`: id → compiled sama/mixture/ardhasama entries to try besides anuṣṭubh."""
    mode = config.mode
    fixed = dict(fixed_metres or {})
    fixed_pats = {mid: m.pada_patterns(fixed)[0] for mid, m in fixed.items()}
    variants = tuple(mode["anustubh_variants"])
    anustubh.check_variants(variants)
    profile = Profile.from_config(config.profile, config.weights)
    budget = tier_budget(config, noise)
    lengths = tuple(sorted({int(k) * anustubh.PADA for k in mode["pada_counts"]}, reverse=True))
    if any(n not in (anustubh.VERSE, anustubh.HALF) for n in lengths):
        raise ValueError(f"unsupported pada_counts {mode['pada_counts']}; only 4 and 2 are implemented")
    masks = {n: masks_for(variants, n // anustubh.PADA) for n in lengths}
    anchors = set(mode["start_anchors"])
    reject_crossing = bool(mode.get("reject_crossing", False))
    full_only = frozenset(mode.get("full_only_metres", ()))  # no anchored halves (reports/strict_vrttas.md)
    # ... unless the two pādas stand on separate lines (layout evidence prose rarely has)
    line_halves = bool(mode.get("full_only_line_halves", False))
    twin_halves = bool(mode.get("full_only_twin_halves", False))
    counters = {"crossing_rejects": 0, "window_starts": 0, "starts_skipped_not_anchor": 0, "windows_too_short": 0,
                "gate_calls": 0, "prefilter_rejects": 0, "failed_first_pada": 0,
                "half_windows_unanchored": 0, "half_candidates": 0, "fixed_metre_gate_calls": 0,
                "fixed_metre_candidates": 0,
                "candidate_arcs": 0, "density_cap_hits": 0}
    seen: dict[str, Candidate] = {}
    aks = stream.aksharas
    for run in stream.runs:
        for s in range(run.start, run.end):
            a = aks[s]
            if not ((a.word_start and "word_start" in anchors) or (a.soft_start and "soft_start" in anchors)):
                counters["starts_skipped_not_anchor"] += 1
                continue
            counters["window_starts"] += 1
            for n in lengths:
                e = s + n
                if e > run.end:
                    counters["windows_too_short"] += 1
                    continue
                anchor = "none"
                if n == anustubh.HALF:
                    anchor = _half_anchor(aks, s, e, text)
                    if anchor is None:
                        counters["half_windows_unanchored"] += 1
                        continue
                if reject_crossing and crosses_structure(aks, s, e, (anustubh.PADA,) * (n // anustubh.PADA)):
                    counters["crossing_rejects"] += 1
                    continue
                lg = "".join(x.weight for x in aks[s:e])
                if mismatch_lower_bound(lg, masks[n]) > 0:  # SRCH-1: exact zero-edit mode only
                    counters["prefilter_rejects"] += 1
                    continue
                counters["gate_calls"] += 1
                word_ends = [x.word_end for x in aks[s:e]]
                result = anustubh.gate(lg, profile, budget, variants, word_ends)
                if not result.ok:
                    if result.reason == "pada1":
                        counters["failed_first_pada"] += 1
                    continue
                odd_variants = tuple(v for v in result.variants if v != "even")
                k = n // anustubh.PADA
                cid = candidate_id(source_sha, s, e, "anustubh", odd_variants, "default")
                if cid not in seen:
                    seen[cid] = Candidate(cid, s, e, "anustubh", odd_variants, k, "free" if k == 4 else "anchored_half",
                                          "B1" if k == 4 else "B2", lg, result, _observed_cues(stream, s, e), anchor,
                                          (anustubh.PADA,) * k)
                    if k == 2:
                        counters["half_candidates"] += 1
            for mid, metre in fixed.items():
                for k, plens in ((k, pl) for k in sorted({int(x) for x in mode["pada_counts"]}, reverse=True)
                                 for pl in sama.length_options(metre, fixed, k)):
                    e = s + sum(plens)
                    if e > run.end:
                        continue
                    anchor = "none"
                    if k == 2 and mid in full_only and not (line_halves and aks[s + plens[0]].line_start):
                        # one-line half: only with a near-matching twin half beside it (padya/twins.py)
                        if not (twin_halves and _half_window_ok(aks, s, e)
                                and has_twin(aks, s, e, half_shapes(mid, metre, fixed))):
                            continue
                        counters["twin_halves"] = counters.get("twin_halves", 0) + 1
                    if k == 2:
                        anchor = _half_anchor(aks, s, e, text)
                        if anchor is None:
                            continue
                    if reject_crossing and crosses_structure(aks, s, e, plens):
                        counters["crossing_rejects"] += 1
                        continue
                    lg = "".join(x.weight for x in aks[s:e])
                    if sama.prefilter_reject(lg, fixed_pats[mid], metre.final_anceps):
                        continue
                    counters["fixed_metre_gate_calls"] += 1
                    result = sama.gate(lg, metre, fixed, profile.cost_uncertain, budget, k, plens)
                    if not result.ok:
                        continue
                    cid = candidate_id(source_sha, s, e, mid, result.variants, "default")
                    if cid not in seen:
                        seen[cid] = Candidate(cid, s, e, mid, result.variants, k, "free" if k == 4 else "anchored_half",
                                              "B1" if k == 4 else "B2", lg, result, _observed_cues(stream, s, e),
                                              anchor, plens)
                        counters["fixed_metre_candidates"] += 1
    cands = tuple(sorted(seen.values(), key=lambda c: (c.s, c.e, c.cand_id)))
    counters["candidate_arcs"] = len(cands)
    cap = float(config.weights["caps"]["candidates_per_1k_syllables"])
    incomplete = len(cands) > cap * max(len(aks), 1000) / 1000.0
    counters["density_cap_hits"] = int(incomplete)
    return GenerationResult(cands, counters, incomplete)
