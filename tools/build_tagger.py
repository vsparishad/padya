#!/usr/bin/env python3
"""Embed a UTF-8 text into tools/tagger/verse_tagger.html as an offline annotation page.

The text is embedded as an escaped JSON string (QC-4: no raw insertion, `<` and the
U+2028/U+2029 line separators are escaped). Offsets exported by the page are code
points into exactly the embedded text, whose SHA-256 is recorded in the metadata.

usage: python3 tools/build_tagger.py TEXT_FILE [--verses verses.jsonl] [--out PAGE.html] [--title NAME]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "tagger" / "verse_tagger.html"
_EMPTY_TEXT = '<script id="embedded-text" type="application/json">null</script>'
_EMPTY_META = '<script id="embedded-meta" type="application/json">null</script>'
_EMPTY_TAGS = '<script id="embedded-tags" type="application/json">null</script>'


def safe_json(value) -> str:
    """JSON that is safe inside a <script> element."""
    return (json.dumps(value, ensure_ascii=False)
            .replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def load_verses(verses_path: Path, text: str) -> list[dict]:
    """Detector verses.jsonl → seed tags. Every record must satisfy INV-1 against *text*."""
    tags = []
    with verses_path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            r = json.loads(line)
            start, end = r["start"], r["end"]
            if text[start:end] != r["text"]:
                raise SystemExit(f"{verses_path}:{line_no}: text mismatch at [{start}, {end}) — wrong text for this output?")
            tags.append({"start": start, "end": end, "label": "verse", "text": r["text"], "source": "detector",
                         "verse_id": r.get("verse_id"), "arc_posterior": r.get("arc_posterior"), "lg_full": r.get("lg_full"),
                         "variant": r.get("variant"), "metre_id": r.get("metre_id"), "detector_version": r.get("detector_version")})
    return tags


def load_suspects(path: Path, text: str) -> list[dict]:
    """Detector suspects.jsonl (review-only OCR near-misses) → seed tags labelled `typo`."""
    tags = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            r = json.loads(line)
            if text[r["start"]:r["end"]] != r["text"]:
                raise SystemExit(f"{path}:{line_no}: text mismatch at [{r['start']}, {r['end']})")
            tags.append({**{k: r.get(k) for k in ("start", "end", "text", "metre_id", "edits", "expected_lg", "observed_lg",
                                                  "suspect_syllables", "suspect_id", "detector_version")},
                         "label": "typo", "source": "detector"})
    return tags


def build(text_path: Path, out: Path, title: str | None, verses: Path | None = None,
          suspects: Path | None = None) -> dict:
    with text_path.open("r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    page = TEMPLATE.read_text(encoding="utf-8")
    if _EMPTY_TEXT not in page or _EMPTY_META not in page or _EMPTY_TAGS not in page:
        raise SystemExit("template placeholders not found")
    tags = load_verses(verses, text) if verses else None
    if suspects is None and verses is not None and (verses.parent / "suspects.jsonl").exists():
        suspects = verses.parent / "suspects.jsonl"  # written next to verses.jsonl by the detector
    if suspects is not None:
        tags = sorted((tags or []) + load_suspects(suspects, text), key=lambda t: t["start"])
    meta = {"file": text_path.name, "size": len(text.encode("utf-8")), "code_points": len(text),
            "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "built_by": "tools/build_tagger.py",
            "seeded_verses": sum(t["label"] == "verse" for t in tags or []),
            "seeded_typos": sum(t["label"] == "typo" for t in tags or []), "verses_file": verses.name if verses else None}
    page = page.replace(_EMPTY_TEXT, f'<script id="embedded-text" type="application/json">{safe_json(text)}</script>')
    page = page.replace(_EMPTY_META, f'<script id="embedded-meta" type="application/json">{safe_json(meta)}</script>')
    if tags:
        page = page.replace(_EMPTY_TAGS, f'<script id="embedded-tags" type="application/json">{safe_json(tags)}</script>')
    if title:
        page = page.replace("<title>Verse Tagger</title>", f"<title>{safe_json(title)[1:-1]}</title>", 1)
    out.write_text(page, encoding="utf-8")
    return meta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--title")
    ap.add_argument("--verses", type=Path, help="detector verses.jsonl to pre-load as tags (review mode)")
    ap.add_argument("--suspects", type=Path, help="detector suspects.jsonl (default: next to --verses)")
    a = ap.parse_args(argv)
    out = a.out or a.text.with_suffix(".detected.tagger.html" if a.verses else ".tagger.html")
    meta = build(a.text, out, a.title, a.verses, a.suspects)
    print(f"wrote {out} ({meta['code_points']} code points, {meta['seeded_verses']} seeded verses, "
          f"{meta['seeded_typos']} typo verses, sha256 {meta['source_sha256'][:16]}…)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
