"""Fixed-pattern metres: sama-vṛtta, upajāti mixtures and ardhasama-vṛtta (§5.3, SC-6, AN-4).

Every pāda must equal one of the metre's admitted patterns slot for slot, except the
pāda-final slot, which is anceps when the registry says so (SC-6: inside the metrical
hypothesis only; the scanner keeps the surface weight). `?` slots match anything and are
charged like anuṣṭubh uncertain slots (SC-7). A mixture (upajāti) lets each pāda pick any
component independently; the chosen component ids are reported as the per-pāda variant.
"""
from __future__ import annotations

from itertools import product
from math import log
from typing import Mapping, Sequence

from padya.metres.anustubh import GateResult
from padya.metres.registry import CompiledMetre


def match_pada(lg: str, pattern: str, final_anceps: bool) -> tuple[bool, int]:
    """(matches, number of charged `?` slots)."""
    if len(lg) != len(pattern):
        return False, 0
    charged = 0
    last = len(pattern) - 1
    for i, (w, want) in enumerate(zip(lg, pattern)):
        if i == last and final_anceps:
            continue
        if w == "?":
            charged += 1
        elif w != want:
            return False, 0
    return True, charged


def pada_lengths(metre: CompiledMetre, by_id: Mapping[str, CompiledMetre], k: int) -> tuple[int, ...]:
    """Slot count of each of the k pādas (ardhasama alternates two lengths)."""
    odd_pats, even_pats = metre.pada_patterns(by_id)
    return tuple(len(odd_pats[0]) if p % 2 == 0 else len(even_pats[0]) for p in range(k))


def length_options(metre: CompiledMetre, by_id: Mapping[str, CompiledMetre], k: int) -> tuple[tuple[int, ...], ...]:
    """Every pāda-length tuple the metre admits for k pādas. A mixed-length mixture (11/12
    upajāti) admits only tuples using at least two lengths; uniform ones belong to the
    single-length mixtures and sama metres."""
    if not metre.mixed_lengths:
        return (pada_lengths(metre, by_id, k),)
    sizes = sorted({len(by_id[c].pattern) for c in metre.components})
    return tuple(t for t in product(sizes, repeat=k) if len(set(t)) > 1)


def gate(lg: str, metre: CompiledMetre, by_id: Mapping[str, CompiledMetre], cost_uncertain: float,
         budget: float, k: int = 4, lengths: tuple[int, ...] | None = None) -> GateResult:
    """Exact verdict for a window of k pādas (k = 2 or 4) with the given pāda lengths
    (default: the metre's only length tuple)."""
    lengths = lengths or length_options(metre, by_id, k)[0]
    if k not in (2, 4) or len(lengths) != k or len(lg) != sum(lengths):
        return GateResult(False, 0.0, (), (), "length")
    odd_pats, even_pats = metre.pada_patterns(by_id)
    names = tuple(metre.components) if metre.cls == "mixture" else (metre.id,)
    found, charged, pos, finals = [], 0, 0, set()
    for p, n in enumerate(lengths):
        seg = lg[pos:pos + n]
        pos += n
        finals.add(pos - 1)
        pats = odd_pats if p % 2 == 0 else even_pats
        for name, pat in zip(names if metre.cls == "mixture" else (metre.id,) * len(pats), pats):
            if len(pat) != n:
                continue
            ok, c = match_pada(seg, pat, metre.final_anceps)
            if ok:
                found.append(name)
                charged += c
                break
        else:
            return GateResult(False, 0.0, (), (), f"pada{p + 1}")
    cost = charged * cost_uncertain
    uncertain = tuple(i for i, w in enumerate(lg) if w == "?" and not (metre.final_anceps and i in finals))
    if cost > budget + 1e-12:
        return GateResult(False, cost, (), uncertain, "budget")
    return GateResult(True, cost, tuple(found), uncertain, "ok")


def log_language_size(metre: CompiledMetre, by_id: Mapping[str, CompiledMetre], k: int,
                      lengths: tuple[int, ...] | None = None) -> float:
    """log of the number of strings of the given pāda lengths the metre admits
    (per pāda: components of that length × anceps)."""
    odd_pats, even_pats = metre.pada_patterns(by_id)
    lengths = lengths or length_options(metre, by_id, k)[0]
    anceps = 2.0 if metre.final_anceps else 1.0
    return sum(log(len({p for p in (odd_pats if i % 2 == 0 else even_pats) if len(p) == n}) * anceps)
               for i, n in enumerate(lengths))


def prefilter_reject(lg: str, patterns: Sequence[str], final_anceps: bool) -> bool:
    """SRCH-1: a cheap necessary condition — the first pāda must match some pattern."""
    return not any(match_pada(lg[:len(pat)], pat, final_anceps)[0] for pat in patterns)
