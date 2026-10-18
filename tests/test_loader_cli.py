"""Cleaner adapter §29.5 (fail closed, T20, TEST6-11), CLI §47.3, determinism T19/TEST6-10."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from padya.cli import main
from padya.errors import ContractError, OffsetError
from padya.loader import EXPECTED_OFFSETS, load_cleaner_folder, load_plain_text, sha256_text

VERSE = "अयं निजः परो वेति गणना लघुचेतसाम् उदारचरितानां तु वसुधैव कुटुम्बकम्"
TEXT = f"तथा च {VERSE} इति ।\n\nअत्र निर्णयः ।\n"


def make_folder(tmp: Path, *, manifest_extra=None, records=None, text=TEXT) -> Path:
    """SYNTHETIC cleaner folder (labelled as such); not real cleaner v3.0 output."""
    (tmp / "cleaned_devanagari").mkdir(parents=True)
    (tmp / "cleaned_records").mkdir()
    (tmp / "cleaned_devanagari" / "doc1.txt").write_text(text, encoding="utf-8")
    manifest = {"cleaner_version": "3.0", "source_tier": "T", "synthetic": True, "files": 1,
                "options": {"reading_view": False, "strip_accents": False, "sandhi_join": False},
                "offsets_refer_to": EXPECTED_OFFSETS}
    manifest.update(manifest_extra or {})
    (tmp / "cleaned_devanagari" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    lines = [json.dumps(r, ensure_ascii=False) for r in (records or [])]
    (tmp / "cleaned_records" / "doc1.txt.jsonl").write_text("\n".join(lines), encoding="utf-8")
    return tmp


def test_synthetic_folder_loads_with_explicit_warning(tmp_path) -> None:
    docs = load_cleaner_folder(make_folder(tmp_path))
    assert len(docs) == 1 and docs[0].synthetic and docs[0].tier == "T"
    assert any("SYNTHETIC" in w for w in docs[0].warnings)
    assert docs[0].text == TEXT and docs[0].text_sha256 == sha256_text(TEXT)  # INV-1, EDGE-9


def test_reading_view_is_refused(tmp_path) -> None:
    with pytest.raises(ContractError, match="reading_view"):
        load_cleaner_folder(make_folder(tmp_path, manifest_extra={"options": {"reading_view": True}}))


def test_unknown_offset_convention_fails_closed(tmp_path) -> None:
    with pytest.raises(ContractError, match="offsets_refer_to"):
        load_cleaner_folder(make_folder(tmp_path, manifest_extra={"offsets_refer_to": "utf-8 bytes"}))


def test_t20_out_of_range_record_fails_closed_without_outputs(tmp_path) -> None:
    folder = make_folder(tmp_path / "in", records=[{"kind": "flag", "cls": "orphan_matra", "start": 5, "end": 9999}])
    out = tmp_path / "out"
    assert main(["run", str(folder), "--out", str(out)]) == 2
    assert not out.exists()  # no partial success artifact (TEST6-11)
    with pytest.raises(OffsetError):
        load_cleaner_folder(folder)


def test_unsorted_records_fail_closed(tmp_path) -> None:
    recs = [{"kind": "vedic", "start": 10, "end": 12, "marks": 1}, {"kind": "vedic", "start": 2, "end": 4, "marks": 1}]
    with pytest.raises(ContractError, match="sorted"):
        load_cleaner_folder(make_folder(tmp_path, records=recs))


def test_sv5_vedic_record_excludes_text_from_detection(tmp_path) -> None:
    start = TEXT.index(VERSE)
    folder = make_folder(tmp_path / "in", records=[{"kind": "vedic", "start": start, "end": start + 3, "marks": 1}])
    out = tmp_path / "out"
    assert main(["run", str(folder), "--out", str(out)]) == 0
    verses = (out / "doc1.txt" / "verses.jsonl").read_text(encoding="utf-8")
    assert verses == ""  # first word excluded → no 32-syllable eligible window
    regions = [json.loads(x) for x in (out / "doc1.txt" / "regions.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(r["label"] == "excluded" for r in regions)


def test_plain_text_preserves_crlf_exactly(tmp_path) -> None:
    path = tmp_path / "x.txt"
    path.write_bytes((VERSE + "\r\n").encode("utf-8"))
    assert load_plain_text(path).text.endswith("\r\n")


def test_cli_deferred_and_unsupported_options_are_rejected(tmp_path, capsys) -> None:  # §47.3
    path = tmp_path / "x.txt"
    path.write_text(VERSE, encoding="utf-8")
    assert main(["evaluate"]) == 2
    assert main(["scan", str(path), "--retrieval"]) == 2
    assert main(["scan", str(path), "--chunk-syllables", "5000"]) == 2
    assert main(["scan", str(path), "--no-retrieval", "--no-models"]) == 0
    assert "not_implemented" in capsys.readouterr().err


@pytest.mark.slow
def test_t19_fresh_process_rerun_is_byte_identical(tmp_path) -> None:  # T19, TEST6-10
    folder = make_folder(tmp_path / "in")
    outs = []
    for k in range(2):
        out = tmp_path / f"out{k}"
        subprocess.run([sys.executable, "-m", "padya.cli", "run", str(folder), "--out", str(out),
                        "--emit-candidates"], check=True, capture_output=True)
        outs.append(out / "doc1.txt")
    for name in ("verses.jsonl", "regions.jsonl", "candidates.jsonl"):
        assert (outs[0] / name).read_bytes() == (outs[1] / name).read_bytes(), name
    reports = [json.loads((o / "report.json").read_text(encoding="utf-8")) for o in outs]
    for r in reports:
        r.pop("timing_seconds")  # wall-clock telemetry is excluded from equality (§26.6)
    assert reports[0] == reports[1]


def test_selftest_runs_offline() -> None:
    assert main(["selftest"]) == 0
