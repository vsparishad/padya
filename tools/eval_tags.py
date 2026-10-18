#!/usr/bin/env python3
"""Score detector runs against tags exported (or saved) from tools/tagger/verse_tagger.html.

usage: python3 tools/eval_tags.py TEXT TAGS [--mode BASE-A|BASE-C] [--profile ...] [--tier T]

TAGS is either `<name>.annotations.jsonl` (export) or a saved copy of the tagger page
(its live <mark> elements carry the offsets). Gold spans are matched to predictions by
exact code-point interval and by overlap (intersection over union ≥ 0.8); the rest
are listed as misses and extras. The tagged sample is not a blind denominator, so
extras are "unmatched predictions", not a false-positive rate (GOLD-5, EVAL6-9).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from padya.config import load_config  # noqa: E402
from padya.loader import load_plain_text  # noqa: E402
from padya.pipeline import detect  # noqa: E402

MARK_RE = re.compile(r'<mark class="([^"]*)" data-start="(\d+)" data-end="(\d+)"(?: data-source="([^"]*)")?')


def load_tags(path: Path, text: str) -> list[dict]:
    raw = path.read_text(encoding="utf-8")
    if raw.lstrip().startswith("{"):
        tags = [json.loads(line) for line in raw.splitlines() if line.strip()]
    else:
        tags = [{"label": c.split()[0], "start": int(a), "end": int(b), "source": src or "human"}
                for c, a, b, src in MARK_RE.findall(raw)]
    for t in tags:
        if "text" in t and text[t["start"]:t["end"]] != t["text"]:
            raise SystemExit(f"tag [{t['start']},{t['end']}) does not match the text (INV-1)")
        t.setdefault("source", "human")
    return sorted(tags, key=lambda t: (t["start"], t["end"]))


def iou(a, b) -> float:
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    return inter / (max(a[1], b[1]) - min(a[0], b[0])) if inter else 0.0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", type=Path)
    ap.add_argument("tags", type=Path)
    ap.add_argument("--mode", default="BASE-A")
    ap.add_argument("--profile", default="classical_strict")
    ap.add_argument("--tier", default="T")
    a = ap.parse_args(argv)
    doc = load_plain_text(a.text, tier=a.tier)
    gold = [t for t in load_tags(a.tags, doc.text) if t["label"] in ("verse", "typo")]  # a typo verse is a verse
    det = detect(doc, load_config(baseline_mode=a.mode, profile=a.profile, tier=a.tier))
    preds = [(v["start"], v["end"], v) for v in det.verses]
    used, rows = set(), []
    for g in gold:
        gi = (g["start"], g["end"])
        best = max(((iou(gi, p[:2]), i) for i, p in enumerate(preds) if i not in used), default=(0.0, None))
        status = "exact" if best[0] == 1.0 else "overlap" if best[0] >= 0.8 else "miss"
        if best[1] is not None and status != "miss":
            used.add(best[1])
        elif any(p[0] <= g["start"] and g["end"] <= p[1] and p[2]["partial"] == "full" for p in preds):
            status = "inside_full"  # a tagged half that lies inside a predicted full verse
        rows.append({"start": g["start"], "end": g["end"], "source": g["source"], "status": status,
                     "iou": round(best[0], 3), "text": doc.text[g["start"]:g["end"]][:60]})
    extras = [p[2] for i, p in enumerate(preds) if i not in used]
    by = {}
    for r in rows:
        by.setdefault(r["source"], {}).setdefault(r["status"], 0)
        by[r["source"]][r["status"]] += 1
    summary = {"mode": a.mode, "profile": a.profile, "gold": len(gold), "predicted": len(preds),
               "exact": sum(r["status"] == "exact" for r in rows), "overlap": sum(r["status"] == "overlap" for r in rows),
               "inside_full": sum(r["status"] == "inside_full" for r in rows),
               "miss": sum(r["status"] == "miss" for r in rows), "unmatched_predictions": len(extras),
               "by_source": by, "halves_predicted": sum(v["partial"] == "half" for v in det.verses),
               "variants_predicted": sorted({x for v in det.verses for x in v["variant"] if x != "pathya"})}
    print(json.dumps(summary, ensure_ascii=False))
    for r in rows:
        if r["status"] != "exact":
            print(f"  {r['status']:7s} iou={r['iou']:<5} [{r['start']},{r['end']}) {r['source']:8s} {r['text']!r}")
    for v in extras:
        print(f"  extra   [{v['start']},{v['end']}) {v['partial']:4s} {v['text'][:60]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
