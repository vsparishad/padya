"""Stage 7: BASE-A scorer (§8.1, §40, BASE-6, BASE-9, PR-1, PR-3, DEC-23).

With `--no-models` the only evidence is metrical: a log-likelihood ratio between
"uniform over the strings the enabled grammar admits" and a fixed i.i.d. L/G null.
Every candidate that passes the same grammar therefore gets the same LLR; BASE-A
is deliberately transparent. Values are empirical potentials, not probabilities.
Units (§8.1 v7): every LLR is a total over the candidate's syllables; `nu_start`
is the only per-event exposure term (DEC-23).
"""
from __future__ import annotations

from dataclasses import dataclass
from math import log
from typing import Mapping

from padya.candidates import Candidate
from padya.config import Config
from padya.metres import sama
from padya.metres.anustubh import Profile, log_language_size_for
from padya.metres.registry import CompiledMetre


@dataclass(slots=True, frozen=True)
class ScoredArc:
    arc_id: str
    s: int
    e: int
    score: float
    candidate: Candidate
    features: tuple[tuple[str, float], ...]  # natural-log units (§26.3)
    provenance: tuple[tuple[str, str], ...]


def null_log_prob(lg: str, p_light: float) -> float:
    """log P_null(lg); `?` slots are marginalised (probability 1)."""
    return sum(log(p_light) if w == "L" else log(1.0 - p_light) for w in lg if w in "LG")


def score(cand: Candidate, config: Config, profile: Profile,
          fixed_metres: Mapping[str, CompiledMetre] | None = None) -> ScoredArc:
    """Grammar side: uniform over the strings admitted by the candidate's own per-pāda
    variant assignment (so pathyā verses score exactly as under BASE-A); the variant and
    partial priors are explicit, separate terms (§8.1, §32.1)."""
    mode, w = config.mode, config.weights
    if mode["null_model"] != "uniform_lg":
        raise ValueError(f"unsupported null model {mode['null_model']!r}")
    p_light = float(mode["null_p_light"])
    known = sum(1 for x in cand.lg if x in "LG")
    if cand.metre_id == "anustubh":
        log_size = log_language_size_for(cand.gate.variants, profile)
        variant_w = sum(float(w["variant_prior"][v]) for v in cand.variant)
    else:
        fixed = fixed_metres or {}
        log_size = sama.log_language_size(fixed[cand.metre_id], fixed, cand.k, tuple(cand.pada_lengths))
        variant_w = 0.0  # mixture components carry no separate prior (§32.1 has none)
    grammar = -log_size * known / len(cand.lg)
    llr = grammar - null_log_prob(cand.lg, p_light)
    grammar_note = f"{cand.metre_id} " + "+".join(sorted(set(cand.variant)))
    metre_w = w["metre_prior"].get(cand.metre_id, w["metre_prior"]["default_vrtta"])
    features = (
        ("llr_metrical_vs_uniform_null", llr),
        ("metre_log_weight", float(metre_w)),
        ("variant_log_weight", variant_w),
        ("partial_log_weight", float(w["partial_prior"][f"k{cand.k}"])),
        ("uncertainty_penalty", -float(w["edits"]["lambda_edit"]) * cand.gate.cost),
        ("start_penalty", float(w["decoder"]["nu_start"])),
    )
    provenance = (
        ("llr_metrical_vs_uniform_null", f"{config.baseline_mode} null p_light={p_light}; grammar={grammar_note}"),
        ("metre_log_weight", "weights.yaml metre_prior (initial; default_vrtta when the metre has no entry)"),
        ("variant_log_weight", "weights.yaml variant_prior (initial)"),
        ("partial_log_weight", "weights.yaml partial_prior (initial; k = pāda count)"),
        ("uncertainty_penalty", "weights.yaml edits.lambda_edit × gate cost (SC-7)"),
        ("start_penalty", "weights.yaml decoder.nu_start (initial)"),
    )
    return ScoredArc(cand.cand_id, cand.s, cand.e, sum(v for _, v in features), cand, features, provenance)
