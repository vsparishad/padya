#!/usr/bin/env python3
"""BASE-A development evaluation against typeset-silver spans (BASE-11, EVAL6-9, GOLD-5).

For each input text, runs BASE-A on the T-punct view and the offset-identical
T-stripped view, then reports candidate recall by failure stage (not_enumerated,
failed_gate, lost_score/overlap), one-to-one exact matching against silver, and
the predictions that match no silver span. Silver is punctuation-derived and
unreviewed: these are debugging numbers, never headline precision/recall or FP/1k.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from padya.config import load_config  # noqa: E402
from padya.loader import document_from_text, load_plain_text  # noqa: E402
from padya.metres.anustubh import Profile, gate  # noqa: E402
from padya.pipeline import detect  # noqa: E402
from padya.scanner import scan  # noqa: E402
from tools.build_gold_from_typeset import silver_verses, strip_punctuation  # noqa: E402
from tools.metrics import match_spans  # noqa: E402


def _stage(silver: dict, det, stream, profile) -> str:
    """BASE-11 / OBJ-2 failure stage for one silver verse."""
    s, e = silver["syllables"]
    accepted = {tuple(v["observed_cover"]) for v in det.verses}
    if tuple(silver["observed_cover"]) in accepted:
        return "detected"
    first = stream.aksharas[s]
    if not (first.word_start or first.soft_start):
        return "not_enumerated"
    lg = "".join(a.weight for a in stream.aksharas[s:e])
    if not gate(lg, profile, 0.0).ok:
        return "failed_gate"
    cand = {tuple(c["syllables"]) for c in det.candidates}
    return "lost_score_or_overlap" if (s, e) in cand else "not_enumerated"


def evaluate_view(text: str, doc_id: str, silver: list[dict], profile) -> dict:
    doc = document_from_text(text, doc_id=doc_id, tier="T")
    det = detect(doc, load_config(tier="T"))
    stream = scan(doc)
    pred = [tuple(v["observed_cover"]) for v in det.verses]
    gold = [tuple(s["observed_cover"]) for s in silver]
    m = match_spans(pred, gold, "exact")
    stages: dict[str, int] = {}
    for s in silver:
        k = _stage(s, det, stream, profile)
        stages[k] = stages.get(k, 0) + 1
    matched = {p for p, _ in m.pairs}
    unmatched = [det.verses[i] for i in range(len(pred)) if i not in matched]
    return {
        "predicted": len(pred), "silver": len(gold), "exact_tp": m.tp,
        "silver_recall": round(m.tp / len(gold), 4) if gold else None,
        "share_of_predictions_matching_silver": round(m.tp / len(pred), 4) if pred else None,
        "unmatched_predictions": len(unmatched), "unmatched_zero_overlap": m.fp_zero_overlap,
        "silver_stage_counts": stages, "timing_s": det.report["timing_seconds"]["total_s"],
        "unmatched_examples": [{"cover": v["observed_cover"], "text": v["text"][:160]} for v in unmatched[:40]],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "runs" / "silver")
    args = parser.parse_args(argv)
    cfg = load_config(tier="T")
    profile = Profile.from_config(cfg.profile, cfg.weights)
    args.out.mkdir(parents=True, exist_ok=True)
    summary = []
    for path in args.files:
        doc = load_plain_text(path, tier="T")
        silver = silver_verses(doc.text, scan(doc))
        stripped, edit_map = strip_punctuation(doc.text)
        result = {"doc_id": doc.doc_id, "source_sha256": doc.text_sha256, "silver_status": "silver (unreviewed)",
                  "t_punct": evaluate_view(doc.text, doc.doc_id, silver, profile),
                  "t_stripped": evaluate_view(stripped, doc.doc_id, silver, profile), "edit_map": edit_map}
        (args.out / f"{doc.doc_id}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        row = {"doc": doc.doc_id, "silver": len(silver)}
        for view in ("t_punct", "t_stripped"):
            r = result[view]
            row[view] = {k: r[k] for k in ("predicted", "exact_tp", "silver_recall", "share_of_predictions_matching_silver",
                                           "unmatched_zero_overlap", "silver_stage_counts")}
        summary.append(row)
        print(json.dumps(row, ensure_ascii=False))
    (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
