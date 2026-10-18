#!/usr/bin/env python3
"""Detect verses in every .txt under a folder and build one review page per text.

usage: python3 tools/review_corpus.py FOLDER --out out/digests [--mode BASE-C] [--profile classical_lenient]
                                      [--tier unspecified] [--jobs 3]

For each text: runs the detector, writes verses.jsonl/regions.jsonl/report.json under
OUT/runs/<slug>/, builds OUT/pages/<slug>.detected.tagger.html (detections pre-loaded
for correction, tools/tagger/verse_tagger.html), and computes a punctuation-derived
silver check (two ।/॥-bracketed 16-syllable units, tools/build_gold_from_typeset.py).
Silver numbers are debugging signals, not precision or recall (GOLD-5, EVAL6-9).
Finally writes OUT/index.html (links and per-text counts) and OUT/summary.json.
The input folder is only read, never written.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from padya.config import load_config  # noqa: E402
from padya.loader import load_plain_text  # noqa: E402
from padya.pipeline import detect  # noqa: E402
from padya.scanner import scan  # noqa: E402
from padya.writer import write_detection  # noqa: E402
from tools.build_gold_from_typeset import silver_verses  # noqa: E402
from tools.build_tagger import build as build_page  # noqa: E402
from tools.devanagari_fonts import FONT_FACES  # noqa: E402


def slug(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    name = rel.name.removesuffix("_Devanagari")
    return re.sub(r"[^\w.-]+", "_", name, flags=re.UNICODE).strip("_")


def process(path: Path, root: Path, out: Path, mode: str, profile: str, tier: str) -> dict:
    t0 = time.perf_counter()
    name = slug(path, root)
    doc = load_plain_text(path, tier=tier)
    det = detect(doc, load_config(baseline_mode=mode, profile=profile, tier=tier))
    run_dir = out / "runs" / name
    write_detection(det, run_dir)
    verses_path = next(run_dir.rglob("verses.jsonl"))
    page = out / "pages" / f"{name}.detected.tagger.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    build_page(path, page, f"{name} — detected verses ({mode})", verses_path)
    silver = silver_verses(doc.text, scan(doc))
    found = {tuple(v["observed_cover"]) for v in det.verses}
    silver_hit = sum(1 for s in silver if tuple(s["observed_cover"]) in found)
    metres = Counter(v["metre_id"] for v in det.verses)
    return {
        "slug": name, "file": str(path.relative_to(root)), "chars": len(doc.text),
        "aksharas": det.report["aksharas"], "verses": len(det.verses),
        "halves": sum(v["partial"] == "half" for v in det.verses),
        "vipula_verses": sum(any("vipula" in x for x in v["variant"]) for v in det.verses),
        "typo_verses": len(det.suspects),
        "metres": dict(metres.most_common()),
        "silver": len(silver), "silver_detected": silver_hit,
        "silver_recall": round(silver_hit / len(silver), 4) if silver else None,
        "page": str(page.relative_to(out)), "seconds": round(time.perf_counter() - t0, 1),
    }


def write_index(rows: list[dict], out: Path, mode: str, profile: str, title: str = "Digest verse review") -> None:
    total = {k: sum(r.get(k, 0) for r in rows) for k in ("chars", "verses", "halves", "typo_verses", "silver", "silver_detected")}
    body = "\n".join(
        "<tr><td><a href=\"{page}\">{name}</a><div class=sub>{file}</div></td><td class=n>{chars:,}</td>"
        "<td class=n>{verses:,}</td><td class=n>{halves:,}</td><td class=n>{other}</td><td class=n>{typos:,}</td><td class=n>{silver}</td></tr>".format(
            page=html.escape(r["page"]), name=html.escape(r["slug"]), file=html.escape(r["file"]), chars=r["chars"],
            verses=r["verses"], halves=r["halves"], typos=r.get("typo_verses", 0),
            other=sum(c for m, c in r["metres"].items() if m != "anustubh"),
            silver="—" if r["silver_recall"] is None else f"{r['silver_recall']:.0%} of {r['silver']:,}")
        for r in sorted(rows, key=lambda r: r["file"]))
    silver_all = f"{total['silver_detected'] / total['silver']:.1%}" if total["silver"] else "—"
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title>
<style>
{FONT_FACES}
:root {{ --bg:#faf8f3; --panel:#fff; --ink:#1f1d1a; --muted:#6b665d; --line:#e4dfd4; --accent:#7a3e12; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#17161a; --panel:#211f25; --ink:#eae6df; --muted:#9b958b; --line:#37343d; --accent:#e0995c; }} }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 var(--font-ui); }}
main {{ max-width:1100px; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:22px; margin:0 0 4px; }} p {{ color:var(--muted); margin:0 0 18px; }}
.wrap {{ overflow-x:auto; background:var(--panel); border:1px solid var(--line); border-radius:8px; }}
table {{ border-collapse:collapse; width:100%; min-width:640px; }}
th, td {{ padding:8px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
th {{ font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }}
td.n, th.n {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
a {{ color:var(--accent); font-weight:600; text-decoration:none; }} a:hover {{ text-decoration:underline; }}
.sub {{ color:var(--muted); font-size:12px; }} tfoot td {{ font-weight:600; }}
</style></head><body><main>
<h1>{html.escape(title)}</h1>
<p>{len(rows)} texts · mode {html.escape(mode)} · profile {html.escape(profile)}. Open a text to review and correct its detected verses; export from the page when done.
Typo verses = stanzas that fit a metre except for one or two OCR-damaged syllables (yellow on the page, suspect syllables underlined); they are suggestions for review, not counted as verses.
Silver = ślokas bracketed by daṇḍas in the edition, a rough recall check, not gold.</p>
<div class="wrap"><table><thead><tr><th>Text</th><th class=n>Characters</th><th class=n>Verses</th><th class=n>Halves</th><th class=n>Other metres</th><th class=n>Typo verses</th><th class=n>Silver found</th></tr></thead>
<tbody>{body}</tbody>
<tfoot><tr><td>All texts</td><td class=n>{total['chars']:,}</td><td class=n>{total['verses']:,}</td><td class=n>{total['halves']:,}</td><td></td><td class=n>{total['typo_verses']:,}</td><td class=n>{silver_all} of {total['silver']:,}</td></tr></tfoot>
</table></div></main></body></html>
"""
    (out / "index.html").write_text(page, encoding="utf-8")


def review(files: list[Path], root: Path, out: Path, mode: str = "BASE-C", profile: str = "classical_lenient",
           tier: str = "unspecified", jobs: int = 3, title: str = "Verse review", log=print) -> tuple[list[dict], list[dict]]:
    """Detect every file, build its review page, then index.html and summary.json under `out`.
    Returns (rows, failures); failures are also listed in summary.json. Reads `root` only."""
    out.mkdir(parents=True, exist_ok=True)
    rows, failures = [], []
    with ProcessPoolExecutor(max_workers=max(1, jobs)) as pool:
        futures = {pool.submit(process, f, root, out, mode, profile, tier): f for f in files}
        for fut in as_completed(futures):
            f = futures[fut]
            try:
                r = fut.result()
                rows.append(r)
                log(f"ok   {r['slug']}: {r['verses']} verses, {r['typo_verses']} typo verses, silver {r['silver_detected']}/{r['silver']} ({r['seconds']}s)")
            except Exception as exc:  # report and continue; failures are listed in summary.json
                failures.append({"file": str(f.relative_to(root)), "error": f"{type(exc).__name__}: {exc}"})
                log(f"FAIL {f.name}: {type(exc).__name__}: {exc}")
    write_index(rows, out, mode, profile, title)
    (out / "summary.json").write_text(json.dumps({"title": title, "mode": mode, "profile": profile, "tier": tier,
                                                   "texts": sorted(rows, key=lambda r: r["file"]), "failures": failures},
                                                  ensure_ascii=False, indent=1), encoding="utf-8")
    return rows, failures


def text_files(path: Path) -> tuple[list[Path], Path]:
    """A .txt file or a folder of them → (files, root for slugs)."""
    if path.is_file():
        return [path], path.parent
    return sorted(p for p in path.rglob("*.txt") if p.is_file()), path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", default="BASE-C")
    ap.add_argument("--profile", default="classical_lenient")
    ap.add_argument("--tier", default="unspecified")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--title", default="Digest verse review", help="heading of index.html")
    a = ap.parse_args(argv)
    files, root = text_files(a.folder)
    if not files:
        raise SystemExit(f"no .txt files under {a.folder}")
    rows, failures = review(files, root, a.out, a.mode, a.profile, a.tier, a.jobs, a.title,
                            log=lambda m: print(m, flush=True))
    print(f"{len(rows)} ok, {len(failures)} failed; index at {a.out / 'index.html'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
