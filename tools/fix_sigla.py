"""Restore citation sigla that the IAST→Devanagari conversion turned into letter garbage.

The IAST editions cite with sigla such as `[MDh 5.125]`, `ĀpDhS 1.1.1.1 …`, `(GDh 17.8-9)`. The
converter transliterated them letter by letter (`[म्ध् ५․१२५]`, `आप्ध्स् १․१․१․१`), which the
scanner then reads as syllables. This tool puts the IAST siglum back, and nothing else:

* only sigla listed with action `restore` in data/sigla.tsv (reports/corpus_damage_scan.md §5 A.6);
* only when the rendering is followed by a number and is not glued to a preceding Devanagari letter
  (every restore-rendering is letter garbage such as `म्ध्`, never a Sanskrit word, so "siglum + number"
  is the safeguard; typical places are a line start, `[`, `(`, `; `, `cf. `, `on `);
* the apparatus words `cf.`, `on`, `see`, which the converter also transliterated (`च्फ़्․`, `ओन्`, `सेए`),
  are restored only when they stand directly before a restored siglum;
* renderings that are also real Devanagari words (मा, वि, सं, मनु …; action `keep`) are never touched;
* the citation's own number is written with ASCII digits as in the IAST source (`[MDh 5․125]`), and a
  pāda marker glued to it (`६च्द्` → `6cd`, `१४ब्` → `14b`) is restored with it; verse numbers and every
  other digit in the text are left as they are.

Output goes to a mirror folder (`--out`), never in place; a JSON report lists every replacement with
its context so it can be reviewed. `--dry-run` writes the report only.

Usage: python tools/fix_sigla.py FOLDER --out OUT_FOLDER [--table data/sigla.tsv] [--dry-run] [--report R.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TABLE_DEFAULT = Path(__file__).resolve().parents[1] / "data" / "sigla.tsv"
NUMBER = r"\.?[ \t]?[<]?[0-9०-९]+(?:[․.,:\-][0-9०-९]+)*"   # 5․125  1․1․1․1  17․8-9  <112․1  2,1
DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
PADA_MARKERS = {"अब्": "ab", "च्द्": "cd", "अ": "a", "ब्": "b", "च्": "c", "द्": "d"}   # BDhS 1․1․1․6cd, GDhS-A 1,1․14b
PADA_RE = "(" + "|".join(re.escape(k) for k in sorted(PADA_MARKERS, key=len, reverse=True)) + r")?(?![\u0900-\u097f])"
LEAD_IN = r"(?<![\u0900-\u097f])"                                # not the tail of a Devanagari word
EDITORIAL = {"च्फ़्․": "cf.", "च्फ़्.": "cf.", "ओन्": "on", "सेए": "see"}   # apparatus words before a siglum
EDITORIAL_RE = "(?:(" + "|".join(re.escape(k) for k in EDITORIAL) + r")[ \t]+)?"
SNIPPET = 28


@dataclass(frozen=True, slots=True)
class Siglum:
    iast: str
    deva: str
    action: str
    expansion: str


def load_table(path: Path) -> tuple[Siglum, ...]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("siglum\t"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            raise ValueError(f"{path}: bad row {line!r}")
        rows.append(Siglum(parts[0], parts[1], parts[2], parts[6] if len(parts) > 6 else ""))
    if not rows:
        raise ValueError(f"{path}: no sigla")
    return tuple(rows)


def build_pattern(table: tuple[Siglum, ...]) -> re.Pattern | None:
    """One alternation over the restore-renderings, longest first, in a safe context before a number."""
    restore = sorted((s for s in table if s.action == "restore"), key=lambda s: -len(s.deva))
    if not restore:
        return None
    alt = "|".join(re.escape(s.deva) for s in restore)
    return re.compile(LEAD_IN + EDITORIAL_RE + "(" + alt + ")(" + NUMBER + ")" + PADA_RE)


def fix_text(text: str, table: tuple[Siglum, ...], pattern: re.Pattern | None = None) -> tuple[str, list[dict]]:
    """Return (fixed text, replacements). Each replacement: offset in the ORIGINAL text, siglum, snippet."""
    pattern = pattern or build_pattern(table)
    if pattern is None:
        return text, []
    by_deva = {s.deva: s for s in table if s.action == "restore"}
    out, pos, log = [], 0, []
    for m in pattern.finditer(text):
        sig = by_deva[m.group(2)]
        out.append(text[pos:m.start()])
        if m.group(1):
            out.append(EDITORIAL[m.group(1)] + " ")
        out.append(sig.iast + m.group(3).translate(DEVA_DIGITS) + PADA_MARKERS.get(m.group(4) or "", ""))
        pos = m.end()
        log.append({"offset": m.start(), "siglum": sig.iast, "deva": sig.deva,
                    "before": text[max(0, m.start() - SNIPPET):m.end() + SNIPPET].replace("\n", "⏎")})
    out.append(text[pos:])
    return "".join(out), log


def unsafe_candidates(text: str, table: tuple[Siglum, ...]) -> Counter:
    """Renderings glued to a preceding Devanagari letter but followed by a number: counted, left alone."""
    c: Counter = Counter()
    for s in table:
        if s.action != "restore":
            continue
        rx = re.compile(r"(?<=[ऀ-ॿ])" + re.escape(s.deva) + r"(?=" + NUMBER + ")")
        n = len(rx.findall(text))
        if n:
            c[s.iast] += n
    return c


def run(folder: Path, out: Path | None, table_path: Path, dry_run: bool, report_path: Path) -> dict:
    table = load_table(table_path)
    pattern = build_pattern(table)
    files = sorted(p for p in folder.rglob("*.txt") if not any(part.startswith("cleaned_") for part in p.parts))
    report = {"source": str(folder), "out": None if dry_run else str(out), "table": str(table_path), "dry_run": dry_run,
              "files": 0, "files_changed": 0, "replacements": Counter(), "unsafe_left": Counter(), "per_file": {}, "contexts": []}
    for p in files:
        text = p.read_text(encoding="utf-8")
        fixed, log = fix_text(text, table, pattern)
        rel = str(p.relative_to(folder))
        report["files"] += 1
        if log:
            report["files_changed"] += 1
            report["per_file"][rel] = Counter(r["siglum"] for r in log)
            report["replacements"].update(report["per_file"][rel])
            report["contexts"].extend({"file": rel, **r} for r in log)
        report["unsafe_left"].update(unsafe_candidates(text, table))
        if not dry_run:
            dest = out / p.relative_to(folder)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(fixed, encoding="utf-8")
    report["replacements"] = dict(report["replacements"].most_common())
    report["unsafe_left"] = dict(report["unsafe_left"].most_common())
    report["per_file"] = {k: dict(v) for k, v in report["per_file"].items()}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", type=Path)
    ap.add_argument("--out", type=Path, help="mirror folder for the fixed files (required unless --dry-run)")
    ap.add_argument("--table", type=Path, default=TABLE_DEFAULT)
    ap.add_argument("--dry-run", action="store_true", help="write the report only")
    ap.add_argument("--report", type=Path, help="JSON report path (default: OUT/sigla_report.json)")
    a = ap.parse_args(argv)
    if not a.folder.is_dir():
        print(f"error: not a folder: {a.folder}", file=sys.stderr)
        return 2
    if not a.dry_run and a.out is None:
        print("error: --out is required unless --dry-run", file=sys.stderr)
        return 2
    if a.out is not None and a.folder.resolve() in (a.out.resolve(), *a.out.resolve().parents):
        print("error: --out must not be the source folder or one of its parents", file=sys.stderr)
        return 2
    report_path = a.report or ((a.out or Path("out")) / "sigla_report.json")
    rep = run(a.folder, a.out, a.table, a.dry_run, report_path)
    total = sum(rep["replacements"].values())
    print(f"{rep['files']} files, {rep['files_changed']} changed, {total:,} sigla restored"
          f"{' (dry run)' if a.dry_run else ''}; {sum(rep['unsafe_left'].values())} candidates left in unsafe contexts")
    for s, n in list(rep["replacements"].items())[:12]:
        print(f"  {s:<10}{n:>7,}")
    print(f"report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
