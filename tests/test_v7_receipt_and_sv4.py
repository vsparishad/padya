"""v7 additions: SV-4 verse-number fallback, SV-5 non-whitespace vedic runs, REC-1 receipts (§49, §50)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from padya.errors import ContractError
from padya.loader import CleanerRecord, document_from_text, known_receipts, load_cleaner_folder
from padya.scanner import scan
from tests.test_loader_cli import make_folder

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = json.loads((ROOT / "cleaner_receipt_v3.1.json").read_text(encoding="utf-8"))


def test_receipt_text_hash_and_offsets_reproduce() -> None:  # REC-3
    text = RECEIPT["fixture_cleaned_text"]
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == RECEIPT["fixture_cleaned_sha256"]
    for r in RECEIPT["fixture_records"]:
        seg = text[r["start"]:r["end"]]
        if r["kind"] == "verse_number":
            assert seg == r["number"]
        if r["kind"] == "flag" and r["cls"] == "double_virama":
            assert seg == "््"


def test_receipt_fixture_through_adapter_and_scanner() -> None:
    """The §49 fixture: three vedic words excluded, numerals outside the syllable stream."""
    text = RECEIPT["fixture_cleaned_text"]
    records = [CleanerRecord(r["kind"], r["start"], r["end"],
                             {k: v for k, v in r.items() if k not in ("kind", "start", "end")})
               for r in RECEIPT["fixture_records"]]
    doc = document_from_text(text, records=records, cleaner_version="3.1", tier="T")
    stream = scan(doc)
    excluded_src = "".join(text[a.src.start:a.src.end] for a in stream.aksharas if a.excluded)
    assert excluded_src == "अ॑ग्निꣳई॒ळेपुरो॑हितं"
    assert not any(ch.isdigit() or "०" <= ch <= "९" for a in stream.aksharas for ch in a.slp1)
    numbered = [(a.slp1, a.verse_num_after, a.verse_num_conf) for a in stream.aksharas if a.verse_num_after]
    assert numbered == [("mam", "१", 1.0), ("vIt", "२", 1.0)]  # SV-4 from records at tier-T confidence


def test_sv4_fallback_numeral_without_both_dandas() -> None:
    doc = document_from_text("होतारं रत्नधातमम् ॥ १२\nका ख ॥ ३ ॥ ततः १३ परम् ४।", tier="T")
    aks = scan(doc).aksharas
    tagged = {a.verse_num_after: (a.slp1, a.verse_num_conf) for a in aks if a.verse_num_after}
    assert tagged["१२"] == ("mam", pytest.approx(0.6))  # one daṇḍa, line end: fallback
    assert tagged["३"] == ("Ka", pytest.approx(0.6))  # no cleaner record: fallback, not 1.0
    assert tagged["४"] == ("ram", pytest.approx(0.6))  # daṇḍa after only
    assert "१३" not in tagged  # bare numeral in running text: not a token


def test_sv5_vedic_record_with_attached_danda_excludes_only_the_word() -> None:
    text = "क ख अ॑ग्निꣳ। ग घ"
    start, end = text.index("अ"), text.index("।") + 1  # non-whitespace run includes the daṇḍa
    doc = document_from_text(text, records=[CleanerRecord("vedic", start, end, {"marks": 1})])
    aks = scan(doc).aksharas
    assert [a.slp1 for a in aks if a.excluded] == ["a", "gniM"]
    assert sum(1 for a in aks if not a.excluded) == 4


def test_rec1_known_receipt_and_strict_mode(tmp_path: Path) -> None:
    assert known_receipts()["3.1"] == RECEIPT["cleaner_sha256"]
    docs = load_cleaner_folder(make_folder(tmp_path / "ok", manifest_extra={"cleaner_version": "3.1"}))
    assert not any("REC-1" in w for w in docs[0].warnings)
    folder = make_folder(tmp_path / "new", manifest_extra={"cleaner_version": "3.2"})
    assert any("REC-1" in w for w in load_cleaner_folder(folder)[0].warnings)
    with pytest.raises(ContractError, match="REC-1"):
        load_cleaner_folder(folder, strict=True)
