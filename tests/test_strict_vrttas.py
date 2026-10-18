"""tools/strict_vrttas.py: pattern parsing, chance-match model, anuṣṭubh overlap and tiers."""
from tools.strict_vrttas import Metre, _metre, anustubh_compatible, pattern_prob, tier

UNIFORM = {"L": 0.5, "G": 0.5, **{f"{a}>{b}": 0.5 for a in "LG" for b in "LG"},
           **{f"{c}>{b}": 0.5 for c in ("LL", "LG", "GL", "GG") for b in "LG"}}


def _row(**kw):
    base = {"support": ["VR", "Mishra"], "anustubh_compatible": False, "expected_full": 0.0,
            "expected_half": 0.0, "expected_half_typo": 0.0}
    return {**base, **kw}


def test_sama_pattern_is_repeated_and_final_syllable_is_anceps():
    m = _metre(["G G L – G G L L G L G G"])  # indravajrā with spacing and a yati dash
    assert m.padas == ("GGLGGLLGLGX",) * 4 and m.kind == "sama"


def test_ardhasama_alternates_odd_and_even_padas():
    m = _metre(["LLGLLGLGLG", "LLGGLLGLGLG"])
    assert m.kind == "ardhasama" and m.half == "LLGLLGLGLX" + "LLGGLLGLGLX"


def test_short_patterns_are_ignored():
    assert _metre(["GGGGG"]) is None


def test_anceps_slot_doubles_the_chance_probability():
    assert pattern_prob("GGGX", UNIFORM) == 2 * pattern_prob("GGGG", UNIFORM) == 0.125


def test_eight_syllable_metres_inside_anustubh_space_are_flagged():
    assert anustubh_compatible(Metre(("LGLGLGLX",) * 4))      # pramāṇikā: a valid even pāda
    assert not anustubh_compatible(Metre(("GGLGGLLGLGX",) * 4))


def test_tiers_follow_sources_length_and_expected_matches():
    assert tier(_row(), 11) == "strict"
    assert tier(_row(expected_half_typo=0.5), 11) == "strict_full_only"
    assert tier(_row(support=["Mishra"]), 11) == "needs_second_source"
    assert tier(_row(), 8) == "risky"
    assert tier(_row(anustubh_compatible=True), 11) == "risky"
