"""Stage 9: verse records (§8.3, §13.1, §24, INV-1…INV-9, CAL-4, CAL6-9).

Every number here is a raw potential or a lattice marginal. `calibrated_probability`
is always null in BASE-A (CAL-1, CAL-4); the release decision is review-only
because no frozen threshold or reviewed negative denominator exists (REL6-11).
"""
from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass
from typing import Any, Mapping

from padya import DETECTOR_VERSION, SCHEMA_VERSION
from padya.boundaries import end_anchor, pada_anchor, start_anchor
from padya.loader import Document
from padya.scanner import AksharaStream, contextual_final_weight
from padya.scorer import ScoredArc
from padya.types import Span


@dataclass(slots=True, frozen=True)
class RunMeta:
    run_id: str
    config_sha256: str
    registry_version: str
    baseline_mode: str
    search_incomplete: bool
    sc12: bool
    profile_name: str = "classical_strict"
    variants: tuple[str, ...] = ("pathya",)


def verse_id(doc: Document, cover: Span, parse_id: str) -> str:
    """INV-8: stable id from source hash, canonical cover and parse; never detection order."""
    key = f"verse|{doc.text_sha256}|{cover.start}|{cover.end}|{parse_id}"
    return "v_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def _alignment_trace(stream: AksharaStream, cover: Span) -> list[list[Any]]:
    edges = stream.analysis.edges
    i = bisect.bisect_left(stream.analysis.edge_src_starts, cover.start)
    trace = []
    for k in range(i, len(edges)):  # index loop: slicing the tuple would copy O(n) per verse
        ed = edges[k]
        if ed.src is None or ed.src.start >= cover.end:
            break
        an = ed.analysis.as_list() if ed.analysis else None
        trace.append([ed.src.start, ed.src.end, an, ed.rule_id, ed.kind])
    return trace


def _lg_full(stream: AksharaStream, s: int, e: int, starts: list[int]) -> str:
    weights = [a.weight for a in stream.aksharas[s:e]]
    weights[-1] = contextual_final_weight(stream.aksharas[e - 1])  # BASE-3/PH-3
    lg = "".join(weights)
    return " ".join(lg[a:b] for a, b in zip(starts, starts[1:] + [len(lg)]))


def _ocr_suspects(stream: AksharaStream, s: int, e: int) -> list[dict]:
    return [{"src_span": a.src.as_list(), "type": "uncertain_weight", "reason": sorted(a.flags) or ["SC-3"]}
            for a in stream.aksharas[s:e] if a.weight == "?"]


def build_verse(doc: Document, stream: AksharaStream, arc: ScoredArc, posterior: float,
                span_marginal: float, margin: float, meta: RunMeta) -> dict:
    aks, text, s, e = stream.aksharas, doc.text, arc.s, arc.e
    start_b = start_anchor(text, stream, s)
    end_t = end_anchor(text, stream, e, meta.sc12)
    cover = Span(aks[s].src.start, end_t.cover_end)
    k, lengths = arc.candidate.k, arc.candidate.pada_lengths
    starts = [sum(lengths[:i]) for i in range(k)]  # slot offset of each pāda within the window
    pada_b = [pada_anchor(text, stream, s + p) for p in starts[1:]]
    pada_covers = [[aks[s + p].src.start, aks[s + p + n - 1].src.end] for p, n in zip(starts, lengths)]
    pada_covers[-1][1] = cover.end
    fused = [b.to_json() for b in [start_b, *pada_b, end_t.anchor] if b.resolution != "exact_between_codepoints"]
    parse_id = "default-surface-v1" + (f"+{end_t.anchor.transformation}" if end_t.frame_overlap else "")
    status = "incomplete_search" if meta.search_incomplete else "uncalibrated"
    features = [[name, round(value, 6)] for name, value in arc.features]
    return {
        "schema_version": SCHEMA_VERSION,
        "verse_id": verse_id(doc, cover, parse_id),
        "source_id": doc.doc_id, "source_sha256": doc.text_sha256, "cleaner_version": doc.cleaner_version,
        "detector_version": DETECTOR_VERSION, "metre_registry_version": meta.registry_version,
        "config_sha256": meta.config_sha256, "run_id": meta.run_id, "baseline_mode": meta.baseline_mode,
        "start": cover.start, "end": cover.end, "text": text[cover.start:cover.end],
        "offset_unit": "unicode_codepoint", "source_tier": doc.tier,
        "metre_id": arc.candidate.metre_id, "variant": [v if v != "even" else "pathya" for v in arc.candidate.gate.variants],
        "partial": "full" if k == 4 else "half",
        "half_position": None, "quotation_type": "unknown",  # AN-6: halves are isomorphic
        "partial_anchor": arc.candidate.anchor,
        "caesura_unverified_padas": list(arc.candidate.gate.caesura_unverified),
        "padas": pada_covers, "boundary_status": "inferred", "sandhi_fused_boundaries": fused,
        "raw_score": round(arc.score, 6), "lattice_posterior": round(posterior, 9),
        "calibrated_probability": None, "confidence_status": status,
        "margin_to_next_best": round(margin, 6),
        "evidence_completeness": [f"gate:{arc.candidate.metre_id}_" + "+".join(sorted(set(arc.candidate.variant))), "null:uniform_lg"],
        "candidate_origin": arc.candidate.origin, "tier_rule": arc.candidate.tier_rule,
        "lg_full": _lg_full(stream, s, e, starts), "ocr_suspect": _ocr_suspects(stream, s, e),
        "trimmed_opener": None, "trimmed_closer": None,
        "attribution": {"raw": None, "primary_authority": None, "via_digest": None},
        "source_match": None, "split_pair": None, "evidence": features,
        "observed_cover": cover.as_list(), "start_boundary": start_b.to_json(),
        "end_boundary": end_t.anchor.to_json(), "pada_boundaries": [b.to_json() for b in pada_b],
        "surface_parse_id": parse_id, "source_alignment_trace": _alignment_trace(stream, cover),
        "metrical_slots": [[s + p, s + p + n] for p, n in zip(starts, lengths)],
        "reconstructed_reading": None, "frame_overlap": end_t.frame_overlap,
        "parse_exhaustive": True, "search_incomplete": meta.search_incomplete,
        "arc_posterior": round(posterior, 9), "span_marginal": round(span_marginal, 9),
        "evidence_provenance": [{"feature": f, "origin": o} for f, o in arc.provenance],
        "release_decision": "accepted_review",
        "grammar_profile": f"{meta.profile_name}:{'+'.join(meta.variants)}",
        "candidate_id": arc.candidate.cand_id,
        "observed_cues": [[name, value] for name, value in arc.candidate.cues],
    }


def validate_verse(doc: Document, verse: Mapping) -> None:
    """§24.1 invariants, checked before anything is written (fail closed)."""
    from padya.errors import ValidationError
    from padya.graphemes import is_grapheme_boundary

    start, end = verse["observed_cover"]
    if not (0 <= start < end <= len(doc.text)):
        raise ValidationError(f"INV-2: cover {start},{end} out of range")
    if (verse["start"], verse["end"]) != (start, end) or verse["text"] != doc.text[start:end]:
        raise ValidationError("INV-1: verse text is not the exact source slice of its cover")
    for b in [verse["start_boundary"], verse["end_boundary"], *verse["pada_boundaries"]]:
        exact = b["resolution"] == "exact_between_codepoints"
        if exact != (b["offset"] is not None):
            raise ValidationError("EDGE-2: offset present iff exact")
        if exact and not is_grapheme_boundary(doc.text, b["offset"]):
            raise ValidationError(f"EDGE-1: offset {b['offset']} is not a grapheme boundary")
    if verse["calibrated_probability"] is not None:
        raise ValidationError("CAL-4: calibrated_probability must be null when uncalibrated")
