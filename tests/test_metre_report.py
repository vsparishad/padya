"""tools/metre_report.py: counts per metre from a synthetic review_corpus output folder."""
import json

from tools.metre_report import main


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def test_counts_full_half_typo_and_unfound_metres(tmp_path):
    # Arrange
    run = tmp_path / "runs" / "book" / "book_Devanagari"
    _write(run / "verses.jsonl", [
        {"metre_id": "anustubh", "partial": "full", "variant": ["pathya", "pathya", "na_vipula", "pathya"]},
        {"metre_id": "anustubh", "partial": "half", "variant": ["pathya", "pathya"]},
        {"metre_id": "upajati", "partial": "full", "variant": ["indravajra", "upendravajra", "indravajra", "indravajra"]},
    ])
    _write(run / "suspects.jsonl", [{"metre_id": "anustubh"}])
    (tmp_path / "summary.json").write_text(json.dumps(
        {"mode": "BASE-C", "texts": [{"slug": "book", "file": "book.txt", "typo_verses": 1}]}), encoding="utf-8")
    md = tmp_path / "m.md"

    # Act
    assert main([str(tmp_path), "--md", str(md)]) == 0

    # Assert
    report = md.read_text(encoding="utf-8")
    assert "| 1 | Anuṣṭubh (śloka) | grammar | 8 |" in report and "| 1 | 1 | 2 | 66.67% | 1 | 1 |" in report
    assert "| IUII | 1 |" in report and "| na_vipula | 1 | 33.33% |" in report
    assert "| Sragviṇī | sama | 12 |" in report.replace("| 34 ", "")  # covered but not found still listed
    assert (tmp_path / "metre_report.html").exists()
