"""Editorial brackets (owner's rule, 2026-10-18): a short `( … )` inside a verse is an editor's
correction or gloss, e.g. `यतेस्सायं (यत्र सायं)`, and is not scanned. INV-1: the source text is
untouched; the verse span still contains the brackets. BASE-A keeps scanning them."""
from __future__ import annotations

from padya.config import load_config
from padya.loader import document_from_text
from padya.pipeline import detect
from padya.scanner import scan

OWNER = ("यतेस्सायं (यत्र सायं) गृहस्थत्वं सूरिभिस्तत्वतत्परैः\n"
         "अयोनौ सङ्ग्रहे (हो) वृत्ते परित्यागो गुरुस्त्रियाः ")


def run(text: str, mode: str = "BASE-C"):
    return detect(document_from_text(text, doc_id="t", tier="T"), load_config(baseline_mode=mode, tier="T"))


def syllables(text: str, max_chars: int | None) -> list[str]:
    return [text[a.src.start:a.src.end] for a in scan(document_from_text(text), editorial_max_chars=max_chars).aksharas]


def test_verse_with_bracketed_corrections_is_detected() -> None:
    # Act
    det = run(OWNER)

    # Assert: one full anuṣṭubh whose text is the source span, brackets included (INV-1)
    (v,) = det.verses
    assert v["metre_id"] == "anustubh" and v["partial"] == "full"
    assert v["text"] == OWNER[v["start"]:v["end"]] and "(यत्र सायं)" in v["text"] and "(हो)" in v["text"]


def test_base_a_still_scans_bracket_contents() -> None:
    assert run(OWNER, mode="BASE-A").verses == ()
    assert "त्र" in syllables("यत्र (यत्र) सायं", None)


def test_scanner_skips_short_brackets_only() -> None:
    # Arrange
    short = "यत्र (हो) सायं"
    long_ = "यत्र (" + "क" * 30 + ") सायं"
    with_danda = "यत्र (हो । ह) सायं"

    # Act / Assert
    assert syllables(short, 20) == ["य", "त्र", "सा", "यं"]
    assert len(syllables(long_, 20)) == 4 + 30
    assert "हो" in syllables(with_danda, 20)


def test_skipped_bracket_does_not_close_the_preceding_syllable() -> None:
    # `ग (स्त) त`: the consonants inside the bracket must not make ग heavy
    (g, _t) = scan(document_from_text("ग (स्त) त"), editorial_max_chars=20).aksharas
    assert g.weight == "L"


# --- citation sigla (base-c-v6): `BDhS 1․1․1․6ab` is a separator, not a foreign-script barrier ---

ANU_SPLIT = ("BDhS 2․1․1․3ab कुटुम्बं पीडयित्वापि ब्राह्मणाय महात्मने ।\n"
             "BDhS 2․1․1․3cd दातव्यं भिक्षवेऽन्नं वै आत्मनो भूतिमिच्छता ॥\n")


def test_citation_tokens_are_separators_not_akshara_or_barrier() -> None:
    aks = scan(document_from_text("[MDh 5․125] इति । cf. GDh 17․8-9 तथा"), editorial_max_chars=20, citation_tokens=True)
    assert [a.slp1[:2] for a in aks.aksharas][:2] == ["i", "ti"] and len(aks.runs) == 1


def test_latin_prose_without_a_number_still_splits_runs() -> None:
    aks = scan(document_from_text("इति । Original BSS text input । तथा"), editorial_max_chars=20, citation_tokens=True)
    assert len(aks.runs) == 2


def test_sloka_printed_as_two_numbered_half_sutras_is_one_full_verse() -> None:
    det = run(ANU_SPLIT)
    assert [(v["metre_id"], v["partial"]) for v in det.verses] == [("anustubh", "full")]
    assert det.verses[0]["text"].startswith("कुटुम्बं") and "BDhS" in det.verses[0]["text"]


def test_base_a_treats_latin_sigla_as_barriers_unchanged() -> None:
    assert run(ANU_SPLIT, mode="BASE-A").verses == ()
    assert len(scan(document_from_text(ANU_SPLIT)).runs) == 2
