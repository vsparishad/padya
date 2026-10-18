"""Review-only OCR near-miss verses (padya/ocr_suspects.py) and their typo tags."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from padya.config import load_config
from padya.loader import document_from_text
from padya.ocr_suspects import _distance
from padya.pipeline import detect
from padya.writer import write_detection
from tools.build_tagger import build

# Owner-reported verses from the Caturvargacintāmaṇi, as printed (OCR typos kept).
SARDULA = ("इति तस्य वंशः ॥\nगोत्रे तस्य बभूव निर्मलगुणश्रेणीभृतामग्रणीर्\nविद्याचारविवेकविकरमनिधिः नीवासुदेवः कृतौ ।\n"
           "यत्कीर्त्या धवलीकृते त्रिभुवने श्रीकण्ठवैकुण्ठयोः\nकैलासाचलदुग्धसिन्धुविषये नशीन्निवासो गृहे ॥ २ ॥\nततो ग्रन्थारम्भः ।\n")
SARDULA_HALF = ("देवेन्द्रलक्ष्मीरपि ॥ १ ॥\nरागः कृष्ण नवस्तबश्रुतिरियं चेतश्चमत्कारिणी\n"
                "मुग्धेबेस्य यथा मया शुभरते वैदग्धामाविष्कृतम् ।\nइति प्रथमम् ।\n")
ANUSTUBH = "अत्र देवलः ।\nनास्तिकस्तेन्हिंस्रेभ्यो जाराय पतिताय च ।\nपिशुनभ्रूणहतृभ्यां प्रदत्तं दुष्फलं भवेत् ॥\nइति ।\n"
PROSE = ("अत्र विशेषो वक्तव्यः । यदा तु सङ्क्रान्तिः रात्रौ भवति तदा पूर्वेद्युः पुण्यकाल इति केचित् । "
         "अन्ये तु परेद्युरिति वदन्ति ॥\n")


def run(text: str, mode: str = "BASE-C"):
    return detect(document_from_text(text, doc_id="t"), load_config(baseline_mode=mode, profile="classical_lenient"))


def marks(s: dict) -> list[tuple[str, int, str]]:
    return [(m["kind"], m["pada"], m["text"]) for m in s["suspect_syllables"]]


def test_distance_ops() -> None:
    assert _distance("GLLL", ("GGLX",))[:2] == (1, "GGLX")  # one wrong weight
    assert _distance("LLLL", ("GLX",))[0] == 1 and _distance("LLLL", ("GLX",))[2] == (("split", 0),)
    assert _distance("GL", ("LLX",))[:3] == (1, "LLX", (("merge", 0),))


def test_sardula_with_split_conjunct_and_wrong_weight() -> None:
    det = run(SARDULA)
    assert det.verses == ()
    (s,) = det.suspects
    assert s["metre_id"] == "sardulavikridita" and s["partial"] == "full" and s["edits"] == 2
    assert marks(s) == [("split", 2, "विक"), ("sub", 4, "न")]
    assert s["text"].startswith("गोत्रे") and s["text"].endswith("गृहे")


def test_sardula_half_with_one_wrong_weight() -> None:
    (s,) = run(SARDULA_HALF).suspects
    assert s["partial"] == "half" and marks(s) == [("sub", 2, "ग्धा")]


def test_anustubh_with_lost_vowel_and_lost_conjunct() -> None:
    (s,) = run(ANUSTUBH).suspects
    assert s["metre_id"] == "anustubh" and s["edits"] == 2
    assert marks(s) == [("merge", 1, "स्ते"), ("sub", 3, "ह")]


def test_prose_yields_no_suspects() -> None:
    assert run(PROSE).suspects == ()


def test_exact_verse_is_a_verse_not_a_suspect() -> None:
    det = run("इति ।\nराशिद्वयं यत्र मासे सङ्क्रमेत दिवाकरः । नाधिमासो भवेदेष मलमासस्तु केवलः ॥\n")
    assert len(det.verses) == 1 and det.suspects == ()


def test_base_a_has_no_suspect_pass() -> None:
    det = run(ANUSTUBH, "BASE-A")
    assert det.suspects == () and "ocr_suspects" in det.report


def test_suspects_file_and_typo_tags_in_page(tmp_path: Path) -> None:
    src = tmp_path / "s.txt"
    src.write_text(ANUSTUBH, encoding="utf-8")
    from padya.loader import load_plain_text
    det = detect(load_plain_text(src), load_config(baseline_mode="BASE-C", profile="classical_lenient"))
    out = write_detection(det, tmp_path / "out")
    rec = json.loads((out / "suspects.jsonl").read_text(encoding="utf-8"))
    assert rec["release_decision"] == "ocr_suspect_review" and ANUSTUBH[rec["start"]:rec["end"]] == rec["text"]
    meta = build(src, tmp_path / "p.html", None, out / "verses.jsonl")
    assert meta["seeded_typos"] == 1 and meta["seeded_verses"] == 0
    assert '"label": "typo"' in (tmp_path / "p.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("budget_key", ["max_edits_full", "max_edits_half", "max_edits_per_pada"])
def test_config_has_budgets(budget_key) -> None:
    assert load_config(baseline_mode="BASE-C").mode["ocr_suspects"][budget_key] >= 1


# Owner-reported cases from the Dānakhaṇḍa (2026-10-17): half-shifted windows across ॥ and
# damaged second halves next to a detected first half.
SHIFTED = ("ब्राह्मणेभ्यो ददौ चापि गयश्चोर्वीं सपत्तनाम् ।\nअवर्षिणि च पर्यन्ये सर्वभूतानि चासकृत् ॥\n"
           "राजा मित्रसहश्रश्च वशिष्ठाय महात्मने ।\nमदयन्तीं प्रियां दत्वा तया सह दिवङ्ग्तः ॥\n")
LABEL_GLUED = ("[२३]सत्यं दमस्तपो दानमहिंसेन्द्रियनिग्रहः ।\nदृश्यन्ते यत्र राजेन्द्र स ब्राह्मण इति स्मृतः ॥\n"
               "वसिष्ठः ।\nयं न सन्तं न चासन्तं नाश्रुतं न बहुश्रुतम् ।\nन सुवृत्तं न दुर्वृत्तं वेद कश्चित् स ब्राह्मणः ॥\n")


def test_no_verse_crosses_double_danda_and_damaged_twin_is_a_typo_half() -> None:
    det = run(SHIFTED)
    assert [v["text"].split()[0] for v in det.verses] == ["ब्राह्मणेभ्यो", "राजा"]
    assert all("॥" not in v["text"] for v in det.verses)
    (s,) = det.suspects
    assert s["partial"] == "half" and s["text"].startswith("मदयन्तीं") and s["suspect_syllables"][0]["kind"] == "missing_in_pada"


def test_prose_label_is_never_glued_into_a_verse() -> None:
    det = run(LABEL_GLUED)
    assert not any("वसिष्ठः" in v["text"] for v in det.verses)
    assert [v["text"][:9] for v in det.verses] == ["सत्यं दमस", "यं न सन्त"]
    (s,) = det.suspects
    assert s["text"].startswith("न सुवृत्तं")


def test_base_a_keeps_its_frozen_behaviour() -> None:  # BASE-A is a frozen baseline: no crossing rule
    assert not load_config(baseline_mode="BASE-A").mode.get("reject_crossing", False)
    assert run(SHIFTED, "BASE-A").report["counters"]["crossing_rejects"] == 0
    assert run(SHIFTED).report["counters"]["crossing_rejects"] > 0
