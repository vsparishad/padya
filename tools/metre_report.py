#!/usr/bin/env python3
"""Metre coverage and occurrence report for a review_corpus.py output folder.

usage: python3 tools/metre_report.py OUT [--md metre_report.md]

Reads OUT/summary.json and every OUT/runs/**/verses.jsonl and suspects.jsonl (counts only,
no verse text is copied), and writes OUT/metre_report.html plus an optional Markdown copy.
Counts are detector output, not gold: rare-metre counts in particular are unreviewed.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from tools.devanagari_fonts import FONT_FACES  # noqa: E402

METRES_YAML = ROOT / "padya" / "config" / "metres.yaml"
PROFILES_YAML = ROOT / "padya" / "config" / "profiles.yaml"
NOT_COVERED = [
    ("Āryā, Gīti, Upagīti, Udgīti", "mātrā (jāti)", "counted in mātrās with gaṇa rules; planned in the blueprint, not built"),
    ("Vaitālīya, Aupacchandasika", "mātrā (jāti)", "mātrā metres; not built"),
    ("Mātrāsamaka family", "mātrā (jāti)", "not built"),
    ("Viṣama metres (Udgatā etc.)", "viṣama", "four different pādas; not built"),
    ("Daṇḍaka", "long (>26 syllables)", "not built"),
    ("Sama metres not in the registry", "sama", "only the registered patterns listed above are matched"),
]


def load_registry(mode: str) -> list[dict]:
    metres = yaml.safe_load(METRES_YAML.read_text(encoding="utf-8"))["metres"]
    profiles = yaml.safe_load(PROFILES_YAML.read_text(encoding="utf-8"))
    enabled = _find_metres(profiles, mode)
    return [m for m in metres if m["id"] in enabled]


def _find_metres(node, mode: str, inside: bool = False) -> set[str]:
    """Metre ids enabled for *mode* in profiles.yaml (searched recursively; layout-agnostic)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "metres" and inside and isinstance(v, list):
                return set(v)
            found = _find_metres(v, mode, inside or k == mode)
            if found:
                return found
    return set()


def shape(m: dict) -> tuple[str, str]:
    """(syllables per pāda, L/G pattern) as display strings."""
    if m["id"] == "anustubh":
        return "8", "odd ××××LGG× (+ na/bha/ma/ra-vipulā), even ××××LGL×"
    if m.get("class") == "mixture":
        syl = "11/12" if m.get("mixed_lengths") else str(m["syllables_per_pada"])
        return syl, " / ".join(m["components"]) + " pādas mixed"
    if m.get("class") == "ardhasama":
        return f"{len(m['odd_pattern'])}/{len(m['even_pattern'])}", f"odd {m['odd_pattern']}, even {m['even_pattern']}"
    return str(m["syllables_per_pada"]), m.get("pattern", "")


def _jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def read_runs(out: Path) -> dict:
    per_text = defaultdict(Counter)  # slug -> metre -> verses (full + half)
    full, half, typo = Counter(), Counter(), Counter()
    pada_variants, upajati_mix = Counter(), Counter()
    for run in sorted((out / "runs").iterdir()):
        for path in run.rglob("verses.jsonl"):
            for r in _jsonl(path):
                mid = r["metre_id"]
                (half if r["partial"] == "half" else full)[mid] += 1
                per_text[run.name][mid] += 1
                if mid == "anustubh":
                    pada_variants.update(r["variant"][::2])  # odd pādas carry the variant
                elif mid.startswith("upajati"):
                    upajati_mix["".join("I" if v.startswith("indra") else "U" for v in r["variant"])] += 1
        for path in run.rglob("suspects.jsonl"):
            typo.update(r["metre_id"] for r in _jsonl(path))
    return {"per_text": per_text, "full": full, "half": half, "typo": typo,
            "pada_variants": pada_variants, "upajati_mix": upajati_mix}


def metre_rows(registry: list[dict], data: dict) -> list[dict]:
    total = sum(data["full"].values()) + sum(data["half"].values())
    rows = []
    for m in registry:
        mid = m["id"]
        n = data["full"][mid] + data["half"][mid]
        syl, pat = shape(m)
        rows.append({"id": mid, "name": m.get("display", mid), "class": m.get("class", "sama"), "syl": syl,
                     "pattern": pat, "full": data["full"][mid], "half": data["half"][mid], "total": n,
                     "share": n / total if total else 0.0, "typo": data["typo"][mid],
                     "texts": sum(1 for c in data["per_text"].values() if c[mid])})
    return sorted(rows, key=lambda r: (-r["total"], r["id"]))


def _others(c: Counter) -> list[tuple[str, int]]:
    return [(k, v) for k, v in c.most_common() if k != "anustubh"]


def _corpus_name(summary: dict) -> str:
    """Corpus name from review_corpus.py --title ("Smṛtimuktāphala verse review" → "Smṛtimuktāphala")."""
    title = summary.get("title") or "the digest corpus"
    return title.removesuffix(" verse review") if title != "Digest verse review" else "the digest corpus"


def markdown(rows: list[dict], data: dict, summary: dict, mode: str) -> str:
    out = [f"# Metres in {_corpus_name(summary)} ({len(summary['texts'])} texts, mode {mode})", "",
           "Detector output, not gold. Rare-metre counts are unreviewed; halves of long metres are the least certain. "
           "Typo = review-only near-misses, not counted as verses.", "",
           "## Metres covered and occurrences", "",
           "| # | Metre | Kind | Syll./pāda | Pattern | Full | Half | Total | Share | Typo | Texts |",
           "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
    out += [f"| {i} | {r['name']} | {r['class']} | {r['syl']} | `{r['pattern']}` | {r['full']:,} | {r['half']:,} | "
            f"{r['total']:,} | {r['share']:.2%} | {r['typo']:,} | {r['texts']} |" for i, r in enumerate(rows, 1)]
    out += ["", "## Not covered", "", "| Metre | Kind | Status |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in NOT_COVERED]
    pv = data["pada_variants"]
    out += ["", "## Anuṣṭubh odd pādas by variant", "", "| Variant | Odd pādas | Share |", "|---|---:|---:|"]
    out += [f"| {k} | {v:,} | {v / sum(pv.values()):.2%} |" for k, v in pv.most_common()]
    out += ["", "## Upajāti pāda mixtures (I = indravajrā/indravaṃśā, U = upendravajrā/vaṃśastha)", "",
            "| Pādas | Count |", "|---|---:|"]
    out += [f"| {k} | {v:,} |" for k, v in data["upajati_mix"].most_common()]
    out += ["", "## Per text", "", "| Text | Verses | Anuṣṭubh | Other metres | Typo | Top other metres |",
            "|---|---:|---:|---:|---:|---|"]
    for t in sorted(summary["texts"], key=lambda t: t["file"]):
        c = data["per_text"].get(t["slug"], Counter())
        others = _others(c)
        out.append(f"| {t['slug']} | {sum(c.values()):,} | {c['anustubh']:,} | {sum(v for _, v in others):,} | "
                   f"{t.get('typo_verses', 0):,} | {', '.join(f'{k} {v}' for k, v in others[:4]) or '—'} |")
    return "\n".join(out) + "\n"


CSS = """
:root { --bg:#faf8f3; --panel:#fff; --ink:#1f1d1a; --muted:#6b665d; --line:#e4dfd4; --accent:#7a3e12; --bar:#e9cfb4; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#17161a; --panel:#211f25; --ink:#eae6df; --muted:#9b958b; --line:#37343d; --accent:#e0995c; --bar:#5a3a22; } }
body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 var(--font-ui); }
main { max-width:1150px; margin:0 auto; padding:24px 16px 64px; }
h1 { font-size:22px; margin:0 0 4px; } h2 { font-size:17px; margin:32px 0 8px; } p { color:var(--muted); margin:0 0 14px; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:10px; margin:16px 0; }
.card { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:10px 14px; }
.card b { display:block; font-size:22px; } .card span { color:var(--muted); font-size:13px; }
.wrap { overflow-x:auto; background:var(--panel); border:1px solid var(--line); border-radius:8px; }
table { border-collapse:collapse; width:100%; } .wide { min-width:820px; }
th, td { padding:7px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }
td.n, th.n { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
td.bar { position:relative; min-width:130px; }
td.bar span { position:absolute; left:10px; top:8px; bottom:8px; background:var(--bar); border-radius:3px; max-width:calc(100% - 20px); }
td.bar em { position:relative; font-style:normal; font-variant-numeric:tabular-nums; }
.sub { color:var(--muted); font-size:12px; } code { font-size:12px; }
.two { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:16px; }
ul { margin:0; padding-left:20px; }
"""


def _metre_tr(i: int, r: dict, biggest: int) -> str:
    width = 100 if r["id"] == "anustubh" else 100 * r["total"] / biggest
    return (f"<tr><td class=n>{i}</td><td><b>{html.escape(r['name'])}</b><div class=sub>{html.escape(r['class'])} · "
            f"<code>{html.escape(r['pattern'])}</code></div></td><td class=n>{html.escape(r['syl'])}</td>"
            f"<td class=n>{r['full']:,}</td><td class=n>{r['half']:,}</td><td class=n><b>{r['total']:,}</b></td>"
            f"<td class=bar><span style='width:{width:.1f}%'></span><em>{r['share']:.2%}</em></td>"
            f"<td class=n>{r['typo']:,}</td><td class=n>{r['texts']}</td></tr>")


def _text_tr(t: dict, data: dict) -> str:
    c = data["per_text"].get(t["slug"], Counter())
    others = _others(c)
    top = ", ".join(f"{k} {v}" for k, v in others[:4]) or "—"
    return (f"<tr><td>{html.escape(t['slug'])}</td><td class=n>{sum(c.values()):,}</td><td class=n>{c['anustubh']:,}</td>"
            f"<td class=n>{sum(v for _, v in others):,}</td><td class=n>{t.get('typo_verses', 0):,}</td>"
            f"<td class=sub>{html.escape(top)}</td></tr>")


def html_page(rows: list[dict], data: dict, summary: dict, mode: str) -> str:
    biggest = max((r["total"] for r in rows if r["id"] != "anustubh"), default=0) or 1
    pv = data["pada_variants"]
    pvs = sum(pv.values()) or 1
    metres = "".join(_metre_tr(i, r, biggest) for i, r in enumerate(rows, 1))
    gaps = "".join(f"<li><b>{html.escape(a)}</b> ({html.escape(b)}) — {html.escape(c)}</li>" for a, b, c in NOT_COVERED)
    variants = "".join(f"<tr><td>{html.escape(k)}</td><td class=n>{v:,}</td><td class=n>{v / pvs:.2%}</td></tr>" for k, v in pv.most_common())
    mixes = "".join(f"<tr><td><code>{html.escape(k)}</code></td><td class=n>{v:,}</td></tr>" for k, v in data["upajati_mix"].most_common(16))
    texts = "".join(_text_tr(t, data) for t in sorted(summary["texts"], key=lambda t: t["file"]))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(_corpus_name(summary))} metre report</title><style>{FONT_FACES}{CSS}</style></head><body><main>
<h1>Metres in {html.escape(_corpus_name(summary))}</h1>
<p>{len(summary['texts'])} texts · mode {html.escape(mode)}. Detector output, not gold: rare-metre counts are unreviewed and halves of long metres are the least certain. Typo = review-only near-misses, not counted as verses. Bars for metres other than anuṣṭubh are scaled to the largest of them.</p>
<div class=cards>
<div class=card><b>{len(rows)}</b><span>metres covered</span></div>
<div class=card><b>{sum(1 for r in rows if r['total'])}</b><span>found in this corpus</span></div>
<div class=card><b>{sum(r['total'] for r in rows):,}</b><span>verses (full + half)</span></div>
<div class=card><b>{sum(data['typo'].values()):,}</b><span>typo verses for review</span></div>
</div>
<h2>Metres covered and occurrences</h2>
<div class=wrap><table class=wide><thead><tr><th class=n>#</th><th>Metre</th><th class=n>Syll./pāda</th><th class=n>Full</th><th class=n>Half</th><th class=n>Total</th><th>Share</th><th class=n>Typo</th><th class=n>Texts</th></tr></thead>
<tbody>{metres}</tbody></table></div>
<h2>Not covered yet</h2><ul>{gaps}</ul>
<div class=two>
<div><h2>Anuṣṭubh odd pādas by variant</h2><div class=wrap><table><thead><tr><th>Variant</th><th class=n>Pādas</th><th class=n>Share</th></tr></thead><tbody>{variants}</tbody></table></div></div>
<div><h2>Upajāti mixtures</h2><p>I = indravajrā/indravaṃśā pāda, U = upendravajrā/vaṃśastha pāda.</p><div class=wrap><table><thead><tr><th>Pādas</th><th class=n>Count</th></tr></thead><tbody>{mixes}</tbody></table></div></div>
</div>
<h2>Per text</h2>
<div class=wrap><table class=wide><thead><tr><th>Text</th><th class=n>Verses</th><th class=n>Anuṣṭubh</th><th class=n>Other</th><th class=n>Typo</th><th>Top other metres</th></tr></thead><tbody>{texts}</tbody></table></div>
</main></body></html>
"""


def write_report(out: Path, md: Path | None = None) -> tuple[int, int]:
    """Build OUT/metre_report.html (and a Markdown copy) from a review folder. Returns (covered, found)."""
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    registry = load_registry(summary["mode"])
    if not registry:
        raise SystemExit(f"no metres enabled for mode {summary['mode']} in {PROFILES_YAML}")
    data = read_runs(out)
    rows = metre_rows(registry, data)
    (out / "metre_report.html").write_text(html_page(rows, data, summary, summary["mode"]), encoding="utf-8")
    if md:
        md.write_text(markdown(rows, data, summary, summary["mode"]), encoding="utf-8")
    return len(rows), sum(1 for r in rows if r["total"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path, help="review_corpus.py output folder")
    ap.add_argument("--md", type=Path, help="also write a Markdown copy here")
    a = ap.parse_args(argv)
    covered, found = write_report(a.out, a.md)
    print(f"{covered} metres covered, {found} found; wrote {a.out / 'metre_report.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
