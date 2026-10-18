"""Fixed-pattern metres from the registry (§5.3, SC-6): sama, upajāti mixtures, ardhasama."""
from __future__ import annotations

from padya.config import load_config
from padya.loader import document_from_text
from padya.metres import sama
from padya.metres.registry import compile_registry
from padya.pipeline import detect

VASANTA = "हेमाद्रिमाधवमते प्रविचार्य सम्यगालोच्य तत्त्वमथ तीर्थकृतां परेषाम् । श्रीरामकृष्णतनयः कमलाकराख्यः काले यथामति विनिर्णयमातनोति ॥ ७ ॥"
UPENDRA = "गृहप्रवेशत्रिदशप्रतिष्ठाविवाहचौलव्रतबन्धपूर्वम् । सौम्यायने कर्म शुभं विधेयं यद्दर्हितं तत्तु तदन्यकाले ॥"
BHUJANGA = "असङ्क्रान्तिमासोऽधिमासः स्फुटं स्यात् द्विसङ्क्रान्तिमासः क्षयाख्यः कदाचित् । क्षयः कार्तिकादित्रये नान्यतः स्यात् तदा वर्षमध्येऽधिमासद्वयं स्यात् ॥"


def registry():
    c = load_config(baseline_mode="BASE-C")
    comp = compile_registry(c.metres)
    return c, {m.id: m for m in comp}


def run(text: str, mode: str = "BASE-C"):
    return detect(document_from_text(text, doc_id="t", tier="T"), load_config(baseline_mode=mode, tier="T"))


def test_match_pada_final_anceps_and_uncertain() -> None:
    assert sama.match_pada("GGLGGLLGLGL", "GGLGGLLGLGG", True) == (True, 0)
    assert sama.match_pada("GGLGGLLGLGL", "GGLGGLLGLGG", False) == (False, 0)
    assert sama.match_pada("GG?GGLLGLGG", "GGLGGLLGLGG", True) == (True, 1)
    assert sama.match_pada("LGLGGLLGLGG", "GGLGGLLGLGG", True) == (False, 0)


def test_upajati_mixture_reports_component_per_pada() -> None:
    _, by_id = registry()
    lg = by_id["indravajra"].pattern + by_id["upendravajra"].pattern * 3
    r = sama.gate(lg, by_id["upajati"], by_id, 0.5, 0.0)
    assert r.ok and r.variants == ("indravajra", "upendravajra", "upendravajra", "upendravajra")
    assert sama.gate(lg[:-1] + "X", by_id["upajati"], by_id, 0.5, 0.0).ok  # pāda-final anceps
    assert not sama.gate("GL" + lg[2:], by_id["upajati"], by_id, 0.5, 0.0).ok  # slot 2 wrong → fails


def test_ardhasama_alternates_patterns() -> None:
    _, by_id = registry()
    m = by_id["viyogini"]
    lg = (m.odd_pattern + m.even_pattern) * 2
    assert sama.gate(lg, m, by_id, 0.5, 0.0).ok
    assert not sama.gate(m.odd_pattern * 4, m, by_id, 0.5, 0.0).ok


def test_base_a_ignores_fixed_metres() -> None:
    assert run(VASANTA, "BASE-A").verses == ()


def test_vasantatilaka_detected_as_one_stanza() -> None:
    (v,) = run(VASANTA).verses
    assert v["metre_id"] == "vasantatilaka" and v["partial"] == "full" and len(v["padas"]) == 4
    assert v["text"].endswith("विनिर्णयमातनोति")


def test_mixed_stanza_is_upajati_with_components_per_pada() -> None:
    (v,) = run(UPENDRA).verses
    assert v["metre_id"] == "upajati" and v["variant"] == ["upendravajra", "upendravajra", "indravajra", "indravajra"]


def test_pure_indravajra_stanza_prefers_the_specific_metre() -> None:
    pure = "कृतेऽपि नानापुरुषैः प्रबन्धे\u0020स्वयं" if False else None
    _, by_id = registry()
    c = load_config(baseline_mode="BASE-C")
    lg = by_id["indravajra"].pattern * 4
    from padya.metres.anustubh import Profile
    from padya.candidates import Candidate
    from padya.scorer import score
    prof = Profile.from_config(c.profile, c.weights)
    g_pure = sama.gate(lg, by_id["indravajra"], by_id, 0.5, 0.0)
    g_mix = sama.gate(lg, by_id["upajati"], by_id, 0.5, 0.0)
    pure = Candidate("a", 0, 44, "indravajra", g_pure.variants, 4, "free", "B1", lg, g_pure, (), "none", (11,) * 4)
    mix = Candidate("b", 0, 44, "upajati", g_mix.variants, 4, "free", "B1", lg, g_mix, (), "none", (11,) * 4)
    assert score(pure, c, prof, by_id).score > score(mix, c, prof, by_id).score


def test_bhujangaprayata_detected() -> None:
    (v,) = run(BHUJANGA).verses
    assert v["metre_id"] == "bhujangaprayata"


def test_fixed_metre_half_needs_anchor() -> None:
    half = "हेमाद्रिमाधवमते प्रविचार्य सम्यगालोच्य तत्त्वमथ तीर्थकृतां परेषाम् ।"
    (v,) = run(half).verses
    assert v["partial"] == "half" and v["metre_id"] == "vasantatilaka"
    assert run(half.rstrip(" ।") + " तथा").verses == ()


def test_full_only_metres_emit_no_halves_and_no_typo_verses() -> None:
    # Arrange: an upajāti half (strict_vrttas: chance halves of 11-syllable metres too likely)
    half = "नक्षत्रसत्राण्ययनानि चेन्दोर्मासेन कुर्याद्भगणात्मकेन ।"
    damaged = "गृहप्रवेशत्रिदशप्रतिष्ठाविवाहचौलव्रतबन्धपूर्वम् । सौम्यायने कर्म शुभं विधेयं यद्गर्हितं तत्तु तदन्यकालेषु ॥"

    # Act
    det_half, det_damaged = run(half), run(damaged)

    # Assert: full stanzas still detected; halves and typo halves are not
    assert det_half.verses == () and det_half.suspects == ()
    assert all(s["partial"] == "full" for s in det_damaged.suspects
               if s["metre_id"] in ("upajati", "indravajra", "upendravajra"))
    assert run(UPENDRA).verses[0]["partial"] == "full"


def test_damaged_upajati_stanza_is_a_full_typo_verse() -> None:
    # Arrange: प्राणीवधे (for प्राणिवधे) and भङ्गचित्ता (for सङ्कुचिता): one wrong syllable per half
    text = ("ये क्षान्तदान्ताः श्रुतपूर्णकर्णा जितेन्द्रियाः प्राणीवधे निवृत्ताः ।\n"
            "प्रतिग्रहे भङ्गचित्ताग्रहस्तास्ते ब्राह्मणास्तारयितुं समर्थाः ॥")

    # Act
    det = run(text)

    # Assert
    (s,) = det.suspects
    assert det.verses == () and s["metre_id"] == "upajati" and s["partial"] == "full" and s["edits"] == 2


def test_eight_syllable_vrttas_are_not_active_in_base_c() -> None:
    active = run(VASANTA).report["active_metres"]
    assert "pramanika" not in active and "vidyunmala" not in active and "vasantatilaka" in active


def test_fixed_metre_outscores_anustubh_windows_inside_it() -> None:
    det = run(VASANTA + " " + UPENDRA)
    assert sorted(v["metre_id"] for v in det.verses) == ["upajati", "vasantatilaka"]


MIXED = ("कृत्वा व्रतं वत्सरमेतदिष्टं\nदद्याच्च दीपान् विधिवत् प्रभूतान् ।\n"
         "चान्द्रं पदं प्राप्य विवर्धते सदः\nधनान्वितः स्यात्त्रिदिवे इहैव ॥")


def test_mixed_11_12_upajati_stanza_is_detected() -> None:
    # Arrange / Act: indravajrā-type pādas with one vaṃśastha-type pāda (11-11-12-11)
    (v,) = run(MIXED).verses

    # Assert
    assert v["metre_id"] == "upajati_mixed" and v["partial"] == "full"
    assert v["variant"][2] in ("vamsastha", "indravamsa")


def test_uniform_length_stanza_is_not_called_mixed() -> None:
    (v,) = run(UPENDRA).verses
    assert v["metre_id"] == "upajati"


def test_full_only_half_is_detected_when_padas_are_on_separate_lines() -> None:
    # Arrange
    two_lines = "शान्ते यथाग्नौ घृतमाजुहोति\nतदेव देवान्न पितॄनुपैति ।"
    one_line = two_lines.replace("\n", " ")

    # Act
    (v,) = run(two_lines).verses

    # Assert: layout evidence admits the half; the same words on one line stay out
    assert v["partial"] == "half" and v["metre_id"] in ("upajati", "indravajra", "upendravajra")
    assert run(one_line).verses == ()


def test_mixed_half_on_separate_lines() -> None:
    (v,) = run("इत्यादि चास्त्राणि च पूजयित्वा\nविश्वेश्वरायेति शिरोऽभिपूजनम् ।").verses
    assert v["metre_id"] == "upajati_mixed" and v["partial"] == "half"


def test_mixed_upajati_is_not_active_in_base_a() -> None:
    assert "upajati_mixed" not in run(MIXED, "BASE-A").report["active_metres"]


DAANA = ("दानेन भूता वशीभ्वन्ति दानेन वैरान्यपि यान्ति नाशम् । "
         "परोऽपि बन्धुत्वमुपैति दानात् दानं हि सर्वव्यसनानि हन्ति ।")


def test_single_line_upajati_half_with_damaged_twin_is_detected() -> None:
    # Arrange: half 1 has two OCR errors in pāda 1 (भूता for भूतानि, वशीभ्वन्ति for वशीभवन्ति)

    # Act
    det = run(DAANA)

    # Assert: the clean half is a verse, its damaged twin a typo half
    (v,) = det.verses
    assert v["partial"] == "half" and v["text"].startswith("परोऽपि") and v["metre_id"] == "upajati"
    (s,) = det.suspects
    assert s["partial"] == "half" and s["text"].startswith("दानेन भूता") and s["edits"] == 2


def test_single_line_half_without_a_near_twin_stays_out() -> None:
    prose = "अथ सर्वेषां दानानां प्रशंसा विस्तरेण कथ्यते पुराणेषु । "
    det = run(prose + "परोऽपि बन्धुत्वमुपैति दानात् दानं हि सर्वव्यसनानि हन्ति ।")
    assert det.verses == () and det.suspects == ()
