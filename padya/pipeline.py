"""End-to-end BASE-A detection for one document (§3, §40, §8.2 uncertain policy)."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any

from padya import DETECTOR_VERSION
from padya.annotate import RunMeta, build_verse, validate_verse
from padya.candidates import generate
from padya.config import Config, canonical_json
from padya.decoder import Arc, decode
from padya.loader import Document
from padya.errors import ValidationError
from padya.metres.anustubh import Profile
from padya.ocr_suspects import find_suspects
from padya.twins import twin_suspects
from padya.metres.registry import active_metres, compile_registry
from padya.regions import char_regions, check_partition, syllable_labels, syllable_regions
from padya.scanner import AksharaStream, scan
from padya.scorer import ScoredArc, score
from padya.types import Span


@dataclass(slots=True, frozen=True)
class Detection:
    doc: Document
    verses: tuple[dict, ...]
    syllable_regions: tuple[dict, ...]
    char_regions: tuple[dict, ...]
    candidates: tuple[dict, ...]
    report: dict
    suspects: tuple[dict, ...] = ()  # review-only OCR near-miss verses (padya/ocr_suspects.py)


def run_id_for(doc: Document, config: Config) -> str:
    """§26.6: deterministic run id derived from the run manifest, not wall-clock."""
    key = f"{doc.text_sha256}|{config.sha256()}|{DETECTOR_VERSION}"
    return "r_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _uncertain(stream: AksharaStream, accepted: set[int], p_verse: list[float | None],
               losers: list[ScoredArc], config: Config) -> tuple[set[int], dict[int, list[str]]]:
    """§8.2 initial abstention policy (CAL-5): mid-range lattice mass or near-miss losers."""
    u = config.weights["uncertain"]
    lo, hi, min_run, near = float(u["p_low"]), float(u["p_high"]), int(u["min_run_syllables"]), float(u["near_miss_score"])
    marked, alternatives = set(), {}
    run: list[int] = []
    for i, p in enumerate(p_verse + [None]):
        if p is not None and lo <= p <= hi and i not in accepted:
            run.append(i)
            continue
        if len(run) >= min_run:
            marked.update(run)
        run = []
    for arc in losers:
        if arc.score > near:
            for i in range(arc.s, arc.e):
                if i not in accepted:
                    marked.add(i)
                    alternatives.setdefault(i, []).append(arc.arc_id)
    return marked, alternatives


def _decode_runs(stream: AksharaStream, arcs: list[ScoredArc]):
    by_run: dict[int, list[ScoredArc]] = {}
    run_of = {}
    for r_idx, run in enumerate(stream.runs):
        for i in range(run.start, run.end):
            run_of[i] = r_idx
    for arc in arcs:
        by_run.setdefault(run_of[arc.s], []).append(arc)
    p_verse: list[float | None] = [None] * len(stream.aksharas)
    accepted, posterior, margins, log_z = [], {}, {}, 0.0
    for r_idx, run in enumerate(stream.runs):
        local = [Arc(a.arc_id, a.s - run.start, a.e - run.start, a.score) for a in by_run.get(r_idx, [])]
        result = decode(run.end - run.start, local)
        accepted.extend(result.accepted)
        posterior.update(result.arc_posterior)
        margins.update(result.margins)
        log_z += result.log_z
        for k, p in enumerate(result.p_prose):
            p_verse[run.start + k] = 1.0 - p
    return accepted, posterior, margins, p_verse, log_z


def detect(doc: Document, config: Config) -> Detection:
    t0 = time.perf_counter()
    compiled = compile_registry(config.metres)
    active = active_metres(compiled, config.mode["metres"], bool(config.mode["allow_unverified_grammar"]))
    editorial = config.mode.get("editorial_brackets", {})
    stream = scan(doc, editorial_max_chars=editorial["max_chars"] if editorial.get("enabled") else None,
                  citation_tokens=bool(editorial.get("enabled") and editorial.get("citation_tokens", False)))
    t_scan = time.perf_counter()
    fixed = {m.id: m for m in compiled if m.id in active and m.cls in ("sama", "mixture", "ardhasama")}
    fixed.update({m.id: m for m in compiled if m.cls == "sama" and any(m.id in f.components for f in fixed.values())})
    gen = generate(stream, doc.text_sha256, config, doc.noise_per_1000, doc.text,
                   {k: v for k, v in fixed.items() if k in active})
    profile = Profile.from_config(config.profile, config.weights)
    arcs = [score(c, config, profile, fixed) for c in gen.candidates]
    by_id = {a.arc_id: a for a in arcs}
    accepted, posterior, margins, p_verse, log_z = _decode_runs(stream, arcs)
    t_decode = time.perf_counter()
    span_marginal: dict[tuple[int, int], float] = {}
    for a in arcs:  # DP-4/DEC-14: union over canonical alternatives realising one span
        span_marginal[(a.s, a.e)] = span_marginal.get((a.s, a.e), 0.0) + posterior[a.arc_id]
    meta = RunMeta(run_id_for(doc, config), config.sha256(), config.registry_version, config.baseline_mode,
                   gen.search_incomplete, bool(config.mode["sc12_fused_closer_typing"]),
                   config.profile_name, tuple(config.mode["anustubh_variants"]))
    verses = []
    for aid in accepted:
        arc = by_id[aid]
        verse = build_verse(doc, stream, arc, posterior[aid], span_marginal[(arc.s, arc.e)], margins[aid], meta)
        validate_verse(doc, verse)
        verses.append(verse)
    accepted_set = set(accepted)
    accepted_slots = {i for aid in accepted for i in range(by_id[aid].s, by_id[aid].e)}
    losers = [a for a in arcs if a.arc_id not in accepted_set]
    uncertain, alternatives = _uncertain(stream, accepted_slots, p_verse, losers, config)
    vlist = [(v["verse_id"], by_id[v["candidate_id"]].s, by_id[v["candidate_id"]].e) for v in verses]
    labels = syllable_labels(stream, vlist, uncertain)
    syl = syllable_regions(stream, labels, p_verse, alternatives)
    covers = [(v["verse_id"], Span(*v["observed_cover"])) for v in verses]
    excluded = [a.src for a in stream.aksharas if a.excluded]
    unc_spans = [stream.aksharas[i].src for i in sorted(uncertain)]
    chars = char_regions(doc.text, covers, excluded, unc_spans)
    check_partition(chars, len(doc.text))
    cand_records = [_candidate_record(a, posterior[a.arc_id], stream, a.arc_id in accepted_set) for a in arcs]
    report = _report(doc, config, meta, stream, gen, verses, syl, active, log_z,
                     {"scan_s": t_scan - t0, "decode_s": t_decode - t_scan, "total_s": time.perf_counter() - t0})
    suspects: list[dict] = []
    ocr_cfg = config.mode.get("ocr_suspects") or {}
    if ocr_cfg.get("enabled"):
        accepted_spans = [(by_id[aid].s, by_id[aid].e) for aid in accepted]
        half_spans = [(by_id[aid].s, by_id[aid].e) for aid in accepted if by_id[aid].candidate.k == 2
                      and by_id[aid].candidate.metre_id == "anustubh"]
        full_only = frozenset(config.mode.get("full_only_metres", ()))  # full-stanza typo verses only
        suspects = find_suspects(doc, stream, accepted_spans, config.mode["anustubh_variants"], profile,
                                 {k: v for k, v in fixed.items() if k in active}, ocr_cfg, meta.run_id,
                                 half_spans, full_only)
        if config.mode.get("full_only_twin_halves"):
            suspects = sorted(suspects + _twin_suspects(doc, stream, by_id, accepted, suspects, fixed, full_only,
                                                        meta.run_id), key=lambda r: r["start"])
        for s in suspects:
            if s["text"] != doc.text[s["start"]:s["end"]]:
                raise ValidationError("INV-1: suspect text is not the exact source slice")
    report["ocr_suspects"] = len(suspects)
    return Detection(doc, tuple(verses), tuple(syl), tuple(chars), tuple(cand_records), report, tuple(suspects))


def _candidate_record(arc: ScoredArc, posterior: float, stream: AksharaStream, accepted: bool) -> dict:
    aks = stream.aksharas
    return {"candidate_id": arc.arc_id, "syllables": [arc.s, arc.e],
            "cover": [aks[arc.s].src.start, aks[arc.e - 1].src.end], "metre_id": arc.candidate.metre_id,
            "lg": arc.candidate.lg, "raw_score": round(arc.score, 6), "lattice_posterior": round(posterior, 9),
            "accepted": accepted, "features": [[k, round(v, 6)] for k, v in arc.features],
            "observed_cues": [[k, v] for k, v in arc.candidate.cues]}


def _report(doc, config, meta, stream, gen, verses, syl, active, log_z, timing) -> dict[str, Any]:
    labels: dict[str, int] = {}
    for r in syl:
        key = "verse" if r["label"].startswith("verse:") else r["label"]
        labels[key] = labels.get(key, 0) + r["syllable_count"]
    n = len(stream.aksharas)
    return {
        "source_id": doc.doc_id, "source_path": doc.path, "source_sha256": doc.text_sha256,
        "source_chars": len(doc.text), "source_tier": doc.tier, "cleaner_version": doc.cleaner_version,
        "synthetic_input": doc.synthetic, "loader_warnings": list(doc.warnings),
        "detector_version": DETECTOR_VERSION, "run_id": meta.run_id, "config_sha256": meta.config_sha256,
        "metre_registry_version": meta.registry_version, "baseline_mode": config.baseline_mode,
        "baseline_frozen_id": config.mode["frozen_id"], "profile": config.profile_name,
        "active_metres": list(active), "anustubh_variants": list(config.mode["anustubh_variants"]),
        "enabled_features": {k: config.mode[k] for k in ("use_cues_in_score", "use_frames", "use_prose_lm",
                                                         "use_retrieval", "ocr_edits", "sc12_fused_closer_typing")},
        "aksharas": n, "eligible_runs": len(stream.runs), "orphan_consonants": stream.orphan_chars,
        "verses_accepted": len(verses), "syllable_labels": labels,
        "candidate_density_per_1k_syllables": round(1000.0 * len(gen.candidates) / max(n, 1), 4),
        "counters": dict(gen.counters), "search_incomplete": gen.search_incomplete, "log_Z": log_z,
        "confidence": "uncalibrated: calibrated_probability is null for every record (CAL-1, CAL-4)",
        "product_scope": "candidate_extraction (REL6-11): no reviewed negative denominator; no precision claim",
        "release_blockers": _release_blockers(config, doc),
        "timing_seconds": {k: round(v, 4) for k, v in timing.items()},
        "config_echo": canonical_json(config.mode),
    }


def _release_blockers(config: Config, doc: Document) -> list[dict]:
    """REL6-12: machine-readable reasons this run is developer-alpha only."""
    enabled = "/".join(config.mode["anustubh_variants"])
    blockers = [
        {"code": "unverified_enabled_grammar", "detail": f"anustubh {enabled} has no recorded primary-source verification"},
        {"code": "missing_gold_negative_denominator", "detail": "no human-reviewed prose sample; FP/1k unknown"},
        {"code": "no_frozen_threshold", "detail": "release decisions are accepted_review, not accepted_strict"},
    ]
    if doc.cleaner_version == "none" or doc.synthetic:
        blockers.append({"code": "cleaner_contract_unverified",
                         "detail": "input is plain text or a synthetic fixture, not verified cleaner v3.0 output"})
    return blockers


def _twin_suspects(doc, stream, by_id, accepted, suspects, fixed, full_only, run_id) -> list[dict]:
    """Damaged twins of accepted one-line halves of full-only metres (padya/twins.py)."""
    halves = [(by_id[a].s, by_id[a].e, by_id[a].candidate.metre_id) for a in accepted
              if by_id[a].candidate.k == 2 and by_id[a].candidate.metre_id in full_only]
    if not halves:
        return []
    index = {a.src.start: i for i, a in enumerate(stream.aksharas)}
    ends = {a.src.end: i + 1 for i, a in enumerate(stream.aksharas)}
    blocked = [(by_id[a].s, by_id[a].e) for a in accepted]
    blocked += [(index[r["start"]], ends[r["end"]]) for r in suspects]
    return twin_suspects(doc, stream, halves, fixed, blocked, run_id)
