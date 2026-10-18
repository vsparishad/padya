#!/usr/bin/env python3
"""Silver verse spans from typeset punctuation (§9.2 tier T, M0; GOLD-5, EVAL6-9).

A *silver* full verse is two consecutive 16-syllable units where the first unit
starts right after ॥ or a quotation mark and ends with ।, and the second ends with
॥ or a quotation mark. This is a conservative, punctuation-derived proxy: it misses
verses with other punctuation, can include metrical prose that an editor punctuated
like a verse, and is NEVER a headline metric. It is for development only.

`strip_punctuation` builds the T-stripped view by replacing daṇḍas, quotation marks
and digits with spaces, so code-point offsets are identical in both views (a
trivially monotone edit map, OFF-5).
"""
from __future__ import annotations

import bisect
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from padya.scanner import AksharaStream  # noqa: E402

UNIT_DELIMS = frozenset("।॥'‘’\"“”")
OPENERS = frozenset("॥'‘’\"“”")
CLOSERS = frozenset("॥'’\"”")
STRIP = frozenset("।॥'‘’\"“”०१२३४५६७८९0123456789")
HEMISTICH = 16


def strip_punctuation(text: str) -> tuple[str, dict]:
    stripped = "".join(" " if ch in STRIP else ch for ch in text)
    edit_map = {"kind": "same_length_substitution", "replaced_with": " ",
                "replaced_chars": "".join(sorted(STRIP)),
                "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "destination_sha256": hashlib.sha256(stripped.encode("utf-8")).hexdigest(),
                "offsets_identical": True}
    return stripped, edit_map


def _units(text: str) -> list[tuple[int, int, str | None, str | None]]:
    """(start, end, delimiter before, delimiter after) for text between delimiters."""
    units, start, before = [], 0, None
    for i, ch in enumerate(text):
        if ch in UNIT_DELIMS:
            units.append((start, i, before, ch))
            start, before = i + 1, ch
    units.append((start, len(text), before, None))
    return units


def silver_verses(text: str, stream: AksharaStream) -> list[dict]:
    starts = [a.src.start for a in stream.aksharas]

    def aks_in(s: int, e: int) -> tuple[int, int]:
        lo = bisect.bisect_left(starts, s)
        hi = lo
        while hi < len(starts) and stream.aksharas[hi].src.end <= e:
            hi += 1
        return lo, hi

    units = [(s, e, b, a, *aks_in(s, e)) for s, e, b, a in _units(text)]
    units = [u for u in units if u[5] > u[4]]  # drop units without syllables (verse numbers …)
    silver = []
    for (s1, e1, b1, a1, i1, j1), (s2, e2, b2, a2, i2, j2) in zip(units, units[1:]):
        if (j1 - i1, j2 - i2) != (HEMISTICH, HEMISTICH) or j1 != i2:
            continue
        if (b1 is None or b1 in OPENERS) and a1 == "।" and a2 in CLOSERS:
            cover = [stream.aksharas[i1].src.start, stream.aksharas[j2 - 1].src.end]
            silver.append({"observed_cover": cover, "syllables": [i1, j2], "status": "silver",
                           "source": "typeset_punctuation", "partial": "full"})
    return silver


def main(argv: list[str]) -> int:
    from padya.loader import load_plain_text
    from padya.scanner import scan

    path = Path(argv[0])
    doc = load_plain_text(path, tier="T")
    spans = silver_verses(doc.text, scan(doc))
    for span in spans:
        print(json.dumps({"doc_id": doc.doc_id, "source_sha256": doc.text_sha256, **span}, ensure_ascii=False))
    print(f"{len(spans)} silver spans (NOT gold; development only)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
