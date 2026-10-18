"""Hypothesis property tests (§14 mandatory properties, §17 OFF, TEST6-8, TEST6-9).

Random Unicode text mixing real pādas, Devanagari noise, punctuation, combining
marks and non-BMP characters: detection never crashes, every accepted span is an
exact source slice (INV-1), verses never overlap (INV-4), both partitions are
complete (INV-6) and every exact offset is grapheme-safe (EDGE-1).
"""
from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from padya.config import load_config
from padya.graphemes import is_grapheme_boundary
from padya.loader import document_from_text
from padya.pipeline import detect
from padya.regions import check_partition

CONFIG = load_config(tier="T")
PADAS = ["अयं निजः परो वेति", "गणना लघुचेतसाम्", "उदारचरितानां तु", "वसुधैव कुटुम्बकम्",
         "कर्मण्येवाधिकारस्ते", "मा फलेषु कदाचन", "तथा च मनुः", "इति", "इत्यादि"]
NOISE = st.text(alphabet="कखगचजतदनपबमयरलवशसहािीुूेैोौंःँ्ऽ।॥ -\n०१‘’—a1𑀅॑‍", max_size=12)
PIECES = st.one_of(st.sampled_from(PADAS), NOISE)


@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(st.lists(PIECES, max_size=14).map(" ".join))
def test_zero_mutation_partitions_and_grapheme_safety(text: str) -> None:
    det = detect(document_from_text(text, doc_id="prop"), CONFIG)
    assert det.doc.text == text  # INV-7: the source is never modified
    covers = []
    for v in det.verses:
        assert v["text"] == text[v["start"]:v["end"]]  # INV-1
        covers.append(tuple(v["observed_cover"]))
        for b in [v["start_boundary"], v["end_boundary"], *v["pada_boundaries"]]:
            if b["resolution"] == "exact_between_codepoints":
                assert is_grapheme_boundary(text, b["offset"])  # EDGE-1
            else:
                assert b["offset"] is None  # EDGE-2
        assert 0.0 <= v["lattice_posterior"] <= 1.0 + 1e-9
        assert v["calibrated_probability"] is None
    covers.sort()
    assert all(a[1] <= b[0] for a, b in zip(covers, covers[1:]))  # INV-4
    check_partition(det.char_regions, len(text))  # INV-6 (characters)
    syl = det.syllable_regions
    assert all(a["syllables"][1] == b["syllables"][0] for a, b in zip(syl, syl[1:]))  # INV-6 (syllables)


@settings(max_examples=100, deadline=None)
@given(st.text(max_size=60))
def test_test6_8_arbitrary_unicode_never_crashes_or_drops_text(text: str) -> None:
    det = detect(document_from_text(text, doc_id="u"), CONFIG)
    check_partition(det.char_regions, len(text))
