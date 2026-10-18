"""M0.5 integration receipt against the REAL cleaner (§29, §48 REL6-1, TEST6-11).

Runs the vendored `clean_sanskrit_corpus.py` v3.1 (owner-supplied, standard library
only) on a small corpus, then loads its output through the §29 adapter. The script's
SHA-256 is pinned so the receipt names exactly which producer was tested.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from padya.loader import EXPECTED_OFFSETS, load_cleaner_folder
from padya.scanner import scan

ROOT = Path(__file__).resolve().parents[1]
CLEANER = ROOT / "vendor" / "cleaner" / "clean_sanskrit_corpus.py"
CLEANER_SHA256 = "66e09ba8761205b50bf27f77171592454dc34d57941b15baf7a3fb1698501cf4"
VERSE = "अयं निजः परो वेति गणना लघुचेतसाम् । उदारचरितानां तु वसुधैव कुटुम्बकम् ॥ १ ॥"
VEDIC = "अ॒ग्निमी॑ळे पु॒रोहि॑तम्"
SAMPLE = f"तथा च मनुः {VERSE}\n\nक़ुरान: {VEDIC} इति श्रुतिः ।\nस्‌ थ विरामः ॥\n"

pytestmark = pytest.mark.skipif(not CLEANER.exists(), reason="vendored cleaner not present")


def _run_cleaner(folder: Path, *extra: str) -> None:
    subprocess.run([sys.executable, "-I", str(CLEANER), str(folder), "--workers", "1", *extra],
                   check=True, capture_output=True)


def test_vendored_cleaner_hash_is_the_receipt() -> None:
    assert hashlib.sha256(CLEANER.read_bytes()).hexdigest() == CLEANER_SHA256
    assert 'VERSION = "3.1"' in CLEANER.read_text(encoding="utf-8")


def test_cleaner_selftest_passes() -> None:
    proc = subprocess.run([sys.executable, "-I", str(CLEANER), "--selftest"], capture_output=True, text=True)
    assert proc.returncode == 0 and "SELFTEST: PASSED" in proc.stdout


def test_real_cleaner_output_loads_through_adapter(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text(SAMPLE, encoding="utf-8")
    _run_cleaner(tmp_path, "--tier", "T")
    manifest = json.loads((tmp_path / "cleaned_devanagari" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["offsets_refer_to"] == EXPECTED_OFFSETS and manifest["cleaner_version"] == "3.1"
    assert set(manifest["options"]) == {"slp1", "reading_view", "strip_accents", "sandhi_join", "records"}
    docs = load_cleaner_folder(tmp_path)
    assert len(docs) == 1
    doc = docs[0]
    assert doc.tier == "T" and doc.cleaner_version == "3.1" and not doc.synthetic
    assert doc.noise_per_1000 is not None  # cleaned_report.json per-file field
    kinds = {r.kind for r in doc.records}
    assert {"vedic", "verse_number"} <= kinds
    for r in doc.records:  # every record offset slices the cleaned text exactly
        assert 0 <= r.start < r.end <= len(doc.text)
    vn = next(r for r in doc.records if r.kind == "verse_number")
    assert doc.text[vn.start:vn.end] == "१" and vn.payload["number"] == "१"
    ved = [r for r in doc.records if r.kind == "vedic"]
    assert all(" " not in doc.text[r.start:r.end] for r in ved)  # one accented word each
    stream = scan(doc)
    excluded = [a for a in stream.aksharas if a.excluded]
    assert excluded and all(doc.text[a.src.start:a.src.end] in doc.text[ved[0].start:ved[-1].end] for a in excluded)
    assert any(not a.excluded for a in stream.aksharas)  # SV-5: the rest stays eligible


def test_adapter_refuses_reading_view_from_real_cleaner(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text(SAMPLE, encoding="utf-8")
    _run_cleaner(tmp_path, "--reading-view")
    with pytest.raises(Exception, match="reading_view"):
        load_cleaner_folder(tmp_path)


def test_adapter_warns_on_strip_accents_from_real_cleaner(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text(SAMPLE, encoding="utf-8")
    _run_cleaner(tmp_path, "--strip-accents")
    doc = load_cleaner_folder(tmp_path)[0]
    assert any("strip_accents" in w for w in doc.warnings)
    assert not [r for r in doc.records if r.kind == "vedic"]
