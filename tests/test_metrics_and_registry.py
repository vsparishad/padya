"""Evaluation matcher (T36, T37, EVAL6-5), registry compiler (T25, §25), candidate dedupe (T38)."""
from __future__ import annotations

import copy
import itertools
import random

import pytest

from padya.config import load_config, thaw
from padya.errors import RegistryError
from padya.metres.registry import active_metres, compile_registry, expand
from tools.metrics import match_spans, poisson_upper_per_1000


def test_t37_two_predictions_one_gold_credit_one_tp() -> None:
    r = match_spans([(0, 10), (2, 11)], [(0, 10)], "iou", 0.5)
    assert (r.tp, r.fp, r.fn) == (1, 1, 0) and r.pairs == ((0, 0),)
    assert r.fp_zero_overlap == 0 and r.fp_all_unmatched == 1  # EVAL6-6


def test_t37_exact_matching_ignores_overextension() -> None:
    r = match_spans([(0, 12)], [(0, 10)], "exact")
    assert (r.tp, r.fp, r.fn) == (0, 1, 1)


def test_eval6_5_matching_is_maximum_weight_not_greedy() -> None:
    rng = random.Random(3)
    for _ in range(200):
        pred = [(s, s + rng.randint(1, 6)) for s in sorted(rng.sample(range(40), 5))]
        gold = [(s, s + rng.randint(1, 6)) for s in sorted(rng.sample(range(40), 5))]
        r = match_spans(pred, gold, "iou", 0.1)
        assert len({p for p, _ in r.pairs}) == len(r.pairs) == len({g for _, g in r.pairs})  # TEST6-13
        best = _brute_force_weight(pred, gold)
        got = sum(_iou(pred[p], gold[g]) for p, g in r.pairs)
        assert got == pytest.approx(best)


def _iou(a, b) -> float:
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    value = inter / union if union else 0.0
    return value if value >= 0.1 else 0.0


def _brute_force_weight(pred, gold) -> float:
    best = 0.0
    for perm in itertools.permutations(range(len(gold))):
        best = max(best, sum(_iou(pred[i], gold[j]) for i, j in enumerate(perm)))
    return best


def test_t36_zero_fp_reports_positive_upper_bound() -> None:
    assert poisson_upper_per_1000(0, 30_000) == pytest.approx(0.0998, abs=1e-3)  # §44.2 example
    assert poisson_upper_per_1000(0, 500) > 5.0
    assert poisson_upper_per_1000(3, 30_000) > poisson_upper_per_1000(0, 30_000)


def test_registry_compiles_and_nothing_is_verified() -> None:
    compiled = compile_registry(load_config().metres)
    assert len(compiled) == 35 and all(c.status != "verified" for c in compiled)
    assert expand(["na", "sa", "ma", "ra", "sa", "la", "ga"]) == "LLLLLGGGGGLGLLGLG"  # Hariṇī


def test_t25_injected_harini_mismatch_fails_closed_with_diagnosis() -> None:
    registry = thaw(load_config().metres)
    bad = copy.deepcopy(registry)
    harini = next(m for m in bad["metres"] if m["id"] == "harini")
    harini["pattern"] = "LLLLLGGGGGLLGLLGG"  # mis-expanded string of the kind v3 carried
    with pytest.raises(RegistryError, match=r"entry #\d+ harini: expand"):
        compile_registry(bad)


def test_registry_rejects_alias_collision_and_bad_length() -> None:
    registry = thaw(load_config().metres)
    bad = copy.deepcopy(registry)
    bad["metres"][1]["aliases"] = ["simhonnata"]  # already an alias of vasantatilaka
    bad["metres"][2]["syllables_per_pada"] = 99
    with pytest.raises(RegistryError) as exc:
        compile_registry(bad)
    assert "alias collision" in str(exc.value) and "syllables_per_pada=99" in str(exc.value)


def test_unverified_metres_cannot_become_active_silently() -> None:  # §5.3, §47.2(4)
    compiled = compile_registry(load_config().metres)
    with pytest.raises(RegistryError):
        active_metres(compiled, ["mandakranta"], allow_unverified=False)
    assert active_metres(compiled, ["anustubh"], allow_unverified=True) == ("anustubh",)


def test_t38_duplicate_windows_collapse_to_one_canonical_candidate() -> None:
    from padya.candidates import candidate_id, generate
    from padya.loader import document_from_text
    from padya.scanner import scan

    text = "अयं निजः परो वेति गणना लघुचेतसाम् उदारचरितानां तु वसुधैव कुटुम्बकम्"
    doc = document_from_text(text)
    gen = generate(scan(doc), doc.text_sha256, load_config(), None)
    ids = [c.cand_id for c in gen.candidates]
    assert len(ids) == len(set(ids)) == 1
    assert ids[0] == candidate_id(doc.text_sha256, 0, 32, "anustubh", ("pathya", "pathya"), "default")
