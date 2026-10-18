"""Adversarial fixture harness (§22, §35, §47, TEST6-12).

Enabled fixtures are asserted; deferred fixtures are reported as skipped with
their milestone and are never counted as passing.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from padya.config import load_config
from padya.graphemes import utf16_offset
from padya.loader import document_from_text
from padya.pipeline import detect
from padya.regions import check_partition
from padya.scanner import scan

FIXTURES = sorted((Path(__file__).parent / "fixtures").glob("T*.yaml"))


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _detect(text: str, tier: str = "T"):
    return detect(document_from_text(text, doc_id="fixture", tier=tier), load_config(tier=tier))


def _projection(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[।॥]", " ", text)).strip()


def _check_verse(verse: dict, want: dict, text: str) -> None:
    if "text_starts" in want:
        assert verse["text"].startswith(want["text_starts"])
    if "text_ends" in want:
        assert verse["text"].endswith(want["text_ends"])
    for key in ("metre_id", "partial", "lg_full"):
        if key in want:
            assert verse[key] == want[key], key
    if "end_boundary" in want:
        for key, value in want["end_boundary"].items():
            assert verse["end_boundary"][key] == value, key
    if "pada_boundary_resolutions" in want:
        assert [b["resolution"] for b in verse["pada_boundaries"]] == want["pada_boundary_resolutions"]
        for b in verse["pada_boundaries"]:
            assert (b["offset"] is None) == (b["resolution"] != "exact_between_codepoints")
    assert verse["text"] == text[verse["start"]:verse["end"]]  # INV-1


@pytest.mark.parametrize("path", FIXTURES, ids=[p.stem for p in FIXTURES])
def test_fixture(path: Path) -> None:
    fx = _load(path)
    if fx["status"] == "deferred":
        pytest.skip(f"{fx['id']} deferred until {fx['deferred_until']}: {fx['reason']}")
    expect, text = fx["expect"], fx["text"]
    det = _detect(text, fx.get("tier", "T"))
    if "min_syllables" in expect:
        assert len(scan(document_from_text(text)).aksharas) >= expect["min_syllables"]
    assert len(det.verses) == expect["verse_count"], [v["text"] for v in det.verses]
    for verse, want in zip(det.verses, expect.get("verses", [])):
        _check_verse(verse, want, text)
    if "min_candidates" in expect:
        assert len(det.candidates) >= expect["min_candidates"]
    covers = [v["observed_cover"] for v in det.verses]
    assert all(a[1] <= b[0] for a, b in zip(covers, covers[1:])), "INV-4 overlap"
    if expect.get("regions_partition"):
        check_partition(det.char_regions, len(text))
    if expect.get("same_projection_as_paired"):
        paired = _detect(fx["paired_text"])
        assert [_projection(v["text"]) for v in det.verses] == [_projection(v["text"]) for v in paired.verses]
    if expect.get("check_utf16"):
        for v in det.verses:
            u16 = text.encode("utf-16-le")
            s16, e16 = utf16_offset(text, v["start"]), utf16_offset(text, v["end"])
            assert u16[2 * s16:2 * e16].decode("utf-16-le") == v["text"]  # OFF-6 round trip


def test_base8_no_partials_under_base_a() -> None:
    """BASE-8: a genuine half-verse with an ellipsis closer yields zero accepted partials."""
    text = "तथा च मनुः अयं निजः परो वेति गणना लघुचेतसाम् इत्यादि । ततः परं निर्णयः ।"
    assert text[11:44] == "अयं निजः परो वेति गणना लघुचेतसाम्"  # §35 T03 offsets
    assert _detect(text).verses == ()


def test_fixture_inventory_covers_t01_to_t42() -> None:
    ids = {p.stem for p in FIXTURES}
    expected_here = {f"T{i:02d}" for i in range(1, 43)} - {"T19", "T20", "T25", "T27", "T33", "T36", "T37", "T38"}
    assert expected_here <= ids, sorted(expected_here - ids)
