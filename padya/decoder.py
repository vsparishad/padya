"""Stage 8: single-arc semi-Markov decoder (§8.2, DP-2, DP-8, DEC-11…DEC-15, §42.2).

Nodes are akṣara boundaries 0..n inside one eligible run. Every step has a prose
edge of weight 0; verse arcs are optional competitors. Viterbi and log-space
forward–backward run on the same arc set. Paired macro arcs are not enabled.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

EPS = 1e-12


@dataclass(slots=True, frozen=True)
class Arc:
    arc_id: str
    s: int  # local node index
    e: int
    w: float


@dataclass(slots=True, frozen=True)
class RunDecode:
    accepted: tuple[str, ...]
    best_score: float
    log_z: float
    arc_posterior: Mapping[str, float]
    p_prose: tuple[float, ...]  # per slot (akṣara) i: P(prose edge i→i+1)
    margins: Mapping[str, float]


def _lse(a: float, b: float) -> float:
    if a == -math.inf:
        return b
    if b == -math.inf:
        return a
    m = max(a, b)
    return m + math.log(math.exp(a - m) + math.exp(b - m))


def _validate(n: int, arcs: Sequence[Arc]) -> None:
    ids = set()
    for a in arcs:
        if not (0 <= a.s < a.e <= n):  # DEC-11
            raise ValueError(f"arc {a.arc_id} [{a.s},{a.e}) outside [0,{n}]")
        if a.arc_id in ids:
            raise ValueError(f"duplicate arc id {a.arc_id}")
        ids.add(a.arc_id)


def _viterbi(n: int, by_end: list[list[Arc]]) -> tuple[list[float], list[Arc | None]]:
    """Deterministic ties (§8.2): higher score, then fewer verses, then earlier arc start."""
    best = [0.0] * (n + 1)
    verses = [0] * (n + 1)
    back: list[Arc | None] = [None] * (n + 1)
    for e in range(1, n + 1):
        best[e], verses[e], back[e] = best[e - 1], verses[e - 1], None
        for arc in by_end[e]:  # sorted by start ascending
            cand, cv = best[arc.s] + arc.w, verses[arc.s] + 1
            if cand > best[e] + EPS or (abs(cand - best[e]) <= EPS and cv < verses[e]):
                best[e], verses[e], back[e] = cand, cv, arc
    return best, back


def _backward_max(n: int, by_start: list[list[Arc]]) -> list[float]:
    bwd = [0.0] * (n + 1)
    for s in range(n - 1, -1, -1):
        bwd[s] = bwd[s + 1]
        for arc in by_start[s]:
            bwd[s] = max(bwd[s], arc.w + bwd[arc.e])
    return bwd


def _forward_backward(n: int, by_end, by_start) -> tuple[list[float], list[float]]:
    alpha = [0.0] + [-math.inf] * n
    for e in range(1, n + 1):
        acc = alpha[e - 1]
        for arc in by_end[e]:
            acc = _lse(acc, alpha[arc.s] + arc.w)
        alpha[e] = acc
    beta = [-math.inf] * n + [0.0]
    for s in range(n - 1, -1, -1):
        acc = beta[s + 1]
        for arc in by_start[s]:
            acc = _lse(acc, arc.w + beta[arc.e])
        beta[s] = acc
    return alpha, beta


def _margin(arc: Arc, max_len: int, fwd: list[float], bwd: list[float], by_start, n: int) -> float:
    """Viterbi total minus the best total of any path that does not use `arc`.

    A path avoiding `arc` either visits node s and leaves it by another move, or
    jumps over s with an arc (s' < s < e'); such arcs start within max_len of s.
    """
    with_arc = fwd[arc.s] + arc.w + bwd[arc.e]
    alt = fwd[arc.s] + bwd[arc.s + 1] if arc.s < n else -math.inf  # prose edge out of s
    for other in by_start[arc.s]:
        if other.arc_id != arc.arc_id:
            alt = max(alt, fwd[arc.s] + other.w + bwd[other.e])
    for start in range(max(0, arc.s - max_len + 1), arc.s):
        for other in by_start[start]:
            if other.e > arc.s:
                alt = max(alt, fwd[other.s] + other.w + bwd[other.e])
    return with_arc - alt


def decode(n: int, arcs: Sequence[Arc]) -> RunDecode:
    _validate(n, arcs)
    by_end: list[list[Arc]] = [[] for _ in range(n + 1)]
    by_start: list[list[Arc]] = [[] for _ in range(n + 1)]
    for arc in sorted(arcs, key=lambda a: (a.s, a.e, a.arc_id)):
        by_end[arc.e].append(arc)
        by_start[arc.s].append(arc)
    fwd, back = _viterbi(n, by_end)
    accepted, e = [], n
    while e > 0:
        arc = back[e]
        if arc is None:
            e -= 1
        else:
            accepted.append(arc.arc_id)
            e = arc.s
    accepted.reverse()
    alpha, beta = _forward_backward(n, by_end, by_start)
    log_z = alpha[n]
    if abs(alpha[n] - beta[0]) > 1e-9 * max(1.0, abs(log_z)):  # §8.2 identity, relative for long runs
        raise ArithmeticError(f"forward/backward mismatch {alpha[n]} vs {beta[0]}")
    posterior = {a.arc_id: math.exp(alpha[a.s] + a.w + beta[a.e] - log_z) for a in arcs}
    p_prose = tuple(math.exp(alpha[i] + beta[i + 1] - log_z) for i in range(n))  # DP-8: single-arc only
    bwd = _backward_max(n, by_start)
    accepted_set = set(accepted)
    chosen = {a.arc_id: a for a in arcs if a.arc_id in accepted_set}
    max_len = max((a.e - a.s for a in arcs), default=1)
    margins = {aid: _margin(chosen[aid], max_len, fwd, bwd, by_start, n) for aid in accepted}
    return RunDecode(tuple(accepted), fwd[n], log_z, posterior, p_prose, margins)
