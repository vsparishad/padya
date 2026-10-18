"""Span evaluation primitives (§11, §45.2, EVAL6-4…6, EVAL6-13, §44.2, T36, T37).

Matching is deterministic one-to-one maximum-weight bipartite assignment (Hungarian
algorithm on the overlap graph), never greedy many-to-one.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Sequence

Interval = tuple[int, int]
Criterion = Literal["exact", "iou"]


@dataclass(frozen=True)
class MatchResult:
    tp: int
    fp: int
    fn: int
    pairs: tuple[tuple[int, int], ...]  # (pred index, gold index)
    fp_zero_overlap: int  # unmatched predictions touching no gold at all (historical FP)
    fp_all_unmatched: int  # every unmatched prediction (EVAL6-6)
    criterion: str


def _overlap(a: Interval, b: Interval) -> int:
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def _weight(p: Interval, g: Interval, criterion: Criterion, iou_min: float) -> float:
    if criterion == "exact":
        return 1.0 if p == g else 0.0
    inter = _overlap(p, g)
    union = (p[1] - p[0]) + (g[1] - g[0]) - inter
    iou = inter / union if union else 0.0
    return iou if iou >= iou_min else 0.0


def _hungarian_max(weights: list[list[float]]) -> list[tuple[int, int]]:
    """Maximum-weight assignment on a rectangular matrix; returns (row, col) pairs."""
    transposed = len(weights) > len(weights[0])
    w = [list(r) for r in zip(*weights)] if transposed else weights
    n, m = len(w), len(w[0])
    big = max(max(r) for r in w)
    cost = [[big - x for x in row] for row in w]
    u, v, p, way = [0.0] * (n + 1), [0.0] * (m + 1), [0] * (m + 1), [0] * (m + 1)
    for i in range(1, n + 1):
        p[0], j0 = i, 0
        minv, used = [math.inf] * (m + 1), [False] * (m + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], math.inf, 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j], way[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    pairs = [(p[j] - 1, j - 1) for j in range(1, m + 1) if p[j]]
    return [(b, a) for a, b in pairs] if transposed else pairs


def match_spans(pred: Sequence[Interval], gold: Sequence[Interval], criterion: Criterion = "exact",
                iou_min: float = 0.5) -> MatchResult:
    edges = {(i, j): _weight(p, g, criterion, iou_min) for i, p in enumerate(pred) for j, g in enumerate(gold)}
    edges = {k: v for k, v in edges.items() if v > 0}
    pairs: list[tuple[int, int]] = []
    if edges:
        rows = sorted({i for i, _ in edges})
        cols = sorted({j for _, j in edges})
        matrix = [[edges.get((i, j), 0.0) for j in cols] for i in rows]
        for r, c in _hungarian_max(matrix):
            if matrix[r][c] > 0:
                pairs.append((rows[r], cols[c]))
    matched_p = {i for i, _ in pairs}
    unmatched = [i for i in range(len(pred)) if i not in matched_p]
    zero = sum(1 for i in unmatched if not any(_overlap(pred[i], g) for g in gold))
    tp = len(pairs)
    return MatchResult(tp, len(pred) - tp, len(gold) - tp, tuple(sorted(pairs)), zero, len(unmatched), criterion)


def poisson_upper_per_1000(events: int, prose_words: int, confidence: float = 0.95) -> float:
    """One-sided exact Poisson upper bound on events per 1,000 words (§44.2, T36).

    For zero events this is 1000·(−ln(1−confidence))/W ≈ 2996/W at 95 %. It assumes a
    Poisson exposure model; clustered works need blocked/bootstrap intervals instead.
    """
    if prose_words <= 0:
        raise ValueError("prose_words must be positive")
    alpha = 1.0 - confidence

    def cdf(lam: float) -> float:
        term = total = math.exp(-lam)
        for k in range(1, events + 1):
            term *= lam / k
            total += term
        return total

    lo, hi = 0.0, max(10.0, 10.0 * (events + 1))
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(mid) > alpha else (lo, mid)
    return 1000.0 * hi / prose_words
