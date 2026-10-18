"""`verse-detect review PATH [--out OUT]`: tagged HTML pages + reports from a .txt file or a folder,
offline (no network, no LLM; fonts via local() only). Owner's request, 2026-10-18."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from padya.cli import main
from tools.devanagari_fonts import FONT_FACES

SLOKA = ("अथ धर्मशास्त्रम् । तत्र मनुराह —\n"
         "कुटुम्बं पीडयित्वापि ब्राह्मणाय महात्मने ।\nदातव्यं भिक्षवेऽन्नं वै आत्मनो भूतिमिच्छता ॥ १ ॥\n"
         "इति । தமிழ் உரை இங்கே. Some English too.\n")


def _corpus(tmp_path: Path) -> Path:
    folder = tmp_path / "corpus"
    (folder / "sub").mkdir(parents=True)
    (folder / "one.txt").write_text(SLOKA, encoding="utf-8")
    (folder / "sub" / "two.txt").write_text(SLOKA.replace("मनुराह", "याज्ञवल्क्य आह"), encoding="utf-8")
    return folder


def test_review_folder_writes_pages_index_reports_and_summary(tmp_path: Path, capsys) -> None:
    folder = _corpus(tmp_path)
    out = tmp_path / "rev"

    rc = main(["review", str(folder), "--out", str(out), "--jobs", "1", "--title", "Test review"])

    assert rc == 0
    for name in ("index.html", "metre_report.html", "metre_report.md", "summary.json"):
        assert (out / name).exists(), name
    assert sorted(p.name for p in (out / "pages").glob("*.html")) == ["one.detected.tagger.html", "two.detected.tagger.html"]
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["title"] == "Test review" and summary["mode"] == "BASE-C" and len(summary["texts"]) == 2
    assert all(t["verses"] == 1 for t in summary["texts"])
    printed = capsys.readouterr().out
    assert "2 text(s), 2 verses" in printed and "metre report" in printed


def test_pages_are_offline_and_carry_the_font_faces_and_the_verse_tag(tmp_path: Path) -> None:
    folder = _corpus(tmp_path)
    out = tmp_path / "rev"
    main(["review", str(folder), "--out", str(out), "--jobs", "1"])
    for page in [*(out / "pages").glob("*.html"), out / "index.html", out / "metre_report.html"]:
        html = page.read_text(encoding="utf-8")
        assert FONT_FACES in html, page.name
        assert "http://" not in html and "https://" not in html and "url(" not in html, page.name  # offline
    tags = re.search(r'<script id="embedded-tags" type="application/json">(.*?)</script>',
                     (out / "pages" / "one.detected.tagger.html").read_text(encoding="utf-8"), re.S)
    (verse,) = json.loads(tags.group(1))
    assert verse["label"] == "verse" and verse["text"].startswith("कुटुम्बं") and verse["metre_id"] == "anustubh"


def test_review_single_file_defaults_to_a_sibling_folder(tmp_path: Path) -> None:
    folder = _corpus(tmp_path)
    assert main(["review", str(folder / "one.txt"), "--jobs", "1"]) == 0
    out = folder / "one_review"
    assert (out / "index.html").exists() and (out / "pages" / "one.detected.tagger.html").exists()
    assert json.loads((out / "summary.json").read_text(encoding="utf-8"))["title"] == "one verse review"


def test_out_inside_the_input_folder_is_refused(tmp_path: Path, capsys) -> None:
    folder = _corpus(tmp_path)
    assert main(["review", str(folder), "--out", str(folder / "rev")]) == 2
    assert "inside the input folder" in capsys.readouterr().err


def test_missing_path_is_an_error(tmp_path: Path) -> None:
    assert main(["review", str(tmp_path / "nope")]) == 2


@pytest.mark.parametrize("mode", ["BASE-A", "BASE-C"])
def test_mode_is_recorded(tmp_path: Path, mode: str) -> None:
    folder = _corpus(tmp_path)
    out = tmp_path / mode
    main(["review", str(folder / "one.txt"), "--out", str(out), "--mode", mode, "--profile", "classical_strict", "--jobs", "1"])
    assert json.loads((out / "summary.json").read_text(encoding="utf-8"))["mode"] == mode
