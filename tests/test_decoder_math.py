"""Decoder proof obligations against an exhaustive path enumerator (DP-8, DP-9, DEC-20, TEST6-7)."""
from __future__ import annotations

import math
import random

import pytest

from padya.decoder import Arc, decode


def _paths(n: int, arcs: list[Arc]):
    """Every path from 0 to n: prose steps or arcs. Yields (score, arcs used, prose slots)."""
    def rec(pos: int, score: float, used: tuple, prose: tuple):
        if pos == n:
            yield score, used, prose
            return
        yield from rec(pos + 1, score, used, prose + (pos,))
        for a in arcs:
            if a.s == pos:
                yield from rec(a.e, score + a.w, used + (a.arc_id,), prose)
    yield from rec(0, 0.0, (), ())


def _random_case(rng: random.Random) -> tuple[int, list[Arc]]:
    n = rng.randint(1, 12)
    arcs, seen = [], set()
    for k in range(rng.randint(0, 20)):
        s = rng.randrange(0, n)
        e = rng.randint(s + 1, n)
        if (s, e) in seen:
            continue
        seen.add((s, e))
        arcs.append(Arc(f"a{k}", s, e, round(rng.uniform(-4, 6), 3)))
    return n, arcs


@pytest.mark.parametrize("seed", range(300))
def test_dec20_viterbi_logz_marginals_match_enumerator(seed: int) -> None:
    rng = random.Random(seed)
    n, arcs = _random_case(rng)
    paths = list(_paths(n, arcs))
    result = decode(n, arcs)
    best = max(p[0] for p in paths)
    assert result.best_score == pytest.approx(best, abs=1e-9)
    chosen = sum(a.w for a in arcs if a.arc_id in result.accepted)
    assert chosen == pytest.approx(best, abs=1e-9)
    log_z = math.log(sum(math.exp(p[0]) for p in paths))
    assert result.log_z == pytest.approx(log_z, abs=1e-9)
    for a in arcs:
        mass = sum(math.exp(p[0]) for p in paths if a.arc_id in p[1])
        assert result.arc_posterior[a.arc_id] == pytest.approx(mass / math.exp(log_z), abs=1e-9)
    for i in range(n):  # DEC-15: P(prose_i) + P(verse_i) = 1 in the single-arc lattice
        mass = sum(math.exp(p[0]) for p in paths if i in p[2])
        assert result.p_prose[i] == pytest.approx(mass / math.exp(log_z), abs=1e-9)
        assert 0.0 <= result.p_prose[i] <= 1.0 + 1e-12


@pytest.mark.parametrize("seed", range(200))
def test_margin_equals_best_minus_best_path_without_arc(seed: int) -> None:
    rng = random.Random(1000 + seed)
    n, arcs = _random_case(rng)
    paths = list(_paths(n, arcs))
    result = decode(n, arcs)
    for aid in result.accepted:
        without = max(p[0] for p in paths if aid not in p[1])
        assert result.margins[aid] == pytest.approx(result.best_score - without, abs=1e-9)


def test_ties_prefer_fewer_verses_then_earlier_start() -> None:
    arcs = [Arc("late", 2, 4, 0.0), Arc("early", 0, 2, 0.0)]
    assert decode(4, arcs).accepted == ()  # zero-gain arcs lose to prose
    arcs = [Arc("b", 1, 3, 1.0), Arc("a", 0, 2, 1.0)]
    assert decode(3, arcs).accepted == ("a",)


def test_dec11_rejects_invalid_arcs() -> None:
    with pytest.raises(ValueError):
        decode(3, [Arc("x", 2, 2, 1.0)])
