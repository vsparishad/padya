"""Pathyā gate AN-1/AN-2/AN-5, §25.1 counterexamples, SRCH-1/2, TEST6-6, T33."""
from __future__ import annotations

import random

import pytest

from padya.config import load_config
from padya.errors import ConfigError
from padya.metres import anustubh
from padya.metres.anustubh import Profile, gate, slow_gate
from padya.metres.bitmask import mismatch_lower_bound, pathya_masks

VASUDHAIVA = "LGLGLGGL" "LLGLLGLG" "LGLLLGGL" "LLGLLGLG"


@pytest.fixture(scope="module")
def profile() -> Profile:
    cfg = load_config()
    return Profile.from_config(cfg.profile, cfg.weights)


def test_an1_an2_pathya_full_verse_accepted(profile) -> None:
    r = gate(VASUDHAIVA, profile, 0.0)
    assert r.ok and r.cost == 0.0


@pytest.mark.parametrize("opening", ["LLL", "LLG"])
def test_an2_odd_forbidden_openings_rejected(profile, opening) -> None:  # T31
    lg = "L" + opening + VASUDHAIVA[4:]
    assert not gate(lg, profile, 0.0).ok


def test_an1_even_ra_opening_forbidden_under_classical_strict(profile) -> None:
    lg = VASUDHAIVA[:8] + "L" + "GLG" + VASUDHAIVA[12:]
    assert not gate(lg, profile, 0.0).ok


def test_an5_one_bad_pada_fails_whole_verse(profile) -> None:
    lg = VASUDHAIVA[:24] + "LLGLLGGG"  # even pāda with odd cadence
    assert not gate(lg, profile, 0.0).ok


def test_vipula_cadence_not_accepted_as_pathya(profile) -> None:  # §25.1, T32
    na_vipula = "GGLGLLLG" + VASUDHAIVA[8:]
    bha_vipula_shape = "LGLGGLLG" + VASUDHAIVA[8:]  # 2–4 GLG, 5–7 GLL
    assert not gate(na_vipula, profile, 0.0).ok
    assert not gate(bha_vipula_shape, profile, 0.0).ok


def test_unimplemented_variants_fail_closed() -> None:  # AN-3, M2
    with pytest.raises(ConfigError):
        anustubh.check_variants(["pathya", "ta_vipula"])
    with pytest.raises(ConfigError):
        anustubh.check_variants(["pathya", "hypermetric9"])
    with pytest.raises(ConfigError):
        anustubh.check_variants(["na_vipula"])  # pathyā is never optional


def test_t33_uncertain_slot_is_charged_even_with_zero_mask_mismatch(profile) -> None:
    lg = VASUDHAIVA[:5] + "?" + VASUDHAIVA[6:]  # slot 6 of pāda 1 unknown
    assert mismatch_lower_bound(lg, pathya_masks()) == 0  # prefilter cannot reject …
    assert not gate(lg, profile, 0.0).ok  # … but tier T budget 0 cannot absorb the cost
    r = gate(lg, profile, 1.0)
    assert r.ok and r.cost == pytest.approx(0.5) and r.uncertain_slots == (5,)


def test_uncertain_anceps_slot_is_free(profile) -> None:
    lg = "?" + VASUDHAIVA[1:7] + "?" + VASUDHAIVA[8:]
    assert gate(lg, profile, 0.0).ok


def test_srch1_prefilter_reject_implies_gate_reject(profile) -> None:
    rng = random.Random(7)
    masks = pathya_masks()
    for _ in range(3000):
        lg = "".join(rng.choice("LG?") for _ in range(32))
        if mismatch_lower_bound(lg, masks) > 0:
            assert not gate(lg, profile, 10.0).ok


def test_test6_6_fast_gate_matches_exhaustive_oracle(profile) -> None:
    rng = random.Random(11)
    for i in range(4000):
        base = VASUDHAIVA if i % 2 else "".join(rng.choice("LG") for _ in range(32))
        lg = "".join(rng.choice("LG?") if rng.random() < 0.15 else c for c in base)
        if lg.count("?") > 8:
            continue
        for budget in (0.0, 0.5, 1.0, 2.0):
            fast = gate(lg, profile, budget)
            ok, cost = slow_gate(lg, profile, budget)
            assert fast.ok == ok, (lg, budget)
            if ok:
                assert fast.cost == pytest.approx(cost)


def test_language_size_matches_closed_form(profile) -> None:
    # odd pāda: 2 × 6 × 2 = 24; even pāda (classical_strict): 2 × 5 × 2 = 20
    assert anustubh.language_size(profile) == (24 * 20) ** 2
