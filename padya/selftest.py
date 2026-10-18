"""`verse-detect selftest`: offline, no keys, no private corpora (API-4, M0 gate)."""
from __future__ import annotations

from typing import Callable

from padya.config import load_config
from padya.loader import document_from_text, sha256_text
from padya.metres.registry import compile_registry
from padya.pipeline import detect

# §13.1 fixture: 91 code points, SHA-256 and [15,82) are mechanically checked (validation.json).
EXAMPLE = "अत्र केचिदाहुः अयं निजः परो वेति गणना लघुचेतसाम् उदारचरितानां तु वसुधैव कुटुम्बकम् इत्यादि।"
EXAMPLE_SHA = "5b8014f44480aa9ec2462ee67ff095cd5147e9126cd280bc191ef37340f89a32"
PROSE = "अत्र केचिदाहुः प्रातःकाले स्नानं कृत्वा संध्यावन्दनं कर्तव्यमिति तन्न युक्तम् देशकालादिभेदेन व्यवस्थाया दृष्टत्वात् ।"


def _check_example() -> str:
    assert len(EXAMPLE) == 91 and sha256_text(EXAMPLE) == EXAMPLE_SHA, "fixture text drifted"
    det = detect(document_from_text(EXAMPLE, doc_id="fixture-001"), load_config())
    assert len(det.verses) == 1, f"expected one verse, got {len(det.verses)}"
    v = det.verses[0]
    assert v["observed_cover"] == [15, 82], v["observed_cover"]
    assert v["text"] == EXAMPLE[15:82]
    assert v["calibrated_probability"] is None
    return f"verse [15,82) lg={v['lg_full']} score={v['raw_score']:.3f}"


def _check_prose() -> str:
    det = detect(document_from_text(PROSE, doc_id="prose"), load_config())
    assert not det.verses, "prose produced a verse"
    return "no verse in prose sample"


def _check_registry() -> str:
    compiled = compile_registry(load_config().metres)
    return f"{len(compiled)} registry entries compiled (none verified)"


def _check_determinism() -> str:
    a = detect(document_from_text(EXAMPLE, doc_id="d"), load_config())
    b = detect(document_from_text(EXAMPLE, doc_id="d"), load_config())
    assert a.verses == b.verses and a.char_regions == b.char_regions, "rerun differs"
    return "identical verses and regions on rerun"


CHECKS: tuple[tuple[str, Callable[[], str]], ...] = (
    ("registry compiles", _check_registry),
    ("§13.1 example detected exactly", _check_example),
    ("prose sample abstains", _check_prose),
    ("deterministic rerun", _check_determinism),
)


def run_selftest() -> int:
    failures = 0
    for name, fn in CHECKS:
        try:
            print(f"PASS  {name}: {fn()}")
        except Exception as exc:  # report every check, never stop at the first
            failures += 1
            print(f"FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"{len(CHECKS) - failures}/{len(CHECKS)} selftest checks passed")
    return 1 if failures else 0
