"""`verse-detect` command line (§14, §47.3, API-1…API-4).

Options that the spec names but this increment does not implement are rejected
with a documented error, never silently ignored (§47.3, BASE-9).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from padya.config import load_config
from padya.errors import NotImplementedFeature, PadyaError
from padya.graphemes import is_grapheme_boundary, utf16_offset
from padya.loader import Document, load_cleaner_folder, load_plain_text
from padya.pipeline import detect
from padya.scanner import scan
from padya.selftest import run_selftest
from padya.writer import write_detection

DEFERRED = {
    "evaluate": "gold-set evaluation needs human-verified gold (M2+); tools/metrics.py has the matcher",
    "benchmark": "benchmarks need declared hardware and a frozen corpus (OPS-10)",
}


def _config(args):
    return load_config(profile=args.profile, baseline_mode=args.mode, tier=args.tier)


def _check_flags(args) -> None:
    if getattr(args, "retrieval", False):
        raise NotImplementedFeature("--retrieval: the reference index is not built (M6); BASE-A runs without it")
    if getattr(args, "models", False):
        raise NotImplementedFeature("--models: no prose LM exists yet; BASE-A is the --no-models baseline")
    if getattr(args, "chunk_syllables", None):
        raise NotImplementedFeature("--chunk-syllables: chunking (OPS-7/8) is deferred to M7")


def _summarise(det) -> str:
    r = det.report
    return (f"{r['source_id']}: {r['aksharas']} akṣaras, {r['counters']['candidate_arcs']} candidates, "
            f"{r['verses_accepted']} verses ({r['baseline_mode']} {'+'.join(r['anustubh_variants'])}, "
            f"uncalibrated) in {r['timing_seconds']['total_s']}s")


def _run_docs(docs: list[Document], args) -> int:
    config = _config(args)
    for doc in docs:
        det = detect(doc, config)
        print(_summarise(det))
        if args.out:
            print(f"  wrote {write_detection(det, Path(args.out), emit_candidates=args.emit_candidates)}")
    return 0


def cmd_scan(args) -> int:
    _check_flags(args)
    return _run_docs([load_plain_text(Path(args.file), tier=args.tier)], args)


def cmd_run(args) -> int:
    _check_flags(args)
    return _run_docs(load_cleaner_folder(Path(args.folder), strict=args.strict), args)


def cmd_dry_run(args) -> int:
    for doc in load_cleaner_folder(Path(args.folder)):
        stream = scan(doc)
        print(json.dumps({"doc": doc.doc_id, "chars": len(doc.text), "aksharas": len(stream.aksharas),
                          "runs": len(stream.runs)}, ensure_ascii=False))
    return 0


def cmd_diagnose_offset(args) -> int:
    doc = load_plain_text(Path(args.file))
    s, e = args.start, args.end
    print(json.dumps({
        "slice": doc.text[s:e], "start_grapheme_safe": is_grapheme_boundary(doc.text, s),
        "end_grapheme_safe": is_grapheme_boundary(doc.text, e),
        "utf16": [utf16_offset(doc.text, s), utf16_offset(doc.text, e)],
        "aksharas": [[a.idx, a.src.start, a.src.end, a.slp1, a.weight]
                     for a in scan(doc).aksharas if a.src.start < e and s < a.src.end],
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_review(args) -> int:
    """`verse-detect review PATH --out OUT`: detect, then write the tagged review pages and reports
    (§36 review.html, delivered as the tagger pages). Offline: no network, no LLM, local fonts only."""
    from tools.metre_report import write_report  # tools are packaged with padya; imported lazily
    from tools.review_corpus import review, text_files

    path = Path(args.path)
    if not path.exists():
        raise PadyaError(f"no such file or folder: {path}")
    files, root = text_files(path)
    if not files:
        raise PadyaError(f"no .txt files under {path}")
    out = Path(args.out) if args.out else path.with_name((path.stem if path.is_file() else path.name) + "_review")
    if out.resolve() == root.resolve() or root.resolve() in out.resolve().parents and path.is_dir():
        raise PadyaError(f"--out {out} lies inside the input folder; choose a folder outside it")
    title = args.title or f"{path.stem if path.is_file() else path.name} verse review"
    rows, failures = review(files, root, out, args.mode, args.profile, args.tier, args.jobs, title,
                            log=lambda m: print(m, flush=True))
    md = out / "metre_report.md"
    covered, found = write_report(out, md)
    verses = sum(r["verses"] for r in rows)
    print(f"{len(rows)} text(s), {verses:,} verses, {sum(r['halves'] for r in rows):,} halves, "
          f"{sum(r['typo_verses'] for r in rows):,} typo verses; {found} of {covered} metres found")
    print(f"tagged pages: {out / 'pages'}\nindex:        {out / 'index.html'}\nmetre report: {out / 'metre_report.html'} (+ .md)")
    if failures:
        print(f"{len(failures)} file(s) failed; see {out / 'summary.json'}", file=sys.stderr)
    return 1 if failures else 0


def _common(p) -> None:
    p.add_argument("--tier", default="unspecified", choices=["T", "P", "R", "unspecified"])
    p.add_argument("--profile", default="classical_strict", choices=["classical_strict", "classical_lenient"])
    p.add_argument("--mode", default="BASE-A", choices=["BASE-A", "BASE-C"],
                   help="BASE-A: frozen pathyā-only full verses; BASE-C: + vipulās and anchored halves (M2.5)")
    p.add_argument("--out", default=None)
    p.add_argument("--emit-candidates", action="store_true")
    p.add_argument("--no-retrieval", dest="retrieval", action="store_false", default=False)
    p.add_argument("--retrieval", dest="retrieval", action="store_true")
    p.add_argument("--no-models", dest="models", action="store_false", default=False)
    p.add_argument("--models", dest="models", action="store_true")
    p.add_argument("--chunk-syllables", type=int, default=None)
    p.add_argument("--strict", action="store_true", help="REC-1: unknown cleaner version is an error")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="verse-detect")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("selftest").set_defaults(func=lambda a: run_selftest())
    p = sub.add_parser("scan", help="detect verses in one plain UTF-8 text file")
    p.add_argument("file")
    _common(p)
    p.set_defaults(func=cmd_scan)
    p = sub.add_parser("run", help="detect verses in a cleaner output folder (§29)")
    p.add_argument("folder")
    _common(p)
    p.set_defaults(func=cmd_run)
    p = sub.add_parser("dry-run")
    p.add_argument("folder")
    p.set_defaults(func=cmd_dry_run)
    p = sub.add_parser("review", help="detect verses in a .txt file or a folder and write tagged HTML pages + reports")
    p.add_argument("path", help="a UTF-8 .txt file or a folder searched recursively for .txt files")
    p.add_argument("--out", default=None, help="output folder (default: <input>_review next to the input)")
    p.add_argument("--mode", default="BASE-C", choices=["BASE-A", "BASE-C"])
    p.add_argument("--profile", default="classical_lenient", choices=["classical_strict", "classical_lenient"])
    p.add_argument("--tier", default="unspecified", choices=["T", "P", "R", "unspecified"])
    p.add_argument("--jobs", type=int, default=3, help="parallel worker processes")
    p.add_argument("--title", default=None, help="heading of index.html")
    p.set_defaults(func=cmd_review)
    p = sub.add_parser("diagnose-offset")
    p.add_argument("file")
    p.add_argument("start", type=int)
    p.add_argument("end", type=int)
    p.set_defaults(func=cmd_diagnose_offset)
    for name in DEFERRED:
        sub.add_parser(name).set_defaults(func=lambda a, n=name: _deferred(n))
    return parser


def _deferred(name: str) -> int:
    raise NotImplementedFeature(f"{name}: {DEFERRED[name]}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except PadyaError as exc:
        print(f"error [{exc.code}]: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
