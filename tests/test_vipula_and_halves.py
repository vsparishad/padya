"""M2.5 vipulā grammar (§5.2 table, §25.1, T24, T32) and anchored halves (AN-6, NEG-3, DET-7)."""
from __future__ import annotations

import random

import pytest

from padya.config import load_config
from padya.loader import document_from_text
from padya.metres import anustubh
from padya.metres.anustubh import VARIANT_ORDER, Profile, gate, pada_language_size, slow_gate
from padya.metres.bitmask import masks_for, mismatch_lower_bound
from padya.pipeline import detect
from padya.scanner import scan

EVEN = "GGGLLGLG"  # a pathyā even pāda
PATHYA_ODD = "LGGGLGGG"
ALL = VARIANT_ORDER


@pytest.fixture
def strict() -> Profile:
    c = load_config()
    return Profile.from_config(c.profile, c.weights)


@pytest.fixture
def lenient() -> Profile:
    c = load_config(profile="classical_lenient")
    return Profile.from_config(c.profile, c.weights)


def verse(odd1: str, odd3: str = PATHYA_ODD) -> str:
    return odd1 + EVEN + odd3 + EVEN


def ends(*visible: int) -> list[bool]:
    return [i in visible for i in range(32)]


# --- positives: one per variant (shapes taken from the owner's tagged Nirṇayasindhu sample) ---

def test_na_vipula_accepted_without_caesura(strict) -> None:
    r = gate(verse("GGLGLLLG"), strict, 0.0, ALL)  # 2–4 GLG, 5–7 LLL, syl 4 G
    assert r.ok and r.variants[0] == "na_vipula" and not r.caesura_unverified


def test_bha_vipula_canonical_glg_is_not_rejected(strict) -> None:  # §25.1 v3 counterexample
    r = gate(verse(PATHYA_ODD, "LGLGGLLG"), strict, 0.0, ALL)
    assert r.ok and r.variants[2] == "bha_vipula"


def test_ma_vipula_needs_caesura_after_5_under_strict(strict, lenient) -> None:
    lg = verse("LGLGGGGG")  # धनुःप्रवेशे वस्त्राणां
    assert not gate(lg, strict, 0.0, ALL, ends()).ok
    assert gate(lg, strict, 0.0, ALL, ends(4)).variants[0] == "ma_vipula"
    r = gate(lg, lenient, 0.0, ALL, ends())
    assert r.ok and r.variants[0] == "ma_vipula" and r.caesura_unverified == (0,)


def test_ra_vipula_needs_caesura_after_4_under_strict(strict) -> None:
    lg = verse("LLGGGLGG")  # ससुवर्ण छत्रदानं (ṇa heavy before छ, SC-13)
    assert not gate(lg, strict, 0.0, ALL, ends()).ok
    assert gate(lg, strict, 0.0, ALL, ends(3)).variants[0] == "ra_vipula"


# --- near negatives (T24): right cadence, forbidden opening or wrong fourth syllable ---

@pytest.mark.parametrize("odd", [
    "LLLGGLGG",  # ra cadence but 2–4 LL* (forbidden)
    "LLLGLLLG",  # na cadence but 2–4 LLG (not in {GGG, LGG, GLG})
    "LGGLGGGG",  # ma cadence but syllable 4 light
    "LGGGGLLG",  # bha cadence with 2–4 GGG and no caesura after 4 (ma-bha needs it)
    "LGGGGGLG",  # ta-vipulā shape: off
])
def test_near_negatives_fail(strict, odd) -> None:
    assert not gate(verse(odd), strict, 0.0, ALL, ends()).ok


def test_t32_no_silent_pathya_fallback(strict) -> None:
    lg = verse("GGLGLLLG")
    assert not gate(lg, strict, 0.0).ok                       # pathyā-only: rejected
    assert gate(lg, strict, 0.0, ALL).variants[0] != "pathya"  # with variants: labelled na, not pathyā


def test_fast_gate_matches_oracle_with_variants(strict, lenient) -> None:  # TEST6-6
    rng = random.Random(21)
    for _ in range(3000):
        n = rng.choice((16, 32))
        lg = "".join(rng.choice("LLGG?") for _ in range(n))
        we = [rng.random() < 0.3 for _ in range(n)]
        budget = rng.choice((0.0, 1.0, 2.5))
        for prof in (strict, lenient):
            fast = gate(lg, prof, budget, ALL, we)
            slow_ok, slow_cost = slow_gate(lg, prof, budget, ALL, we)
            assert fast.ok == slow_ok, (lg, we, prof.caesura)
            if fast.ok:
                assert fast.cost == pytest.approx(slow_cost)


def test_prefilter_with_variants_never_rejects_a_gate_pass(strict) -> None:  # SRCH-1
    rng = random.Random(5)
    masks = masks_for(ALL)
    for _ in range(3000):
        lg = "".join(rng.choice("LG?") for _ in range(32))
        if mismatch_lower_bound(lg, masks) > 0:
            assert not gate(lg, strict, 10.0, ALL, [True] * 32).ok


def test_language_sizes_are_exact_counts(strict) -> None:
    assert pada_language_size("pathya", strict) == 24
    assert pada_language_size("even", strict) == 20
    assert anustubh.language_size(strict) == (24 * 20) ** 2
    assert anustubh.language_size(strict, ALL) == ((24 + 12 + 8 + 4 + 12) * 20) ** 2


# --- SC-13 che ca ---

def test_sc13_short_vowel_before_cha_is_heavy() -> None:
    w = "".join(a.weight for a in scan(document_from_text("ससुवर्ण छत्रदानं")).aksharas)
    assert w == "LLGGGLGG"


# --- end to end: BASE-C on tagged sample verses; BASE-A unchanged ---

RA_VERSE = "राशिद्वयं यत्र मासे सङ्क्रमेत दिवाकरः । नाधिमासो भवेदेष मलमासस्तु केवलः ॥"
HALF = "ज्यायांसं भ्रातरं भट्टदिवाकरमुपास्महे ॥ ६ ॥"


def run(text: str, mode: str, profile: str = "classical_strict"):
    return detect(document_from_text(text, doc_id="t", tier="T"), load_config(baseline_mode=mode, profile=profile, tier="T"))


def test_base_a_stays_pathya_only_full_verses() -> None:
    assert run(RA_VERSE, "BASE-A").verses == ()
    assert run(HALF, "BASE-A").verses == ()


def test_base_c_detects_ra_vipula_verse() -> None:
    (v,) = run(RA_VERSE, "BASE-C").verses
    assert v["variant"] == ["ra_vipula", "pathya", "pathya", "pathya"] and v["partial"] == "full"
    assert v["text"].startswith("राशिद्वयं") and v["text"].endswith("केवलः")


def test_base_c_detects_anchored_half_only() -> None:
    (v,) = run(HALF, "BASE-C").verses
    assert v["partial"] == "half" and v["partial_anchor"] == "verse_number" and len(v["padas"]) == 2
    assert v["text"] == "ज्यायांसं भ्रातरं भट्टदिवाकरमुपास्महे"
    (q,) = run("तथा च व्यासः — ‘षष्ट्या तु दिवसैर्मासः कथितो बादरायणैः’ इति ॥", "BASE-C").verses
    assert q["partial"] == "half" and q["partial_anchor"] == "quote_close"
    (i,) = run("ज्यायांसं भ्रातरं भट्टदिवाकरमुपास्महे इति", "BASE-C").verses
    assert i["partial_anchor"] == "iti_closer"
    assert run("ज्यायांसं भ्रातरं भट्टदिवाकरमुपास्महे तथा", "BASE-C").verses == ()  # BASE-8: no anchor


def test_full_verse_beats_its_two_halves() -> None:
    text = "सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः । सर्वे भद्राणि पश्यन्तु मा कश्चिद्दुःखभाग्भवेत् ॥"
    det = run(text, "BASE-C", "classical_lenient")
    assert [v["partial"] for v in det.verses] == ["full"]
