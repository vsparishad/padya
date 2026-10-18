"""Scanner rules SC-0…SC-9, SV-7, INV-5, M1 offset validity.

Expected L/G strings are agent-scanned by hand, not independently adjudicated
(TEST6-3); they check rule implementation, not philological gold.
"""
from __future__ import annotations

import pytest

from padya.loader import CleanerRecord, document_from_text
from padya.scanner import contextual_final_weight, scan


def weights(text: str) -> str:
    return "".join(a.weight for a in scan(document_from_text(text)).aksharas)


@pytest.mark.parametrize("text,lg", [
    ("अयं निजः परो वेति", "LGLGLGGL"),                 # SC-0, SC-1, SC-4
    ("गणना लघुचेतसाम्", "LLGLLGLG"),                    # SC-5 pause closure on final म्
    ("कर्मण्येवाधिकारस्ते", "GGGGLGGG"),               # SC-5 clusters
    ("वसुधैव कुटुम्बकम्", "LLGLLGLG"),
])
def test_sc0_sc5_known_padas(text: str, lg: str) -> None:
    assert weights(text) == lg


def test_sc1_anusvara_before_vowel_is_guru() -> None:  # T27
    assert weights("अयं अत्र")[1] == "G"


def test_sc3_candrabindu_short_vowel_is_uncertain_not_zero() -> None:  # T27
    stream = scan(document_from_text("हँस"))
    first = stream.aksharas[0]
    assert first.weight == "?" and first.nasal and first.matra is None
    assert first.possible_parses == ("L", "G")


def test_sc4_visarga_guru() -> None:
    assert weights("निजः परो") == "LGLG"


def test_sc5_cluster_across_space_counts() -> None:
    assert weights("निषाद प्रतिष्ठां")[2] == "G"  # द before प्र


def test_sc8_danda_blocks_lookahead() -> None:
    assert weights("कदाचन । स्त्री")[3] == "L"  # न before । then स्त्र: no closure


def test_sc9_avagraha_silent_and_soft_start() -> None:
    stream = scan(document_from_text("सङ्गोऽस्त्वकर्मणि"))
    assert [a.slp1 for a in stream.aksharas] == ["sa", "Ngo", "stva", "ka", "rma", "Ri"]
    assert stream.aksharas[2].soft_start and not stream.aksharas[2].word_start


def test_sv7_word_starts_and_hyphen_soft_start() -> None:
    aks = scan(document_from_text("राम-लक्ष्मणौ गच्छतः")).aksharas
    assert aks[0].word_start and aks[2].soft_start and not aks[2].word_start
    assert aks[5].word_start


def test_sv8_phonological_flag_makes_weight_uncertain() -> None:
    doc = document_from_text("कर्म", records=[CleanerRecord("flag", 0, 2, {"cls": "orphan_matra"})])
    assert scan(doc).aksharas[0].weight == "?"


def test_contextual_final_weight_closed_by_own_coda() -> None:
    aks = scan(document_from_text("कुटुम्बकम् इति")).aksharas
    assert aks[3].weight == "L" and contextual_final_weight(aks[3]) == "G"


def test_m1_offset_projection_validity_and_inv5() -> None:
    text = "तथा च मनुः अयं निजः परो वेति ॥१॥ सङ्गोऽस्त्व क़ुरान॒ 𑀅 ॐ"
    stream = scan(document_from_text(text))
    prev_end = 0
    for a in stream.aksharas:
        assert prev_end <= a.src.start < a.src.end <= len(text)  # ordered, non-overlapping
        assert text[a.src.start:a.src.end]  # projected slice is non-empty
        prev_end = a.src.end
    # every vowel nucleus belongs to exactly one akṣara (INV-5)
    nuclei = [i for i in stream.items if i.kind == "V"]
    assert len(nuclei) == len(stream.aksharas)


def test_off1_analysis_edges_are_monotone() -> None:
    stream = scan(document_from_text("कर्मण्येवाधिकारस्ते मा"))
    srcs = [e.src.start for e in stream.analysis.edges]
    ans = [e.analysis.start for e in stream.analysis.edges if e.analysis]
    assert srcs == sorted(srcs) and ans == sorted(ans)
    assert stream.analysis.slp1 == "karmaRyevADikAraste mA"


def test_foreign_script_splits_runs() -> None:
    stream = scan(document_from_text("अयं निजः abc परो वेति"))
    assert len(stream.runs) == 2


def test_sc7_nonstandard_vowel_sign_is_uncertain_not_a_barrier() -> None:
    """ॊ (short o) is a typing variant in editions: weight '?', never a run barrier (DET-5)."""
    text = "विक्रमॊ वृषः"
    stream = scan(document_from_text(text))
    assert len(stream.runs) == 1 and stream.aksharas[2].weight == "?"
    assert "nonstandard_vowel" in stream.aksharas[2].flags
    assert stream.aksharas[2].matra is None


def test_double_danda_survives_a_vowelless_reference_fragment() -> None:
    from padya.loader import document_from_text
    from padya.scanner import scan
    aks = scan(document_from_text("तदपत्यतया भृगोः ॥ [म् ३․१६]\nशूद्रां शयनमारोप्य")).aksharas
    shu = next(a for a in aks if a.slp1 == "SU")
    goh = next(a for a in aks if a.slp1 == "goH")
    assert shu.delim_before == "D2" and shu.line_start and goh.delim_after == "D2"
