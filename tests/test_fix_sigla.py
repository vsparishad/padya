"""tools/fix_sigla.py: restore IAST citation sigla from their letter-garbage Devanagari renderings
(reports/corpus_damage_scan.md §5 A.6). Source text is never changed in place; only listed sigla in
a safe context before a number are touched; real Devanagari words are left alone."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.fix_sigla import TABLE_DEFAULT, build_pattern, fix_text, load_table, run, unsafe_candidates

TABLE = load_table(TABLE_DEFAULT)


def test_table_has_restore_and_keep_rows_and_no_pronounceable_restore() -> None:
    actions = {s.action for s in TABLE}
    assert actions == {"restore", "keep"}
    for s in TABLE:
        if s.action == "restore":
            assert s.deva.endswith("्") or "्" in s.deva, s   # garbage renderings only
    assert {s.deva for s in TABLE if s.action == "keep"} >= {"मा", "वि", "सं", "मनु"}


def test_bracketed_citation_is_restored() -> None:
    # Arrange
    text = "न चैषा शुद्धिः ॥ [म्ध् ५․१२५] इति मनुः ।"

    # Act
    fixed, log = fix_text(text, TABLE)

    # Assert
    assert fixed == "न चैषा शुद्धिः ॥ [MDh 5․125] इति मनुः ।"
    assert [r["siglum"] for r in log] == ["MDh"] and log[0]["offset"] == text.index("म्ध्")


def test_line_start_sutra_siglum_and_second_citation_after_semicolon() -> None:
    text = "आप्ध्स् १․१․१․१ अथातः सामयाचारिकान् धर्मान् ।\nतथा [य्ध् २․५३; विध् ६․४१] इति ।"
    fixed, _ = fix_text(text, TABLE)
    assert fixed == "ĀpDhS 1․1․1․1 अथातः सामयाचारिकान् धर्मान् ।\nतथा [YDh 2․53; ViDh 6․41] इति ।"


def test_longest_siglum_wins() -> None:
    fixed, _ = fix_text("[ग्ध्स्-अ १,१ = ग्ध्स्-स्त् १․१]", TABLE)
    assert fixed == "[GDhS-A 1,1 = GDhS-St 1․1]"


def test_real_words_and_bare_renderings_are_untouched() -> None:
    # मा / वि / मनु are action=keep; a rendering without a number or outside a safe context stays
    text = "मा भैः । (मनु ८․१५०) इति । विद्वान् म्ध् इति न । धर्मम्ध् ५ इति"
    fixed, log = fix_text(text, TABLE)
    assert fixed == text and log == []
    assert unsafe_candidates(text, TABLE) == {"MDh": 1}   # glued to a word: counted, not touched


def test_idempotent_and_non_sigla_text_identical() -> None:
    text = "वसिष्ठः ॥ [वध् ३․५९]\nब्ध्स् १․१․१․२ तस्य वेदो मूलम् ॥"
    once, _ = fix_text(text, TABLE)
    twice, log2 = fix_text(once, TABLE)
    assert once == twice and log2 == []
    assert once == "वसिष्ठः ॥ [VaDh 3․59]\nBDhS 1․1․1․2 तस्य वेदो मूलम् ॥"   # only the citation's digits change


def test_run_writes_mirror_and_report_and_dry_run_writes_nothing(tmp_path: Path) -> None:
    src = tmp_path / "src" / "sub"
    src.mkdir(parents=True)
    (src / "a.txt").write_text("[म्ध् १] क\n", encoding="utf-8")
    (src / "b.txt").write_text("कखग\n", encoding="utf-8")
    out = tmp_path / "out"

    rep = run(tmp_path / "src", None, TABLE_DEFAULT, dry_run=True, report_path=tmp_path / "dry.json")
    assert not out.exists() and rep["replacements"] == {"MDh": 1} and rep["files"] == 2

    rep = run(tmp_path / "src", out, TABLE_DEFAULT, dry_run=False, report_path=out / "r.json")
    assert (out / "sub" / "a.txt").read_text(encoding="utf-8") == "[MDh 1] क\n"
    assert (out / "sub" / "b.txt").read_text(encoding="utf-8") == "कखग\n"
    saved = json.loads((out / "r.json").read_text(encoding="utf-8"))
    assert saved["files_changed"] == 1 and saved["contexts"][0]["file"] == "sub/a.txt"
    assert (src / "a.txt").read_text(encoding="utf-8") == "[म्ध् १] क\n"   # source untouched


def test_pada_markers_after_the_sutra_number() -> None:
    fixed, _ = fix_text("ब्ध्स् १․१․१․६च्द् शिष्टाः ।\nग्ध्स्-अ १,१․१४ब् । ग्ध्स्-स्त् १․१४: द्वौ", TABLE)
    assert fixed == "BDhS 1․1․1․6cd शिष्टाः ।\nGDhS-A 1,1․14b । GDhS-St 1․14: द्वौ"
    assert fix_text("[म्ध् ५․१२५]अथ", TABLE)[0] == "[MDh 5․125]अथ"   # a following word is not a marker


def test_pattern_requires_a_number() -> None:
    assert build_pattern(TABLE).search("[म्ध्] इति") is None


def test_duplicate_spellings_resolve_to_the_common_siglum() -> None:
    fixed, _ = fix_text("[य्ध् २․१२७] [ध्को ११४]", TABLE)
    assert fixed == "[YDh 2․127] [DhKo 114]"


@pytest.mark.parametrize("ctx", ["(म्ध् ५)", "[=म्ध् ५]", "/ म्ध् ५", "इति । म्ध् ५․७६]"])
def test_contexts(ctx: str) -> None:
    fixed, _ = fix_text(ctx, TABLE)
    assert "MDh 5" in fixed and "म्ध्" not in fixed, ctx


def test_apparatus_words_restored_only_before_a_siglum() -> None:
    fixed, _ = fix_text("[च्फ़्․ म्ध् ४․५; वध् ६․१] (काशिका ओन् पाण् ४․१․३१) सेए ग्ध्स्-अ २,१․६० । ओन् इति", TABLE)
    assert fixed == "[cf. MDh 4․5; VaDh 6․1] (काशिका on Pāṇ 4․1․31) see GDhS-A 2,1․60 । ओन् इति"
