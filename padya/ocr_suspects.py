"""Review-only near-miss verses: metrical stanzas damaged by one or two OCR errors.

The main detector accepts only exact metrical matches (tier T, zero edits). Printed
digests contain verses whose metre is broken by a dropped vowel sign or a lost
conjunct (`हतृ` for `हन्तृ`, `विकरम` for `विक्रम`). This pass runs after decoding, on
akṣaras no accepted verse covers, and proposes spans that fit a metre except for a
small number of syllable edits (substitution, extra or missing syllable).

These are never verses in `verses.jsonl` and never change the decoder: they are
written to `suspects.jsonl` with `release_decision: ocr_suspect_review` for a human
to confirm (blueprint M5 territory; §5.5 budgets, OCR events). Guards against prose:

- the span starts at a line start or right after a daṇḍa / verse number, and ends at
  a daṇḍa or verse number; it crosses no `॥` and no paragraph break;
- at most one edit per pāda, `max_edits_full` per stanza, `max_edits_half` per half;
- a full anuṣṭubh needs a visible half boundary (a daṇḍa or line break after pāda 2);
- fixed-pattern metres need word boundaries between pādas, and halves are proposed
  only for fixed-pattern metres with pādas of at least `min_half_pada` syllables
  (an anuṣṭubh half with one free edit is too easy for prose to satisfy).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from typing import Mapping, Sequence

from padya import DETECTOR_VERSION, SCHEMA_VERSION
from padya.metres import anustubh, sama
from padya.metres.anustubh import Profile
from padya.metres.registry import CompiledMetre
from padya.scanner import AksharaStream, contextual_final_weight

ANY = "X"  # pāda-final anceps slot in a pattern


@dataclass(slots=True, frozen=True)
class Shape:
    metre_id: str
    k: int  # pādas
    lengths: tuple[int, ...]
    patterns: tuple[tuple[str, ...], ...]  # admitted pattern set per pāda (final anceps as X)
    needs_word_breaks: bool  # pāda boundaries must fall on word boundaries
    half_break_after: int | None  # pāda index after which a daṇḍa/line break is required


def _anceps(p: str, final_anceps: bool) -> str:
    return p[:-1] + ANY if final_anceps else p


@lru_cache(maxsize=None)
def _anustubh_patterns(variants: tuple[str, ...], profile: Profile) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Admitted pāda strings; odd ones ordered pathyā first so ties prefer the commonest form."""
    lenient = Profile(profile.odd_forbidden, profile.even_forbidden, profile.cost_uncertain, "lenient")
    odd: list[str] = []
    even: set[str] = set()
    for v in anustubh.VARIANT_ORDER:
        if v not in variants:
            continue
        for bits in product("LG", repeat=anustubh.PADA):
            s = "".join(bits)
            if anustubh.odd_variant_ok(s, v, lenient) and _anceps(s, True) not in odd:
                odd.append(_anceps(s, True))
    for bits in product("LG", repeat=anustubh.PADA):
        s = "".join(bits)
        if anustubh.even_ok(s, profile):
            even.add(_anceps(s, True))
    return tuple(odd), tuple(sorted(even))


def shapes(variants: Sequence[str], profile: Profile, fixed: Mapping[str, CompiledMetre],
           min_half_pada: int, full_only: frozenset[str] = frozenset()) -> list[Shape]:
    """Searchable shapes. Metres in `full_only` get no half shapes (typo halves of short
    vṛttas are too easy for prose; reports/strict_vrttas.md)."""
    odd, even = _anustubh_patterns(tuple(variants), profile)
    out = [Shape("anustubh", 4, (8,) * 4, (odd, even, odd, even), False, 1)]
    for mid, m in fixed.items():
        odd_p, even_p = m.pada_patterns(fixed)
        odd_s = tuple(sorted({_anceps(p, m.final_anceps) for p in odd_p}))
        even_s = tuple(sorted({_anceps(p, m.final_anceps) for p in even_p}))
        for k in (4, 2):
            if k == 2 and mid in full_only:
                continue
            for lengths in sama.length_options(m, fixed, k):
                if k == 2 and min(lengths) < min_half_pada:
                    continue
                pats = tuple(tuple(x for x in (odd_s if p % 2 == 0 else even_s) if len(x) == n)
                             for p, n in enumerate(lengths))
                out.append(Shape(mid, k, lengths, pats, True, None))
    return out


def _match(o: str, p: str) -> bool:
    return p == ANY or o == "?" or o == p


@lru_cache(maxsize=200_000)
def _distance(obs: str, pats: tuple[str, ...]) -> tuple[int, str, tuple[tuple[str, int], ...]]:
    """Min edit distance of `obs` to any pattern, with the edit operations of the best one.

    Unit-cost edits: 'sub' (one syllable has the wrong weight), 'extra' (an inserted
    syllable), 'missing' (a dropped syllable), and the two OCR-specific ones:
    'split' — a heavy syllable read as two light ones (a lost virāma: विक्रम → विकरम,
    `G` ↔ `LL`, same mātrā count) and 'merge' — the reverse (`LL` ↔ `G`).
    Ops are (kind, obs_index); 'missing' names the observed position before the gap.
    """
    best = (99, "", ())
    for p in pats:
        n, m = len(obs), len(p)
        if abs(n - m) >= best[0] + 1:
            continue
        inf = 99
        d = [[inf] * (m + 1) for _ in range(n + 1)]
        d[0][0] = 0
        for i in range(n + 1):
            for j in range(m + 1):
                if i == 0 and j == 0:
                    continue
                c = inf
                if i and j:
                    c = min(c, d[i - 1][j - 1] + (0 if _match(obs[i - 1], p[j - 1]) else 1))
                if i:
                    c = min(c, d[i - 1][j] + 1)
                if j:
                    c = min(c, d[i][j - 1] + 1)
                if i >= 2 and j and obs[i - 2:i] == "LL" and p[j - 1] in ("G", ANY):
                    c = min(c, d[i - 2][j - 1] + 1)
                if i and j >= 2 and obs[i - 1] == "G" and p[j - 2:j] == "LL":
                    c = min(c, d[i - 1][j - 2] + 1)
                d[i][j] = c
        if d[n][m] < best[0]:
            ops, i, j = [], n, m
            while i or j:
                here = d[i][j]
                if i and j and here == d[i - 1][j - 1] + (0 if _match(obs[i - 1], p[j - 1]) else 1):
                    if not _match(obs[i - 1], p[j - 1]):
                        ops.append(("sub", i - 1))
                    i, j = i - 1, j - 1
                elif i >= 2 and j and obs[i - 2:i] == "LL" and p[j - 1] in ("G", ANY) and here == d[i - 2][j - 1] + 1:
                    ops.append(("split", i - 2))
                    i, j = i - 2, j - 1
                elif i and j >= 2 and obs[i - 1] == "G" and p[j - 2:j] == "LL" and here == d[i - 1][j - 2] + 1:
                    ops.append(("merge", i - 1))
                    i, j = i - 1, j - 2
                elif i and here == d[i - 1][j] + 1:
                    ops.append(("extra", i - 1))
                    i -= 1
                else:
                    ops.append(("missing", i))
                    j -= 1
            best = (d[n][m], p, tuple(reversed(ops)))
    return best


# Visarga sandhi before a voiceless stop (-āḥ te → -āste, -aḥ ca → -aśca, -aḥ ṭī → -aṣṭī) fuses
# the pāda boundary into one written word; the boundary akṣara then starts with sibilant+stop.
SANDHI_JOIN = frozenset(a + b for a in "sSz" for b in "tTcCwW")
MAX_FUSED_BOUNDARIES = 1  # per suspect, full stanzas only


def _boundary_ok(a, shape: Shape, fused: int) -> tuple[bool, int]:
    """(allowed, fused boundaries used so far) for a pāda boundary at akṣara `a`."""
    if not shape.needs_word_breaks or a.word_start or a.soft_start:
        return True, fused
    if shape.k == 4 and fused < MAX_FUSED_BOUNDARIES and a.slp1[:2] in SANDHI_JOIN:
        return True, fused + 1
    return False, fused


def _fit(lg: str, shape: Shape, s: int, aks, per_pada: int, budget: int):
    """Best segmentation of lg into the shape's pādas (DP); returns (cost, segments) or None."""
    n = len(lg)
    # state: (position, fused boundaries) -> (cost, back-pointer)
    table: list[dict[tuple[int, int], tuple[int, tuple | None]]] = [{(0, 0): (0, None)}]
    for p, length in enumerate(shape.lengths):
        nxt: dict[tuple[int, int], tuple[int, tuple]] = {}
        for pred, (c, _) in table[-1].items():
            i, fused = pred
            if p:
                ok, fused = _boundary_ok(aks[s + i], shape, fused)
                if not ok:
                    continue
            if p and shape.half_break_after is not None and p == shape.half_break_after + 1:
                a = aks[s + i]
                if not (a.line_start or a.delim_before):
                    continue
            for dl in range(-per_pada, per_pada + 1):  # ±1 for normal suspects
                j = i + length + dl
                if j > n or j <= i:
                    continue
                cost, pat, ops = _distance(lg[i:j], shape.patterns[p])
                if cost > per_pada or c + cost > budget:
                    continue
                key = (j, fused)
                if key not in nxt or c + cost < nxt[key][0]:
                    nxt[key] = (c + cost, (i, pat, ops, pred))
        table.append(nxt)
    ends = [k for k in table[-1] if k[0] == n]
    if not ends:
        return None
    key = min(ends, key=lambda k: table[-1][k][0])
    total = table[-1][key][0]
    segs = []
    for p in range(shape.k, 0, -1):
        _, (i, pat, ops, prev) = table[p][key]
        segs.append((i, key[0], pat, ops))
        key = prev
    return total, list(reversed(segs))



def _complement_half(aks, s: int, e: int, accepted_halves: set[tuple[int, int]]) -> bool:
    """An anuṣṭubh half may be a suspect only as the damaged twin of a detected half of the
    same stanza: directly after a half that ends at a single daṇḍa (and itself ending at ॥ or
    a verse number), or directly before a half that ends at ॥ / a verse number."""
    for hs, he in accepted_halves:
        if he == s and aks[he - 1].delim_after == "D1" and (aks[e - 1].delim_after == "D2" or aks[e - 1].verse_num_after):
            return True
        if hs == e and aks[e - 1].delim_after == "D1" and (aks[he - 1].delim_after == "D2" or aks[he - 1].verse_num_after):
            return True
    return False


def find_suspects(doc, stream: AksharaStream, accepted: Sequence[tuple[int, int]], variants: Sequence[str],
                  profile: Profile, fixed: Mapping[str, CompiledMetre], cfg: Mapping, run_id: str,
                  accepted_halves: Sequence[tuple[int, int]] = (), full_only: frozenset[str] = frozenset()) -> list[dict]:
    aks = stream.aksharas
    halves = set(accepted_halves)
    covered = [0] * len(aks)
    for s, e in accepted:
        for i in range(s, e):
            covered[i] = 1
    prefix = [0]
    for c in covered:
        prefix.append(prefix[-1] + c)
    max_full, max_half = int(cfg["max_edits_full"]), int(cfg["max_edits_half"])
    per_pada = int(cfg["max_edits_per_pada"])
    by_len: dict[int, list[Shape]] = {}
    for sh in shapes(variants, profile, fixed, int(cfg["min_half_pada"]), full_only):
        by_len.setdefault(sum(sh.lengths), []).append(sh)
    odd, even = _anustubh_patterns(tuple(variants), profile)
    twin = Shape("anustubh", 2, (8, 8), (odd, even), False, None)  # only via _complement_half
    by_len.setdefault(16, []).append(twin)
    lo_len, hi_len = min(by_len) - max_full, max(by_len) + max_full
    found = []
    for run in stream.runs:
        for s in range(run.start, run.end):
            a = aks[s]
            if covered[s] or not a.word_start:
                continue
            if not (a.line_start or a.delim_before or s == run.start or (s and aks[s - 1].verse_num_after)):
                continue
            for e in range(s + 1, min(run.end, s + hi_len) + 1):
                if prefix[e] - prefix[s]:
                    break  # ran into an accepted verse; longer windows only overlap more
                x = aks[e - 1]
                if e - 1 > s and (x.delim_before == "D2" or x.para_start):
                    break  # never cross a double daṇḍa or a paragraph break
                if e - s < lo_len or not (x.word_end and (x.delim_after or x.verse_num_after)):
                    continue
                if any(aks[k].verse_num_after for k in range(s, e - 1)):
                    break  # never swallow a verse number
                w, lg = e - s, None
                for total, group in by_len.items():
                    for sh in group:
                        budget = max_full if sh.k == 4 else max_half
                        if abs(total - w) > budget:
                            continue
                        if sh is twin and not _complement_half(aks, s, e, halves):
                            continue
                        if lg is None:
                            ws = [y.weight for y in aks[s:e]]
                            ws[-1] = contextual_final_weight(aks[e - 1])
                            lg = "".join(ws)
                        fit = _fit(lg, sh, s, aks, per_pada, budget)
                        if fit and fit[0] >= 1:
                            found.append((fit[0], -sh.k, s, sh.metre_id, e, sh, fit[1]))
    found.sort(key=lambda f: (f[1], f[0], f[2], f[3]))  # whole stanzas first, then fewest edits
    taken = [False] * len(aks)
    out = []
    for cost, _, s, _, e, sh, segs in found:
        if any(taken[s:e]):
            continue
        for i in range(s, e):
            taken[i] = True
        out.append(_record(doc, stream, s, e, sh, segs, cost, run_id))
    return sorted(out, key=lambda r: r["start"])


def _record(doc, stream, s, e, sh: Shape, segs, cost: int, run_id: str) -> dict:
    aks, text = stream.aksharas, doc.text
    start, end = aks[s].src.start, aks[e - 1].src.end
    marks = []
    for p, (i, j, _, ops) in enumerate(segs):
        for kind, oi in ops:
            if kind in ("missing", "extra"):  # which syllable is missing/extra is ambiguous: flag the pāda
                a, b = aks[s + i].src.start, aks[s + j - 1].src.end
                marks.append({"start": a, "end": b, "kind": f"{kind}_in_pada", "pada": p + 1, "syllable": None,
                              "text": text[a:b]})
                continue
            idx = s + i + min(oi, j - i - 1)
            last = min(idx + 1, s + j - 1) if kind == "split" else idx  # a split spans two observed syllables
            marks.append({"start": aks[idx].src.start, "end": aks[last].src.end, "kind": kind, "pada": p + 1,
                          "syllable": oi + 1, "text": text[aks[idx].src.start:aks[last].src.end]})
    marks = list({(m["start"], m["end"], m["kind"]): m for m in marks}.values())  # one mark per span and kind
    key = f"suspect|{doc.text_sha256}|{start}|{end}|{sh.metre_id}"
    lg = "".join(contextual_final_weight(aks[x]) if x == e - 1 else aks[x].weight for x in range(s, e))
    return {
        "schema_version": SCHEMA_VERSION, "suspect_id": "s_" + hashlib.sha256(key.encode()).hexdigest()[:20],
        "source_id": doc.doc_id, "source_sha256": doc.text_sha256, "detector_version": DETECTOR_VERSION,
        "run_id": run_id, "start": start, "end": end, "text": text[start:end], "offset_unit": "unicode_codepoint",
        "metre_id": sh.metre_id, "partial": "full" if sh.k == 4 else "half", "edits": cost,
        "observed_lg": [lg[i:j] for i, j, _, _ in segs],
        "expected_lg": [pat.replace(ANY, "x") for _, _, pat, _ in segs],
        "suspect_syllables": marks, "release_decision": "ocr_suspect_review",
        "calibrated_probability": None, "confidence_status": "uncalibrated",
    }
