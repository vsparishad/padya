"""tools/review_corpus.py: batch detection + review pages over a folder of texts."""
from __future__ import annotations

import json
from pathlib import Path

from tools.review_corpus import main, slug

VERSE = "राशिद्वयं यत्र मासे सङ्क्रमेत दिवाकरः । नाधिमासो भवेदेष मलमासस्तु केवलः ॥\n"


def test_slug_drops_suffix_and_unsafe_characters(tmp_path: Path) -> None:
    p = tmp_path / "Kṛtya" / "Kṛtyakalpataru of X: Vrata_Devanagari.txt"
    assert slug(p, tmp_path) == "Kṛtyakalpataru_of_X_Vrata"


def test_batch_builds_pages_index_and_summary(tmp_path: Path) -> None:
    src = tmp_path / "in" / "Book"
    src.mkdir(parents=True)
    (src / "a_Devanagari.txt").write_text("गद्यम् अत्र । " + VERSE, encoding="utf-8")
    (src / "b_Devanagari.txt").write_text("केवलं गद्यम् ।\n", encoding="utf-8")
    out = tmp_path / "out"
    assert main([str(tmp_path / "in"), "--out", str(out), "--jobs", "1"]) == 0
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    rows = {r["slug"]: r for r in summary["texts"]}
    assert rows["a"]["verses"] == 1 and rows["a"]["metres"] == {"anustubh": 1}
    assert rows["b"]["verses"] == 0 and summary["failures"] == []
    page = (out / rows["a"]["page"]).read_text(encoding="utf-8")
    assert '"source": "detector"' in page and "नाधिमासो" in page
    assert (src / "a_Devanagari.txt").read_text(encoding="utf-8").endswith(VERSE)  # input untouched
    index = (out / "index.html").read_text(encoding="utf-8")
    assert "pages/a.detected.tagger.html" in index and "2 texts" in index
