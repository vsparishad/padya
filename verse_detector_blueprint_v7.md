# पद्यज्ञापिनी — Sanskrit Verse Span Detector

## Project blueprint and engineering specification for an AI development agent

Project owner: Neelakantha Shastri (shastravid@gmail.com), Vaidika Samrakshana Parishad
Parent projects: Vāṅmayam / Granthanidhi
Version: 7.0 — 16 October 2026 (v6 retained; cleaner contract re-attested against the real v3.1 producer with an integration receipt; reconciliation ledger; shipped verifier)
Companion documents: `normalisation_spec_v2.md`, `clean_sanskrit_corpus.py` **v3.1** (SHA-256 `66e09ba8761205b50bf27f77171592454dc34d57941b15baf7a3fb1698501cf4`; the input producer — its records sidecar and manifest are the detector's input contract, attested in §49), `verify_verse_detector_v7.py`, `cleaner_receipt_v3.1.json`

---

## Revision 7.0 — what changed

v7 keeps every v6 rule. Its purpose is to close the single largest open item v6 left — "the cleaner was not supplied, so §29 is an expectation" — and to reconcile a few places where v6's additions and the older body of the text pull in different directions.

| change | detail | where |
|---|---|---|
| §29 re-attested | The real `clean_sanskrit_corpus.py` v3.1 (SHA-256 `66e09ba8761205b5…`) was run on a fixture that exercises every record kind; emitted text, records, manifest and report fields are embedded as an integration receipt with hashes. §29 is now a **verified producer contract**, satisfying REL6-1 for M0.5. | §29, §49 |
| Cleaner version | v3.0 → v3.1 (adds L0-3.9: ॆ ॊ ॅ ॉ / ऎ ऒ ऍ ऑ mapped to े ो / ए ओ, counted as `nonsanskrit_vowel_fixed`). No record-schema change. | §29.4 |
| Two producer facts not stated before | (a) a `vedic` record is a maximal **non-whitespace** run, so it may include an attached daṇḍa or quote mark; (b) a `verse_number` record requires a daṇḍa on **both** sides — `१२॥` at a line end without a leading daṇḍa is not a record, so SV-4 gets a fallback. | §29.2, SV-4 |
| `orphan_matra` semantics | the cleaner re-attaches a mātrā separated by a space from a consonant (L0-3.2) **before** flagging, so `orphan_matra` only survives when the mātrā has no consonant to attach to; the receipt fixture shows `क ा` → `का` with no flag. | §29.2 |
| Scorer exposure note | DEC-23's warning about mixing per-syllable averages with per-event weights is reconciled with §33.1: LLRs enter `S(c)` as **totals over the span**, `ν_start` is the only per-event opportunity term. | §8.1 |
| Verifier shipped | `verify_verse_detector_v7.py` is the seed of `tools/verify_spec.py` (§47.2): it checks the receipt hash against the cleaner file when both are present, re-validates the receipt's own offsets, parses all four YAML seeds, re-expands all gaṇa formulas, and checks fixture hashes. | §47.2, §50 |
| Reconciliation ledger | one table listing each v6 ↔ earlier-text tension and the reading that governs | §50 |

Nothing in v7 claims a measured accuracy, speed or calibration result; those remain targets until the gold sets exist.

## Revision 6.0 — verified improvements and remaining uncertainty

This revision preserves all of v5's normative stages and rule IDs. It adds **Sections 39–48** and refines the existing main specification wherever a new constraint would otherwise contradict an older statement. The central deliverable remains **high-precision discovery and demarcation of classical Sanskrit verses inside mixed prose**, not Vedic metre classification, a generic chandas web app, or OCR correction.

| v6 decision | why | normative section |
|---|---|---|
| Separate *observed detection*, *metrical hypothesis*, and *citation intent* | a recognisable cadence does not prove a quoted verse; 32-syllable coincidences are frequent enough to benchmark | §39, §42 |
| Use a deterministic two-pass discovery baseline before complex models | isolates candidate-recall failures from scorer errors and yields early evidence on punctuation-stripped text | §40 |
| Formalise emitted boundaries as graph edges over surface and phonological slots | avoids falsely claiming that sandhi-restored letters have exact source offsets | §41 |
| Require exact-gate confirmation after all fast prefilters | `?` is not a wildcard with zero cost, and pāda-specific constraints are not equivalent to Hamming masks | §40, §43 |
| Separate per-candidate calibration from per-document deployment threshold | event rate and candidate density vary across genres and OCR tiers | §44 |
| Add a truly blind **prose-denominator audit** and negative exposure control | FP/1k is meaningless without reviewing material the detector did *not* nominate | §45 |
| Constrain optional pair bonuses, retrieval, local OCR hypotheses by explicit ablations | keeps high-recall features from silently inflating false positives | §43, §46 |
| Define machine-readable fixture invariants and a rigorous benchmark manifest | permits an autonomous coding agent to demonstrate, not declare, correctness | §47 |
| Establish measured-scope release tiers and hard stop conditions | v1 can ship with pathyā-only if its limits are transparent and verified | §48 |

**Audit status.** This document's textual and mathematical contracts were reviewed; an attached v5 file is the only supplied implementation-related artifact in this turn. Its referenced cleaner program, normalisation specification, and annotated corpora were **not supplied here**, so the alleged exact cleaner contract in §29 is treated as a **candidate adapter contract pending integration against real files**, not independently attested truth. The manuscript-specific variants and metre entries remain `needs_verification` unless the verification ledger supplies evidence. No algorithmic accuracy or speed numbers are claimed as observed results.

---

## Revision 5.0 — what this revision adds

Version 5.0 keeps every v4 rule and adds the material an implementing agent would otherwise have to invent, plus three corrections.

| addition | section |
|---|---|
| Exact cleaner data contract (record kinds, manifest keys, report fields, adapter validations) | §29 |
| Typed interface contracts for every stage | §30 |
| Finite sandhi inventory at verse boundaries and a **normative attachment policy** for shared graphemes (closes the "documented attachment policy" placeholder in OFF-10) | §31 |
| `weights.yaml` with every *initial* value in one place; `metres.yaml` entry schema; `frames.yaml` and `authorities.yaml` seeds drawn from the owner's Nirṇayasindhu sample | §32 |
| Prose/verse LM and language-classifier implementation specs | §33 |
| Error taxonomy E01–E16 so milestone reports are comparable | §34 |
| Fixture file format for T01–T22 | §35 |
| Minimum viable path and explicit deferral list — what **not** to build before the first T-stripped number exists | §36 |
| Gold and review-decision JSON schemas | §37 |
| Glossary | §38 |

| correction | detail |
|---|---|
| Hariṇī | The v4 formula-derived string `LLLLLGGGGGLGLLGLG` (*na sa ma ra sa la ga*) agrees with the traditional definition (yati "rasa-yuga-haya" = 6, 4, 7 → positions 6 and 10). Status raised from `blocked` to `needs_verification` like every other registry entry; still not `verified` until the Vṛttaratnākara check is recorded. |
| Milestone table vs execution order | §12 now lists M0.5 (data contract) and M2.5 (vipulās one at a time) so the table and §27.3 agree. |
| T-fixture count | §12 referred to "T01–T30"; the fixture set is T01–T22 (§22) plus generated stress inputs. |

## Revision 4.0 — independently audited engineering clarifications

Version 4.0 retains the v3 pipeline, source tiers, goals, milestone ordering, and rule-ID conventions. Changes below address **implementation-breaking ambiguities**, not a change of scope. The product remains **classical Sanskrit verse-span detection in prose**, not Vedic metrical identification.

| audit finding | required correction | stage |
|---|---|---|
| A boundary can be lost in vowel/visarga sandhi | distinguish `surface_interval` from `phonological_boundary`; some underlying verse characters have **no exact surface substring** | loader, scanner, annotator, metrics |
| Meter-table Hariṇī mismatch | compile every gaṇa formula to L/G; quarantine discrepancies, correct the **formula-derived candidate** pending source verification | registry |
| Śloka bha-/ma-/ra-vipulā conditions mistaken/weak | use separate grammar predicates, require the relevant caesura where needed, and test positive/near-negative examples | gate |
| Bitmask treats `?` as a cost-free exact match | prefilter only; full gate charges uncertainty and validates grammar even at Hamming distance 0 | gate |
| Syllable weight depends on candidate boundaries | keep context-free vowel/mark traits and compute contextual weight within a proposed phonological parse | scanner, gate |
| Split half-verses have a joint bonus but decoder has only single arcs | use explicitly priced **paired-span macro arcs** or remove the joint bonus | candidates, decoder |
| Free candidates cross excluded regions | segment decoding at exclusion barriers; output excluded/non-Sanskrit regions independently | scanner, decoder |
| Exact surface offsets may be impossible in coalesced words | add `boundary_resolution` and a separate **phonological** boundary metric, never invent an offset | schema, gold, review |
| A single verse's metrical match can accidentally appear in prose | add conditioned hard-negative scorer and sampling-corrected evaluation; measure verse overlap, FP density and source coverage | model, metrics |
| Some v3 examples/requirements are internally contradictory | repair `lg_full`, stop claiming impossible character reconstructions and replace the invalid posterior-monotonicity property | fixtures, tests |
| Latency goals lack a reproducible cost model | publish baseline and adversarial latency/RSS per candidate-density band; prioritize correctness | operations |

**Authority hierarchy.** Human-verified edition and śāstric metre definition → mechanically consistent gaṇa expansion → independent analyser output → draft table. If sources conflict, mark the individual metre/variant `blocked`; continue unrelated milestones. Avoid interpreting an unverified pattern as settled by this document.

---

## Revision 3.0 — what changed and why

Three earlier drafts exist: v1.0 (the original architecture), "v2 hardening" (invariants, offsets, negatives, calibration, release gates) and "v2.0 enhanced" (sandhi phenomena, extended metre inventory, bit-parallel gate, multi-hop attribution). This revision keeps v1.0's pipeline and rule ids, absorbs both v2 drafts, and corrects the following points found while reconciling them.

| topic | resolution in v3.0 |
|---|---|
| Vedic material | Out of scope for metre. Spans the cleaner tagged as accented are excluded from the classical gate and emitted as `excluded` regions with `source_tag = vedic`. No Vedic metre name is ever produced; no syllable-count "Vedic" guess. (The owner's requirement is classical verse detection, not Vedic chandas identification.) |
| Ekādeśa across pāda junctions (v2.0 SC-10) | Real but **rare**; v2.0 overstated it as "regular". Kept as an opt-in hypothesis, default **off**, enabled only after its frequency is measured on gold T. |
| *Muta cum liquida* leniency (v2.0 SC-11) | Not a classical rule; an epic/Purāṇic licence. Kept as opt-in, default **off**, anuṣṭubh only, and requires owner confirmation (**ASK**) with examples from the corpus before enabling. |
| Mattamayūra pattern | v2.0 gave `GGGGLGLLGGLGG`; the gaṇa formula *ma-ta-ya-sa-ga* gives `GGGGGLLGGLLGG`. Entry marked `needs_verification` until checked against Vṛttaratnākara. |
| Vaitālīya cadence | v2.0 wrote "6 mātrās + LGLG" (6 mātrās, giving 12). The cadence is *ra-la-ga* = `GLGLG` (8 mātrās): odd pāda 6+8 = 14, even 8+8 = 16. Aupacchandasika adds a guru: `GLGLGG`, 16/18. |
| Āryā halves | First half 30 mātrās, second 27 (the `12+18 / 12+15` quarters are the same thing). Gīti 30+30, Upagīti 27+27, Udgīti 27+30. Stated once, consistently. |
| Anuṣṭubh 2–4 restriction | Stated precisely: in every pāda, syllables 2–4 must not be *na* (`LLL`) or *sa* (`LLG`); in even pādas *ra* (`GLG`) is additionally disallowed under the `classical_strict` profile (configurable). |
| Pāda boundary nudging | v1.0 allowed ±1 syllable shifts to word boundaries after validation. **Removed.** A different split is a different candidate: re-run the gate, re-score. Never shift silently. |
| Confidence | Lattice posterior and calibrated probability are separate fields. `calibrated_probability` is `null` until a calibration model has been fitted on a dev split and measured (Brier/ECE). |
| Gold from stripped typeset text | Automatic spans are **silver** until a sampled human audit; both variants of one passage stay in the same split. |
| Tier B pruning | Fail-fast on the first pāda is admissible only when no edits are allowed in that pāda; with a budget, use a lower bound, not a hard reject. |
| Performance claims | Targets are aspirational until measured on declared hardware; correctness and FP gates take priority. |

---

## 0. How to use this document

Written for an autonomous coding agent. Read entirely before writing code.

1. **Milestone gating.** Build M0 → M7 (section 12) in order. A milestone is complete only when its automated tests, invariant/property tests and gold-set metrics pass and `reports/M<n>.md` is written.
2. **Rule traceability.** Every rule has a stable id (`SV-3`, `SC-10`, `AN-2`, `A5`, `B3`, `F-4`, `R-2`, `C-6`, `INV-4`, `OFF-1`, `NEG-3`, `OCR-2`, `OPS-7`, `GOLD-4`, `CAL-2`, `QC-2`, `T07`). Put the id in docstrings, comments, test names (`test_sc12_fused_iti`) and commit messages.
3. **Zero mutation.** `Document.text` is never altered, normalised or "fixed". The detector annotates with stand-off offsets. Confidence is never a reason to fill or correct text.
4. **Tunables live in one file.** Every number marked *initial* is in `padya/config/weights.yaml`, changed only by `tools/tune.py` or with the owner's agreement.
5. **ASK** = stop on that sub-feature, summarise the ambiguity with corpus examples, wait. Ask only for genuinely blocking decisions; non-blocking defaults are in section 21.
6. **Empirical reporting.** No milestone is "done" by inspection. Report the full metric table (section 11), invariant pass/fail, and the 20 worst errors with diagnosis.
7. **Companion files are prerequisites, not assumptions.** Validate the cleaner's record schema and manifest against the actual files before relying on them; build adapter + fixtures; never invent their format.
8. **Prefer abstention to invention.** When evidence is ambiguous, emit alternatives and an `uncertain` region rather than a forced decision.
9. **No skipped test counts as passed.** `xfail` requires an issue id and is never counted toward milestone pass rates.

---

## 1. Problem statement and domain context

### 1.1 Input and output

**Input.** One Sanskrit work of arbitrary length (up to ~2 × 10⁶ syllables), Devanagari, mixed prose and verse (गद्य–पद्य मिश्रित), as produced by the cleaner:
`cleaned_devanagari/<file>`, `cleaned_records/<file>.jsonl` (flags, accented words, verse numbers, with offsets into the cleaned text), `manifest.json` (tier, cleaner version, options, offset convention).

Source tiers: **T** typeset / born-digital, **P** proofread OCR, **R** raw OCR.

**Output.** Stand-off annotations of detected full/partial verses and pratīkas, including exact **observed-surface** code-point intervals when representable, pāda *metrical* boundaries, metre and variant, scores, evidence, OCR events, attribution and reference matches. Crucially, an underlying philological boundary lost in external sandhi **may not have an exact character offset**. Such a boundary is represented explicitly as `shared_surface` or `unresolved` (OFF-7…OFF-12); never manufacture a Sanskrit substring that is not in `Document.text`.

### 1.2 Why this is harder than chandas identification

A chandas tool answers "what metre is this verse?" given a verse. This system answers "where are the verses?" given a book, and must reject metrical accidents in prose. In the target texts — in priority order Nirṇayasindhu, Dharmasindhu, Mitākṣarā, Smṛticandrikā, Caturvargacintāmaṇi (Hemādri), Madanaratna, Parāśaramādhavīya, Smṛtimuktāphala — five phenomena must be handled natively:

1. **Unmarked inline embedding.** Quotations run on with the prose: `तथा च मनुः अयं निजः परो वेति … कुटुम्बकम् इति`, often without daṇḍa, quote marks or line break.
2. **External sandhi across frame and verse.** `यथाह — अष्टौ` is printed `यथाहाष्टौ`; `कुटुम्बकम् इति` is printed `कुटुम्बकमिति`. The verse boundary lies *inside* an orthographic word.
3. **Ekādeśa at pāda junctions** (rare but real). Vowel coalescence across pāda 1|2 or 3|4 can leave a 15-syllable surface hemistich.
4. **Epic/Purāṇic licence (ārṣa prayoga).** Most quotations are anuṣṭubh from smṛti and purāṇa, which admit vipulās freely and, occasionally, hypermetric odd pādas and lightness before `pr/hr/br`.
5. **Split quotations and pratīkas.** A half is quoted, glossed (`उत्तरार्धं तु —`), then the other half; or only the first words are cited followed by `इत्यादि`.

**Working hypotheses to measure, not assume:** that anuṣṭubh dominates and that most quotations carry a frame. Quantify per work before using as priors (section 9).

---

## 2. Goals and non-goals

### Goals
- **G1** Locate verses with no reliance on daṇḍas, line breaks or quotation marks, while using them as weighted evidence.
- **G2** Exact *surface* boundaries where attested; otherwise explicitly typed phonological/sandhi-fused boundaries (including lost characters) with auditable anchors, plus consistent treatment across lines, paragraphs and pages.
- **G3** Ultra-low prose false-positive rate. Primary gate: **false positives per 1,000 adjudicated prose words**, complemented by span overlap/over-extension and detected-verse coverage metrics.
- **G4** Half-verses, three-pāda spans, single pādas, split halves and pratīkas — when evidence supports them.
- **G5** Pāda sub-segmentation with evidence-backed boundaries.
- **G6** Graceful degradation over tiers; isolate unprocessable regions rather than hallucinate.
- **G7** Granthanidhi-ready citation graph: `{raw, primary_authority, via_digest}` plus reference links, separately recording textual similarity and bibliographic attribution certainty.

### Non-goals
- Exhaustive classification of rare *daṇḍaka* / *viṣama-vṛtta* metres (the registry is extensible by table).
- Vedic metre recognition, classification or evaluation.
- Whole-text sandhi splitting or morphology.
- OCR correction.
- Any LLM call inside `padya/`.

---

## 3. Architecture

```
cleaned_devanagari/<file>      cleaned_records/<file>.jsonl      manifest.json
          │                              │                            │
          ▼                              ▼                            ▼
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │ 1  Loader        text + records + manifest → Document (immutable, hashed)    │
 │ 2  Scan view     delimiter tokens, verse-number tokens, excluded spans,      │
 │                  language runs, boundary flags, SLP1 analysis view + spans   │
 │ 3  Scanner       Akshara stream: weight L/G/?, mātrā, fusion traits, offsets │
 │ 4  Candidates    Tier A (anchored) · Tier B (windowed) · retrieval-assisted  │
 │ 5  Gate          bitmask pre-filter · anuṣṭubh grammar · banded aligner ·    │
 │                  mātrā DP · tiered edit budget                               │
 │ 6  Evidence      prose LMs · citation frames · known-verse index · cues      │
 │ 7  Scorer        log-odds S(c) against the prose null                        │
 │ 8  Decoder       semi-Markov Viterbi + log-space forward–backward            │
 │ 9  Annotator     pāda spans, fused-closer trim, attribution, OCR events      │
 │ 10 Writer        verses.jsonl · regions.jsonl · candidates.jsonl ·           │
 │                  report.json · review.html · VTF export                      │
 └──────────────────────────────────────────────────────────────────────────────┘
```

**Architectural invariants.** Each stage is a pure, typed function `run(input, config) -> output` over frozen dataclasses (`slots=True, frozen=True`). No module-level mutable state; caches are explicit and keyed by content hash + registry version. Each stage is unit-testable in isolation.

---

## 4. Stages 1–3: loader, scan view, akṣara scanner

### 4.1 Document model (`padya/loader.py`)

```python
TierType = Literal["T", "P", "R", "unspecified"]

@dataclass(slots=True, frozen=True)
class Span:            # code-point offsets into Document.text, end exclusive
    start: int; end: int

@dataclass(slots=True, frozen=True)
class CleanerRecord:   # kind in {"flag", "vedic", "verse_number"} today; adapter tolerates new kinds
    kind: str; start: int; end: int; payload: Mapping[str, JsonScalarOrFrozen]  # deeply immutable

@dataclass(slots=True, frozen=True)
class Document:
    doc_id: str
    path: str
    tier: TierType
    noise_per_1000: float | None     # from cleaned_report.json if present
    text: str                        # exactly as on disk
    text_sha256: str
    cleaner_version: str
    records: tuple[CleanerRecord, ...]  # copied and recursively frozen on load
    paragraphs: tuple[Span, ...]     # \n\n blocks
    lines: tuple[Span, ...]
```

Offsets are Python code-point indices, 0-based, end-exclusive. `manifest.json: offsets_refer_to` is **checked** at load; mismatch is a hard error. Consumers needing UTF-8 byte or UTF-16 offsets get an explicit converted view (`OFF-6`).

### 4.2 Scan view (`padya/scanview.py`) — overlays, never edits

| id | layer | rule |
|---|---|---|
| **SV-1** | delimiters | `।` → D1, `॥` → D2 with confidence T 1.0 / P 0.95 / R 0.90. Tier R only: isolated `l`, `I`, `1`, `!`, `\|` flanked by Devanagari or space → D1 at 0.60; `ll`, `II`, `11`, `\|\|` → D2 at 0.60. Never promoted in tier T. |
| **SV-2** | line starts | LS token, confidence T 0.80 / P 0.0 / R 0.0. |
| **SV-3** | paragraph starts | PS token, confidence T 0.90 / P 0.50 / R 0.30. |
| **SV-4** | verse numbers | from `verse_number` records → `VerseNumToken(offset, number, conf)`, T 1.0 / P 0.75 / R 0.70. Digits are excluded from the syllable stream. **Fallback (v7):** the cleaner records a number only when a daṇḍa stands on both sides; a Devanagari/ASCII numeral run adjacent to a single D1/D2 or at a line end (`…॥ १२` / `१२॥`) is tokenised by the scan view itself as a `VerseNumToken` at 0.6 × the tier confidence, and all numerals are always excluded from the syllable stream. |
| **SV-5** | excluded spans | from cleaner-provided `vedic` records only. **Do not blindly bridge two accented records across ≤ 2 unaccented words**: merge only when a shared cleaner run-id/explicit block span proves continuity. Otherwise retain disjoint exclusions and leave intervening text eligible. No Vedic metre inference/name. |
| **SV-6** | language runs | character 5-gram classifier → `sa / hi / mr / other` per paragraph, then split into runs at quote marks and before `इति`. Non-`sa` runs get a negative prior (*initial* −3.0 on candidates starting inside them) rather than hard exclusion; quoted Devanagari inside a `hi`/`mr` run is re-labelled `sa`. Classifier **off** until M4 and until mixed-language recall is measured (NEG-8). |
| **SV-7** | word boundaries | space → `word_start`; hyphen between letters → `soft_start`; avagraha sets `soft_start` on the following syllable (pūrvarūpa evidence). |
| **SV-8** | flags | `flag` records projected onto akṣaras. Classes affecting vowel identity or consonant closure (`orphan_matra`, `virama_then_matra`, `double_virama`, `latin_in_word`) give weight `?` with the reason recorded; purely typographic flags (`long_unspaced_run`) do not change weight. |
| **SV-9** | analysis view | SLP1 produced from `Document.text` with **many-to-many origin intervals** for each output phonological token, plus tombstones for omitted punctuation. Never assume that one SLP1 character maps to one Devanagari code point. The cleaner's tables must first pass compatibility tests; SLP1 is disposable, never the canonical text. See OFF-* and §4.4. |
| **SV-10** | apparatus and page breaks | if the cleaner ever emits `footnote` / `page_break` records: footnotes are scanned separately and never bridged with main text; page breaks are zero-cost bridge tokens so a verse may continue across them. |

### 4.3 Akṣara scanner (`padya/scanner.py`)

```python
@dataclass(slots=True, frozen=True)
class Akshara:
    idx: int
    src: Span                        # into Document.text
    slp1: str                        # onset + nucleus + coda
    vowel: str                       # a i u f x A I U F X e E o O
    weight: Literal["L", "G", "?"]   # surface phonological weight
    matra: int | None                # 1, 2 or None when unknown (never zero)
    word_start: bool; soft_start: bool; line_start: bool; para_start: bool
    delim_before: str | None; delim_conf: float
    verse_num_before: str | None
    fusible_vowel: bool              # SC-10: optional hypothesis, not proof
    yan_onset: bool                  # SC-10
    intrinsic_heavy: bool            # long vowel / unambiguous coda
    contextual_cluster: tuple[int, ...]  # next consonant-token ids, not already charged as G
    possible_parses: tuple[str, ...] # analysis alternatives for uncertain marks
    lenient_cluster: bool            # SC-11
    trailing_iti: bool               # SC-12
    excluded: bool                   # SV-5
    flags: frozenset[str]
```

| id | rule |
|---|---|
| **SC-0** | One vowel nucleus = one syllable. `a i u f x` → L (1 mātrā); `A I U F X e E o O` → G (2 mātrās). Pluta mark forces G. |
| **SC-1** | **Default classical scanning:** written anusvāra makes the preceding syllable G regardless of the following vowel. The v3 rule that universally shifts `M` into a following onset before a vowel is **withdrawn**. An alternative phonological resolution is allowed only as an explicit, corpus-verified variant, default off; preserve the original sign. |
| **SC-2** | Anusvāra before a consonant, D1/D2 or end of text → G (explicit subset of SC-1); do not double-charge this condition. |
| **SC-3** | Candrabindu indicates nasalisation; **do not automatically treat it as interchangeable with anusvāra in every context**. Record a nasalisation trait; choose G only when verified by phonology/rules for that input, otherwise `?` with a traceable alternative. Add positive and negative fixtures. |
| **SC-4** | Visarga `H`, jihvāmūlīya, upadhmānīya, ardhavisarga → G. |
| **SC-5** | Short vowel followed by ≥ 2 consonantal phonemes before the next vowel → G (subject to pauses and parse). Compute from **tokenised Sanskrit phonemes**, not raw glyph count. In SLP1, digraph confusion is avoidable only if a validated transliterator produced canonical single-symbol aspirates. At proposed pāda/verse boundaries recompute **context-sensitive** closure; do not let following prose silently change a verse's last-syllable treatment. |
| **SC-6** | Pāda-final syllable is anceps (X) **inside the metrical hypothesis only**; the scanner records true surface weight (AN-4). |
| **SC-7** | Akṣara with an uncertain phonological flag has possible {L,G} with explicit 0.5 cost per uncertain matched slot (*initial*). `mātrā=unknown` is **not zero mātrās**; branch or abstain in jāti analysis. |
| **SC-8** | Explicit D1/D2 breaks and validated sentence/paragraph pauses may block consonant lookahead; unconfirmed PS, spaces, hyphens, quotes, dashes and line breaks only provide weighted possibilities. In noisy OCR a `|` may be punctuation or a real character; **branch** rather than coercing one parse. No pause interpretation may destroy the surface map. |
| **SC-9** | Avagraha is silent: zero syllables, zero consonants; sets `soft_start` on the next syllable. |
| **SC-10** *(opt-in, default off)* | Junctional ekādeśa may license **two underlying vowel slots for one observed nucleus** at a proposed pāda boundary, but never by pretending the text contains a new code point. Model one-to-many phonological alignment with `shared_surface` boundary and event cost. Support only explicitly enumerated sandhi transformations verified in fixtures. Do not infer this merely because a vowel is long; disable by default pending corpus evidence. |
| **SC-11** *(opt-in, default off, **ASK**)* | `lenient_cluster` when a syllable is G solely because of a following stop/sibilant + liquid (`pr hr br kr tr dr gr Sr sr kl pl hl`). In the anuṣṭubh gate only, such a syllable may match L at cost 0.20 (*initial*), and only when a frame or retrieval hit supports the candidate. |
| **SC-12** | Fused quotative `iti / ityādi / ityādinā`: search for **typed surface analyses** of forms such as `kuwumbakamiti`, `varjayetIti`, `smftiriti`, `cAhuriti`; keep all plausible parses when the underlying word boundary has disappeared. A literal offset before `iti` is valid only where `iti` survives as a contiguous grapheme sequence. In visarga transformations or vowel coalescence, emit `boundary_resolution=shared_surface` or `unresolved`, not an invented offset. F-5 applies the same policy to fused openers. Frames alone must not force a sandhi split. |

**M1 acceptance.** On adjudicated held-out scanner gold: ≥ 99.5% L/G token agreement, ≥ 99.9% syllable-count agreement, and **100% offset-projection validity** (`Document.text[a.src.start:a.src.end]` reproduces the akṣara's characters).

---

### 4.4 Boundary semantics and phonological parse lattice (OFF-7…OFF-12, PH-1…PH-7) — **normative v4**

The fundamental objects are **(a) observed source characters, (b) analysis phonemes/metrical syllables, and (c) optional reconstructions**. They are not interchangeable. Example: the intended sequence `यथाह + अष्टौ` may appear in the surface as `यथाहाष्टौ`; the initial अ of the quoted verse is absorbed by sandhi. A literal full-verse source slice containing the missing अ is mathematically impossible. Similarly, `स्मृतिः + इति` may surface as `स्मृतिरिति`, without an exact substring spelling the underlying visarga.

```python
BoundaryResolution = Literal[
    "exact_between_codepoints",  # unambiguous source offset
    "inside_grapheme",          # source glyph sequence cannot be split safely
    "shared_surface",           # two underlying units share surface material
    "unresolved",               # competing plausible phonological parses
]

@dataclass(slots=True, frozen=True)
class BoundaryAnchor:
    resolution: BoundaryResolution
    offset: int | None             # only when an exact safe boundary exists
    covering_src: Span | None      # observed grapheme or token in other cases
    analysis_left: int | None      # end slot in analysis-token space
    analysis_right: int | None     # start slot in analysis-token space
    transformation: str | None     # e.g. "ā+a→ā", "ḥ+i→ri"
    evidence_ids: tuple[str, ...]

@dataclass(slots=True, frozen=True)
class SurfaceAndMetricalSpan:
    observed_cover: Span           # always a valid non-empty substring
    start_boundary: BoundaryAnchor
    end_boundary: BoundaryAnchor
    phonological_slots: tuple[int, ...]
    reconstruction: str | None     # OPTIONAL, never used as observed text
```

- **OFF-7** `observed_cover` is an exact source slice; `reconstruction` may contain underlying letters not present in that slice, and must be labelled hypothesis rather than source quotation.
- **OFF-8** A fused boundary is measured against a **human-labelled relation** (`exact/shared/unresolved`), not penalised as a fabricated exact-offset failure. Store both *surface-cover IoU* and *metrical-slot boundary* correctness.
- **OFF-9** A character and metrical-token may map many-to-many; use alignment **edges**, not only parallel offsets. Empty-side edges record elision/zero output; no empty codepoint is synthesized.
- **OFF-10** All emitted exact offsets must be Unicode grapheme-safe; char slicing must be valid at `start`/`end`. At shared boundaries pāda surface covers may overlap, but emitted verse **regions remain one non-overlapping surface partition** by choosing a documented attachment policy.
- **OFF-11** `Document.text` remains byte-for-byte/character-for-character fixed. A transliteration round trip is not necessarily the original Unicode spelling; only origin-preserving projection is required.
- **OFF-12** A boundary hypothesis includes `surface_parse_id` and a `source_alignment_trace`, reproducible under registry and cleaner version hashes.
- **PH-1** Use **deterministic single scan** for well-formed T input. Only branch locally for ambiguous pauses, OCR vowel signs, avagraha, SC-10 and SC-12; never enumerate a full-document phoneme lattice exponentially.
- **PH-2** Apply ambiguous-parse beam caps *per window*; if pruning could omit plausible parses, tag `search_incomplete` and abstain instead of making a high-confidence claim.
- **PH-3** The gate computes contextual L/G using proposed pāda boundaries. Intrinsic vowel length cannot change. Candidate-specific cluster/pausal closure and pādānta anceps are explicit features, not mutations of `Akshara.weight`.
- **PH-4** Surface and phonological offsets form separate coordinate systems (`src_cp`, `analysis_slot`); source-region partition is always in `src_cp`.
- **PH-5** When a fused opener/closer cannot be divided orthographically, report `observed_cover`, `frame_overlap`, `boundary_resolution` and optional underlying reading; never silently trim or delete shared surface code points.
- **PH-6** For a word whose surface can plausibly be prose OR an embedded quotation, preserve both hypotheses until score/decoder; the word-break cue is **weak**, not a truth label.
- **PH-7** `Akshara.weight` is documented as the **default surface parse** only. Alternative parsed forms carry a local `ScansionPath` with weights, slots, alignment and edit events; all downstream modules consume one complete path consistently.

**Acceptance:** round-trip projected slices, safe grapheme boundaries, monotone analysis-token order, a finite local parse cap, and a **negative** test where the verse's first vowel has been completely absorbed (`यथाहाष्टौ`). Do not claim an exact observed substring matching an underlying reconstructed verse.


## 5. Stage 5: metrical gate (`padya/metres/`)

### 5.1 Representation and matching

A metre = ordered pāda templates over `{L, G, X}` with optional yati positions, or (anuṣṭubh) a constraint grammar, or (jāti) a mātrā grammar. `match(slice, template, budget) -> (ok, cost, alignment, edits)`.

**Two-phase matcher.**
1. *Bit-parallel **necessary-condition pre-filter*** — encode the L/G hypotheses as masks. Each verified fixed-pāda template ≤ 32 syllables compiles to `req_L` and `req_G` (X ignored). Hamming `popcount` is a lower bound **only for a fixed-length, unambiguous parse**. A zero Hamming mismatch **does not authorize acceptance**: `?`, any parse alternative, contextual SC-5, yati, variant constraints, and cross-pāda consistency still need the final grammar. Even an exact T hit must pass the complete metrical gate. Never give `?` a free exact match; charge its declared uncertainty cost.
2. *Banded alignment* (tiers P/R; SC-10 only if on) — Wagner–Fischer with band ≥ permitted insertions/deletions; reject only when an **admissible lower bound** exceeds budget. Substitute 1.0, insert/delete 1.0, `?` 0.5, verified fusion/leniency by their configured costs. Record uncertainty even on an otherwise exact mask match. Test that the fast gate and a slow full-search oracle make identical accept/reject decisions for bounded short inputs.

Every edit is an event `{type, syllable_idx, src_anchor, template_pos, reason}`; insertions have an anchor *between* code points, never a fabricated character range (OCR-2).

### 5.2 Anuṣṭubh (śloka) — `anustubh.py`

Four pādas × 8 syllables (32), or 30–31 surface syllables only when SC-10 is enabled and used.

| id | rule |
|---|---|
| **AN-1** | Even pādas (2, 4): syllables 5–7 = `L G L`; syllable 8 anceps; syllables 2–4 ≠ `LLL`, `LLG`; under profile `classical_strict` also ≠ `GLG`. |
| **AN-2** | Odd pādas (1, 3), *pathyā*: 5–7 = `L G G`; 8 anceps; 2–4 ≠ `LLL`, `LLG`. |
| **AN-3** | Non-pathyā odd pādas are **named variants** with pre-cadence and caesura constraints. The 5–7 triple alone never admits one. Variants are *blocked by default* until verified positive/negative fixtures and profile-specific tests pass (`data/metres/verification.tsv`). |
| **AN-4** | Surface weight is stored separately from the metrical allowance (pāda-final anceps). |
| **AN-5** | A 32-syllable free candidate (no delimiter/frame) must pass both hemistichs; a single 8-syllable window cannot win on metre alone (NEG-3). |
| **AN-6** | A 16-syllable half may be pādas 1–2 or 3–4; they are isomorphic, so `half_position` is reported only when a verse number, D2 or retrieval hit decides it. |
| **AN-7** | Three-pāda and single-pāda quotations require a frame, verse number or verified retrieval hit. |
| **AN-8** | Explore all admissible pāda segmentations (potentially more than four under OCR/fusion), using length/edit lower bounds. Word boundaries are weighted evidence, not a prerequisite; if the boundary is fused, use OFF-7…OFF-12. |
| **AN-9** *(opt-in, default off)* | Hypothesised hypermetric/resolved odd pāda. Treat as a separate metre-profile analysis with verified examples, not as a generic 9-syllable permission; prior −3.0 only after fitting. |

| variant | syllables 5–7 | syllable 4 | additional constraint | log-prior (*initial*) | default |
|---|---|---|---|---|---|
| pathyā | `L G G` | any | 2–4 ∉ {LLL, LLG} | 0.00 | on |
| na-vipulā | `L L L` | G | 2–4 ∈ {GGG, LGG, GLG} | −2.50 | on after fixtures |
| bha-vipulā | `G L L` | G | canonical 2–4 `GLG` (ra-bha); exceptional `GGG` (ma-bha) **requires verified caesura after syllable 4** | −2.80 | **blocked until verified** |
| ma-vipulā | `G G G` | G | canonical 2–4 `GLG` (ra-ma); **caesura after syllable 5** required for strict profile | −2.80 | **blocked until verified** |
| ra-vipulā | `G L G` | G | syllables 2–4 not `LL*`, with **caesura after syllable 4** in strict profile | −3.50 | **blocked until verified** |
| ta-vipulā (epic) | `G G L` | G | only with frame or retrieval | −4.20 | off |

`verification.tsv` columns: `metre, variant, pattern/constraint, primary_reference, second_reference, positive_examples, negative_examples, status(enabled|blocked|needs_verification)`. Sources: Vṛttaratnākara; Ollett's anuṣṭubh summary (prakrit.info/vrddhi/meter/anustubh); the `chanda` library's anuṣṭubh regexes as a **test-time** oracle only (AGPL).

### 5.3 Sama-vṛtta and ardhasama-vṛtta registry (`config/metres.yaml`)

Seed inventory. Every entry starts `needs_verification` until length, **machine-expanded gaṇa formula**, pattern, yati, one positive and one adversarial negative are checked against a primary prosody source plus an independent implementation. A mismatch (including Hariṇī above) → `blocked`, not a valid registry entry. Final syllable can be X (anceps) only where philologically justified; preserve surface L/G separately. The compiler must fail if `len(pattern) != n` or `expand(gaṇa_formula) != pattern`, except a declared, source-verified override with a versioned rationale.

| metre | n | pattern | yati | gaṇa formula |
|---|---|---|---|---|
| Pramāṇikā | 8 | `LGLGLGLG` | – | ja ra la ga |
| Vidyunmālā | 8 | `GGGGGGGG` | 4 | ma ma ga ga |
| Bhujagaśiśubhṛtā | 9 | `LLLLLLGGG` | 7 | na na ma |
| Indravajrā | 11 | `GGLGGLLGLGG` | – | ta ta ja ga ga |
| Upendravajrā | 11 | `LGLGGLLGLGG` | – | ja ta ja ga ga |
| Upajāti | 11 | any per-pāda mix of the two above | – | |
| Dodhaka | 11 | `GLLGLLGLLGG` | – | bha bha bha ga ga |
| Śālinī | 11 | `GGGGGLGGLGG` | 4 | ma ta ta ga ga |
| Vātormī | 11 | `GGGGLLGGLGG` | 4 | ma bha ta ga ga |
| Bhramaravilasita | 11 | `GGGGLLLLLLG` | 4 | ma bha na la ga |
| Rathoddhatā | 11 | `GLGLLLGLGLG` | – | ra na ra la ga |
| Svāgatā | 11 | `GLGLLLGLLGG` | – | ra na bha ga ga |
| Vaṃśastha | 12 | `LGLGGLLGLGLG` | – | ja ta ja ra |
| Indravaṃśā | 12 | `GGLGGLLGLGLG` | – | ta ta ja ra |
| Upajāti-12 | 12 | per-pāda mix of Vaṃśastha / Indravaṃśā | – | |
| Drutavilambita | 12 | `LLLGLLGLLGLG` | – | na bha bha ra |
| Bhujaṅgaprayāta | 12 | `LGGLGGLGGLGG` | – | ya ya ya ya |
| Toṭaka | 12 | `LLGLLGLLGLLG` | – | sa sa sa sa |
| Sragviṇī | 12 | `GLGGLGGLGGLG` | – | ra ra ra ra |
| Praharṣiṇī | 13 | `GGGLLLLGLGLGG` | 3 | ma na ja ra ga |
| Rucirā | 13 | `LGLGLLLLGLGLG` | 4 | ja bha sa ja ga |
| Mattamayūra | 13 | `GGGGGLLGGLLGG` | 4 | ma ta ya sa ga — *v2.0 draft had a different string; verify* |
| Vasantatilakā | 14 | `GGLGLLLGLLGLGG` | – | ta bha ja ja ga ga |
| Mālinī | 15 | `LLLLLLGGGLGGLGG` | 8 | na na ma ya ya |
| Pañcacāmara | 16 | `LGLGLGLGLGLGLGLG` | – | ja ra ja ra ja ga |
| Śikhariṇī | 17 | `LGGGGGLLLLLGGLLLG` | 6 | ya ma na sa bha la ga |
| Mandākrāntā | 17 | `GGGGLLLLLGGLGGLGG` | 4, 10 | ma bha na ta ta ga ga |
| Hariṇī | 17 | `LLLLLGGGGGLGLLGLG` | 6, 10 | na sa ma ra sa la ga — formula-consistent and matches the traditional yati 6/4/7; `needs_verification` (v3 had a mis-expanded string) |
| Pṛthvī | 17 | `LGLLLGLGLLLGLGGLG` | 8 | ja sa ja sa ya la ga |
| Śārdūlavikrīḍita | 19 | `GGGLLGLGLLLGGGLGGLG` | 12 | ma sa ja sa ta ta ga |
| Sragdharā | 21 | `GGGGLGGLLLLLLGGLGGLGG` | 7, 14 | ma ra bha na ya ya ya |

Note on Bhramaravilasita: the v2.0 draft had `GGGLLLLLLGG`; *ma bha na la ga* gives `GGG GLL LLL L G` = `GGGGLLLLLLG`. Verify both.

Ardhasama-vṛtta:

| metre | odd pāda | even pāda |
|---|---|---|
| Viyoginī (Sundarī) | `LLGLLGLGLG` (10) | `LLGGLLGLGLG` (11) |
| Puṣpitāgrā | `LLLLLLGLGLGG` (12) | `LLLLGLLGLGLGG` (13) |

Yati is evidence (C-4), never a hard constraint; do not assume a yati coincides with an orthographic space.

### 5.4 Mātrā metres (`jati.py`) — feature-gated after M3

| id | rule |
|---|---|
| **JA-1** | Āryā: first half 30 mātrās = seven 4-mātrā groups (`GG`, `GLL`, `LLG`, `LLLL`, `LGL`) plus final G; second half 27 replaces its sixth group with one L. Quarter view 12+18 / 12+15 is a consequence, **not an independent recognition rule**. |
| **JA-2** | Odd gaṇas (1,3,5,7) exclude syncopated `LGL`. Sixth group of the first half uses the syncopated form in the standard profile; exceptional `LLLL` needs a separately verified caesura/variant rule, disabled until fixtures. Cross-check against a primary source; metre names and Mātrā subtleties are versioned. |
| **JA-3** | Gīti 30+30, Upagīti 27+27, Udgīti 27+30. Keep separate gold and separate metrics; no aggregate "jāti accuracy". |
| **JA-4** | A mātrā sum alone never proves poetry. Tier B Āryā requires a plausible half-boundary (exact, soft, or OFF-7 fusion) **and** an independent cue (delimiter/frame/retrieval), then the full gaṇa grammar. Keep off until held-out prose false-positive evaluation passes. |
| **JA-5** | Vaitālīya: odd pāda = 6 mātrās + `GLGLG` (14); even = 8 mātrās + `GLGLG` (16). Aupacchandasika: cadence `GLGLGG` (16/18). Both opt-in. |
| **JA-6** | Mātrā templates are matched by a small DP over gaṇa boundaries, producing the same edit-event structure as 5.1. |

### 5.5 Edit budget by tier

| tier | cleaner noise (flags / 1,000 akṣaras) | budget per 32 syllables | indels per 32 | per-pāda cap |
|---|---|---|---|---|
| T | any | 0 (+ SC-10/11 fractional costs if enabled) | 0 | 0 |
| P | < 5 | 1.0 | 0 | 1 |
| P | ≥ 5 | 2.0 | 1 | 1 |
| R | < 5 | 1.5 | 1 | 1 |
| R | 5–20 | 2.5 | 2 | 1 |
| R | > 20 | region `unprocessable`; no candidates | – | – |

`B(n) = configured_budget32 × n / 32` **without integer rounding of fractional budgets**; enforce separate integer indel count and per-pāda caps. Noise is computed **per reviewable locality** (page or a sufficiently long paragraph/window, with smoothed estimates when samples are small), using document-level noise as fallback. A highly corrupted page becomes `unprocessable` without suppressing clean pages in the same book. All edit/`?` costs are recorded. Tier T remains strict; optional phonological licences are *not* OCR edits.

### 5.6 Excluded spans

Classical gate does not run inside SV-5 spans. Emit `region = excluded, source_tag = vedic`, with per-line syllable counts for the reviewer only. No metre name, no "Vedic" metric. If the owner later wants Vedic templates, that is a new milestone, not a flag.

---

## 6. Stage 4: candidate generation (`padya/candidates.py`)

A candidate: a **surface-cover plus phonological-slot path**, metre, variant, `k ∈ {1,2,3,4}` pādas, origin ∈ `{anchored, free, retrieval}`. The shorthand akṣara slice `[s, e)` is valid only for unambiguous one-to-one paths; fused boundaries are governed by OFF-7…12 and §41.

### 6.1 Tier A — anchored (high precision, O(N))

| id | rule |
|---|---|
| **A1** | Chunk between two structural tokens (D1, D2, PS, LS in tier T, document edges) whose syllable count = `k × L_m ± B(n)` (or 30/31 for anuṣṭubh with SC-10 on) and passes the gate. Exact-extent match is the strongest single evidence. |
| **A2** | A1 after stripping a leading opener and/or trailing closer (section 7.2), including fused `-iti` (SC-12) and fused openers (F-5). The stripped frame becomes structured evidence. |
| **A3** | Merge adjacent A1/A2 sub-spans of the same metre (or Upajāti/ardhasama pairs) separated by D1, LS or a space: 16+16, 8+8+8+8, 8+24 → 32. Inherits the minimum internal delimiter confidence. |
| **A4** | Chunk longer than one verse (> 36 syllables): windows anchored at its left edge (prose → verse) or right edge (verse → prose) get a partial-extent bonus; the interior goes to Tier B. |
| **A5** | Split ardhaśloka: if two half-verse spans separated by ≤ 8 words with a verified bridging formula, propose a **paired-span macro candidate** with two verse components and an explicit intervening-prose gap. The optional shared bonus applies **once to the macro**, never twice to the ordinary component arcs. Decoder implementation and scoring described in DP-1…DP-7; without macro support, set bonus=0 and output an unscored review relation. |
| **A6** | Pratīka: 4–11 syllables immediately after an opener/opening quote and immediately before `इत्यादि` / `इत्यादिना` / `इत्युपक्रम्य`. Bypasses the length gate; routed to retrieval (R-3). Without a retrieval hit it is emitted as `pratika_unresolved` in the review queue, never as a verse. |

### 6.2 Tier B — windowed (recall)

| id | rule |
|---|---|
| **B1** | Starts at `word_start`, `soft_start`, **typed fused-opener anchor**, or independently verified retrieval alignment; bounded inside-word fallback for flagged collapsed OCR runs. Never start at an arbitrary phoneme simply because a high-scoring metre can be fitted. Strong Tier A interiors can be deferred but must be revisited in conflicts (OPS-3). For an unflagged but sandhied orthographic word, a verified F-5 cue may propose a **bounded local set** of internal phonological start anchors; generic full-document interior starts are forbidden by default and measured as an ablation. |
| **B2** | For each start and enabled metre, `k ∈ {1,2,3,4}` pādas, ± `B(n)` syllables in tiers P/R, −1 per enabled SC-10 junction, and an alternative end just before a `trailing_iti`. |
| **B3** | Crossing penalties (*initial*): internal D2 −3.0 × conf; internal D1 not at a pāda/half boundary −1.5 × conf; PS −1.5 (T) / −0.3 (P, R); page break 0. |
| **B4** | Pruning must be admissible: when the per-pāda cap is 0, reject on first-pāda failure; otherwise compute a lower bound (Hamming of best alignment within the band) and reject only if it exceeds the remaining budget. |
| **B5** | One canonical candidate per `(s, e, metre_id, variant_id, parse)`; alternate evidence is aggregated **by independent evidence id**, never stacked twice or duplicated as a separate arc (OPS-4). |

### 6.3 Retrieval-assisted (origin `retrieval`)

| id | rule |
|---|---|
| **R-A** | A verified reference may propose a span/pratīka, but confirmation is against the **observed surface** and an alignment trace. A genuine textual variant can differ from the reference; report variant positions instead of importing missing syllables/words. Reference-initiated discovery must still pass a relevance/context test, so stock substrings cannot create verses in arbitrary prose. |

Complexity note: Tier B is `O(A × M × K × B)` for A eligible starts, M enabled metres, K ≤ 4, B bounded alignments. Measure worst-case A and candidate density (OPS-6); do not assert linearity.

---

## 7. Stage 6: evidence (`padya/evidence/`)

### 7.1 Prose background models (`prose_model.py`)

Two generative models trained on adjudicated gadya (section 9.3):

- `P_prose^LG` — 8-gram interpolated Kneser-Ney over the binary L/G stream.
- `P_prose^char` — 5-gram Kneser-Ney over SLP1 with spaces; contrasted with `P_verse^char` trained on gold verses (captures verse endings vs śāstra prose endings like `-त्वात्`, `-चेत्`, `-इति वाच्यम्`).

```
LLR_model(c) = [ log P(LG_c | m) − log P_prose^LG(LG_c) ]
             + α_lex · [ log P_verse^char(c) − log P_prose^char(c) ]        α_lex = 0.25 (initial)
```

**Discourse cue** (*initial* −2.5, soft and ablated): possible prose markers (`इति चेन्न`, `अत्रोच्यते`, `तन्न`, `ननु`, `वाच्यम्`, `व्याख्येयम्`, `प्रकृतम्`, `इत्यर्थः`, `इति भावः`). These may occur in real verse; never use as an absolute exclusion, avoid lexical double-counting, and publish per-cue false-negative analyses. Table in `config/frames.yaml`.

Likelihoods are natural logs, with explicitly documented length normalisation; edit costs are charged **once** (in λ_edit, not again in `log P(LG|m)`) (PR-3). The combined scorer is an **empirical energy/discriminant** because its hand-tuned frame weights and metre-relative penalties are not independently measured generative log-probabilities. Forward–backward gives lattice *model marginals*, not automatically real-world correctness probabilities.

### 7.2 Citation frames (`frames.py`, `config/frames.yaml`)

Window: ≤ 5 words before `c.start`, ≤ 3 words after `c.end`.

| id | opener class | examples |
|---|---|---|
| **F-1** | single authority | `<Authority-Nom> (आह|उवाच|अब्रवीत्)?`; `(तथा च|अत्र|यदाह|यथाह|उक्तं च|तदुक्तम्) <Authority>`; `तथा च मनुः`, `यथाह याज्ञवल्क्यः`, `कात्यायनोऽपि`, `व्यासः`, `स्मृत्यन्तरे`, `पुराणान्तरे`, `भारते`, `गीतासु` |
| **F-2** | multi-hop (digest + primary) | `<Digest-Loc> <Primary>`: `हेमाद्रौ भविष्ये`, `माधवीये पराशरः`, `मिताक्षरायां यमः`, `रत्नाकरे बृहस्पतिः`, `स्मृतिचन्द्रिकायां देवलः`, `कौस्तुभे स्कान्दे`, `मदनरत्ने बौधायनः` → `{via_digest, primary_authority}` |
| **F-3** | anonymous / kārikā | `अत्र श्लोकाः`, `तत्र श्लोकः`, `संग्रहश्लोकः`, `कारिका च`, `वृद्धवाक्यम्`, `अत्रोदाहरन्ति`, `यथोक्तम्`, `स्मृतिश्च` → `quotation_type` hint |
| **F-4** | typographic | a nominal in `-ः`, `-ौ`, `-े`, `-षु` followed by `—`, `:-`, `-`, `‘` or `“` |
| **F-5** | fused opener | opener whose final vowel has coalesced with the verse's first syllable (`यथाहाष्टौ`, `उक्तं चैवं`): matcher table of opener stems + sandhi outcomes; the split offset is recorded like SC-12 |

| id | closer class | examples |
|---|---|---|
| **F-6** | quotative | `इति`, `इति च`, fused `-इति` (SC-12) |
| **F-7** | ellipsis | `इत्यादि`, `इत्यादिना`, `इत्युपक्रम्य`, `इत्यन्तेन`, `इत्यादिग्रन्थः` |
| **F-8** | causal | `इति वचनात्`, `इति स्मृतेः`, `इति स्मरणात्`, `इति निषेधात्`, `इति श्रुतेः`, `इत्युक्तेः`, `इति दर्शनात्` |
| **F-9** | structural | `’`, `”`, a VerseNumToken |

Scoring (*initial*): opener within 3 words +2.0 (+2.8 if F-4 punctuation present); closer within 2 words or fused +2.0; both +1.2 synergy; F-7 ellipsis lifts `log P(k | m)` for k ∈ {1,2,3} to 0.0. An opener alone never proves a quotation (NEG-4, GOLD-3).

### 7.3 Known-verse index (`retrieval.py`, `tools/build_reference_index.py`)

| id | rule |
|---|---|
| **R-1** | Two indexes: a strict normalised SLP1 stream (spaces/punctuation removed, vowel length retained) and a **fuzzy retrieval-only** skeleton (nasal variants, optional geminate/final alternations). Transformations are one-way search keys, never trusted as the alignment text; store provenance and collision rate. |
| **R-2** | Stage 1: indexed 10-character strict shingles + 5-consonant *fuzzy* fingerprints propose top-K references; use IDF and minimum distinct content. Stage 2: **semi-global, coverage-aware alignment** on the observed SLP1 span and reference (local Smith–Waterman alone can align a tiny common substring and overstate a full hit). Report aligned-character coverage of **both** strings, longest exact run, edit ratio and mapping uncertainty. Thresholds (shingle %, edit %, top-K) are train/dev parameters. Partial/pratīka hits have separate stricter distinctiveness and confirmation gates. |
| **R-3** | Evidence: +4.5 (*initial*), conditional on distinctive match and surface alignment. Reference pāda boundaries are **hypotheses**; project them only when the local text supports the mapping and OFF-7 flags any unresolvable fusion. Never override a contradictory gate silently. Pratīkas (A6) are resolved only here. |
| **R-4** | Textual similarity and source attribution are reported separately (PR-2): a quotation can be found without being attributed, and attributed only above a stricter threshold. |
| **R-5** | The index is optional; absent → contributes 0, warns once. Reference metadata: `source_work, edition, locator, rights, text, offsets`. Evaluation partitions govern which references may be used (GOLD-6). |

### 7.4 Boundary cues (`cues.py`)

| id | condition | log-odds (*initial*) |
|---|---|---|
| **C-1** | starts on `word_start` | 0.0 (required for Tier B; −1.0 if only `soft_start`; −2.5 if inside a collapsed word, flagged `word_boundary_suspect`) |
| **C-2** | ends on `word_start` or before fused `-iti` | +0.6 (−2.0 if mid-word without SC-12) |
| **C-3** | every internal pāda boundary on a word/soft boundary or SC-10 fusion | +1.2 (else +0.3 per aligned break) |
| **C-4** | each satisfied yati | +0.5 |
| **C-5** | start coincides with D1/D2/LS/PS | +1.2 × conf |
| **C-6** | end coincides with D1/D2 | +1.8 × conf |
| **C-7** | VerseNumToken immediately after end | +3.5 × conf |
| **C-8** | crosses an internal D2 | −3.0 × conf (same as B3; charged once) |

---

## 8. Stages 7–9: scoring, decoding, annotation

### 8.1 Score (`scorer.py`)

```
S(c) = LLR_model(c)
     + log P(m)                               # anuṣṭubh 0.0, Upajāti −2.2, Vasantatilakā −2.5,
                                              # Śārdūlavikrīḍita −2.8, other vṛtta −3.5 (initial; re-estimate from gold)
     + log P(k | m, frame)                    # k=4: 0.0; k=2: −1.2; k=3: −3.2; k=1: −4.0; lifted by F-7 or R-3
     + log P(variant)                         # section 5.2 table
     − λ_edit · cost(c)                       # λ_edit = 1.6 (initial); edits charged here only
     + S_frame(c) + S_ret(c) + S_cues(c)
     + S_lang(c)                              # SV-6 negative prior when applicable
     + ν_start                                # per-verse start penalty, −1.0 (initial): opportunity correction
                                              # for evaluating many overlapping windows
```

**Units (v7):** every LLR term in `S(c)` is a **total** over the candidate's syllables (the per-syllable normalisation in §33.1 is a storage convention for the models; the scorer multiplies back by length), so `S(c)` is a per-event potential in natural-log units; `ν_start` is the only opportunity/exposure correction, which is what DEC-23 requires. Prose arcs score 0. A *single-span* candidate enters the Viterbi path only when it improves total path score; do **not** apply `S(c) > 0` as an independent proof of versehood. Paired macros use their explicitly defined total cost. Search intensity changes the candidate prior: estimate `ν_start` and classification thresholds on documents with comparable window density; report selection bias and reliability versus density.

### 8.2 Decoder (`decoder.py`) — single-arc default; optional macros only after §43 verification

Sparse lattice: prose arcs `(i, i+1, 0)`, verse arcs `(c.s, c.e, S(c))`. Candidates bucketed by end and by start.

```
best[0] = 0
for e in 1..N:
    best[e] = best[e-1]
    for c in C_end[e]: best[e] = max(best[e], best[c.s] + S(c))
```

Ties broken deterministically: fewer edits, fewer partials, fewer verses, earlier offset, then `(metre_id, variant_id)`. Metre aliases on one span collapse to a canonical id with aliases recorded (OPS-4).

Forward–backward in log-space over the **same deduplicated lattice**:

```
α_e = α_{e−1} ⊕ ⊕_{c∈C_end[e]} (α_{c.s} + S(c))        α_0 = 0
β_s = β_{s+1} ⊕ ⊕_{c∈C_start[s]} (S(c) + β_{c.e})      β_N = 0
Z = α_N = β_0      (assert |α_N − β_0| < 1e−9)
lattice_posterior(c) = exp(α_{c.s} + S(c) + β_{c.e} − Z)
p_prose_edge(i) = exp(α_i + β_{i+1} − Z)  # valid in **single-arc-only** lattice
p_verse_lattice(i) = 1 − p_prose_edge(i)  # NOT valid with paired macros: use DP-5
```

`lattice_posterior` is `P(arc | this lattice)`, **not** a calibrated correctness probability (CAL-1). Also store `margin_to_next_best` (Viterbi score minus best competing non-overlapping configuration through the span) and `evidence_completeness` (which layers were active).

**Uncertain regions.** Until calibration exists: syllables not in an accepted span where `p_verse_lattice ∈ [0.35, 0.65]` for ≥ 8 consecutive syllables, or where any candidate has `S(c) > −2.0` but lost — emitted as `uncertain` with the top-3 alternatives. These thresholds are the *initial* abstention policy and are frozen per release (CAL-5).

**Chunking** (OPS-7/8): candidate generation may run on overlapping chunks with overlap determined by maximum span + context-dependent scanner lookahead + frame/retrieval context + edit budget. **Score once using global feature state and globally indexed LMs**, dedupe candidates by canonical key, then run one global DP; do not combine independently decoded chunk posteriors. Whole-file/chunked identity is tested, not assumed.

### 8.3 Annotator (`annotate.py`)

1. **Pādas.** From the validated gate alignment; reference alignments can **propose** alternative pāda splits only if revalidated. Exact boundary offsets exist only when `BoundaryAnchor.resolution == exact_between_codepoints`. At fusion, record `shared_surface`/`inside_grapheme`, overlap in *analysis* rather than pretending two disjoint source strings. No post-hoc nudging (INV-9).
2. **Fused closer/opener.** With SC-12/F-5, trim only when a safe literal source boundary exists. Otherwise emit `frame_overlap` and typed anchors, with `surface_text == Document.text[observed_cover.start:observed_cover.end]`. A reconstructed verse reading is stored separately and never passed off as observed source.
3. **Attribution.** Raw frame → `config/authorities.yaml` → `{raw, primary_authority, via_digest, quotation_type}`; `quotation_type ∈ {cited, authorial, unknown}` from F-1/F-2 vs F-3, default `unknown`.
4. **OCR events.** Every edit/`?` becomes an `ocr_suspect` entry `{src_span | anchor, type, reason}`.

---

### 8.4 Paired quotations, barriers, and posterior semantics (DP-1…DP-10) — **normative v4**

A v3 inconsistency: A5 promises one **joint** score for two disjoint half-verses but the decoder's only operations are single-span verse arcs. Adding a pair bonus to both halves **double counts evidence** and is not equivalent to optimising a pair. Implement one of these alternatives:

- **Default before M3:** emit the `split_pair` as an *unscored* review relation; both halves are decoded independently; pairing has no selection bonus.
- **M3 verified mode:** create one `PairedArc(s1,e1,s2,e2,score_pair)` spanning `[s1,e2)`. The score is `S(span1) + S(span2) + bonus_pair`; `[e1,s2)` is an **internally annotated prose gap**. A DP path choosing this macro cannot separately choose the two component arcs. Output is *two* accepted verse spans, not a contiguous merged verse. Duplicate pair hypotheses are canonicalized. Limits: gap ≤ configured words and ≤ one paragraph unless an edition cue says otherwise.

```python
# Simplified v4 macro-arc lattice for a contiguous eligible run.
# Each arc has a start/end, weight, and a disjoint set of verse component spans.
# Prose arc (i,i+1) has weight 0; excluded spans are handled as barriers.
best[0] = (0.0, [])
for end in range(1, N + 1):
    options = [extend(best[end - 1], prose_arc(end-1, end))]
    options += [extend(best[arc.start], arc) for arc in arcs_by_end[end]]
    best[end] = deterministic_argmax(options)
# PairedArc occupies its envelope but marks its interior gap as prose.
```

- **DP-1** Arcs are disjoint in *envelope* space; a macro arc contributes a set of non-overlapping observed verse covers and explicit prose gaps. No node may choose component arcs and a pair macro together.
- **DP-2** All bar-delimited excluded/non-Sanskrit/footnote regions are barriers. Split lattice into contiguous eligible runs; allow cross-page continuation only if the page break is not a content barrier. Decoder never marks excluded text as a verse.
- **DP-3** Calculate Viterbi **and** forward–backward on *the same* final sparse arc set, including macro arcs. Do not use only single-arc formulas for a paired-span model.
- **DP-4** For a given observed verse cover, distinguish `posterior(candidate arc)` from `posterior(exists any arc realising this span)`; the latter sums mutually exclusive canonical alternatives including macros. Calibrated correctness is a third, separate quantity.
- **DP-5** `p_prose(i)` sums the mass of all arcs whose **annotation of slot i is prose**, including prose positions inside paired macros; it is **not** merely the edge `(i,i+1)` marginal in a model with macro gaps. Formula `1 - edge_prose_marginal` is invalid for that case.
- **DP-6** Confidence may be absent in budget-truncated or OOD regions: set `confidence_status=ood` and `calibrated_probability=null`; never promote large raw score to a fabricated probability.
- **DP-7** Macro candidate generation must remain bounded, e.g. only validated half-spans plus a closed set of bridging phrases. Cap pair arcs per 1,000 syllables and report incomplete pruning.
- **DP-8** If no macros are enabled and every eligible syllable has a prose edge, use the v3 single-arc recursion and exact log-sum-exp FB identities as a compatibility test.
- **DP-9** Validate all short sequences (≤ 12 slots, ≤ 20 arcs) by **exhaustive enumerator**: optimal path, log-partition, slot marginals and span marginals must agree to tolerance.
- **DP-10** Decoder ties, transparent gating, and abstention must be reproducible across chunk sizes. Floating-point sensitivity is documented; no reliance on dictionary iteration order.

### 8.5 Detection objective, not generic metre coverage (OBJ-1…OBJ-6)

- **OBJ-1** The primary latent state is `prose | verse_span | excluded | uncertain`; metre and variant are *conditional explanations* of a verse candidate, not the target outcome alone.
- **OBJ-2** Candidate quality and gate completeness are distinct. Report **candidate-generation recall** against gold before scoring; a missed candidate cannot be fixed by a better decoder.
- **OBJ-3** Track boundary precision separately for start, end, half, and pāda. Score over-extension (`gold verse + neighbouring prose`) as an error even when intersection is high.
- **OBJ-4** Candidate score uses explicit semantic cues only as secondary features. Do not claim semantic understanding from a character n-gram model.
- **OBJ-5** No production LLM inference; expert review can relabel annotation and attribution but may not mutate historical gold without versioning.
- **OBJ-6** Selecting `uncertain` is a third policy, not an attempt to inflate measured precision by excluding difficult gold positives. Report coverage/abstention and reviewed-positive rates together.


## 9. Data

### 9.1 Scanner gold (`data/gold/scanner.jsonl`, M1)
≥ 500 verses across the registry's metres, including pāda-final anceps cases, sandhi across spaces, fused `-iti`, and flagged characters. `chanda` and `vidyut-chandas` produce **silver** agreement labels; every disagreement and a random 20% of agreements are adjudicated by a human (record annotator and edition). Schema: `{id, text_devanagari, slp1, lg, matra, metre, adjudicated: bool}`.

### 9.2 Detection gold (`data/gold/detect/<tier>/<doc_id>.jsonl`, M2+)

| tier | construction | targets |
|---|---|---|
| **T** | `tools/build_gold_from_typeset.py` on 3–5 typeset mixed texts (Mitākṣarā, Medhātithi, Parāśaramādhavīya from GRETIL/SARIT): punctuated/numbered verses → spans; produces **T-punct** and **T-stripped** views with a recorded edit map and both hashes. Spans are **silver** until a sampled blind audit (≥ 200 spans, ≥ 2,000 prose words) is adjudicated; daṇḍas can mark prose and quotes can straddle formatting. | thousands of spans; audit sample adjudicated |
| **P** | owner-supplied proofread chapters of Nirṇayasindhu / Dharmasindhu; LLM pre-annotation → two human annotators on the test split; labels `full | half | three | pada | pratika | nonverse | ambiguous | excluded`, `quotation_type`, attribution | ≥ 350 full, ≥ 60 half, ≥ 25 pāda/pratīka, ≥ 50,000 prose words, plus the NEG suite |
| **R** | raw OCR of the same P chapters; gold projected through a character-level alignment; spans that cross inserted/deleted/merged text are `unscorable`; stratified human sample | same passages as P |

Record: `{start, end, padas:[[s,e],…], metre, variant, partial, quotation_type, attribution, source, status: silver|verified|ambiguous|unscorable, annotators}`.

### 9.3 Model training data
- Prose LMs: adjudicated verse-free paragraphs + pure gadya śāstra (Śābarabhāṣya, Tarkasaṃgraha commentary). Partition by work/edition (GOLD-1).
- Verse char LM: gold verses from the train split only.
- Language classifier: Sanskrit from the above; Hindi/Marathi ṭīkā from bilingual editions; `other` = Tamil runs, front matter.
- Priors (`log P(m)`, `log P(k|m)`, variant priors): counts from gold T train split.

### 9.4 Reference corpus
`data/reference/<work>/cleaned_devanagari/…` produced by the cleaner; `reference_manifest.json` with rights and edition. Owner supplies (section 15).

---

### 9.5 Annotation policy, negatives and leakage preflight (DATA-1…DATA-10)

**Ground truth is an editorial decision and must be explicitly defined.** Annotate *metrical quotation spans actually presented as verse*, irrespective of whether the source author agrees with the quotation's authority. Do not automatically label a stock phrase as a verse merely because it occurs in the reference index. Distinguish `intent=verse_quote | authorial_verse | metrical_prose | undecidable` from `metrical_form`; exact boundary labels may be `shared_surface` when sandhi removes the written separator.

- **DATA-1** Gold annotation UI must ask for start/end *surface covers*, metrical pāda slots, `boundary_resolution`, and `quotation_type` independently.
- **DATA-2** Label **hard-negative spans** as `negative_prose`, not just all text outside verses; sample long continuous prose, citation frames without quotations, verse-looking formulae and copied lines in discussion.
- **DATA-3** For editorial `citation vs kārikā`, separate `is_metrical_verse` from `is_a_quotation`; the detector should find both but cannot assert a primary authority from metre alone.
- **DATA-4** Two annotators + adjudication for **all of blind-test boundary disagreements**; published metrics state adjudicated-positive N, eligible-negative words and per-work counts.
- **DATA-5** P/R text versions and strip/no-strip versions of the same underlying passage share one split; treat near-duplicate editions and embedded standard verses as **retrieval leakage risk**, with a held-out-references setting.
- **DATA-6** Score exact surface offset only where human gold says recoverable; use a separate phonological-boundary F1 for coalesced cases. Never credit a guessed exact offset against fused gold.
- **DATA-7** Work-level bootstrap or blocked permutation intervals; per-verse binomial intervals are overconfident when pages/works are correlated.
- **DATA-8** Track annotation coverage: fraction of *all* characters reviewed, not only preselected verse candidates. Otherwise missed verses never enter gold and recall is upward biased.
- **DATA-9** Training reference index and metadata are **locked before test**. Report seen/unseen authors and works separately; no corpus-specific manual threshold tuning on test.
- **DATA-10** Publish the instruction sheet and adjudication trail; a silver automatically stripped set cannot be advertised as gold no matter how many entries it contains.


## 10. Review loop and offline LLM use

- `review.html`: single static file per document, offline, text embedded as escaped JSON (no raw insertion; QC-4). Shows the original with highlights by decision status, `uncertain` regions, excluded spans; inspector with pādas, L/G, evidence waterfall, alternatives, OCR events, raw-source toggle, ±150-character context. Keyboard triage `A/R/B/M/P/U/E` (accept, reject, boundary, metre, partial/authorial, uncertain, export). Decisions are append-only events `{prior, new, reviewer, time, run_id, reason}` exported as `review_decisions.jsonl` (QC-2); the page never writes files silently.
- LLM, offline only, in `tools/`: pre-annotation drafts for human verification; ranking `uncertain` spans; proposing sandhi splits for display. Never imported by `padya/`.
- `tools/tune.py`: coordinate ascent / Powell over `weights.yaml` with L2 regularisation toward initial weights, objective `span-F1 − 5.0 × FP_per_1k` on **train/dev** only; test split frozen; freeze scorer + thresholds + calibration before reporting test numbers.

---

## 11. Metrics (`tools/metrics.py`) — reported per milestone, per tier, per work

| metric | definition |
|---|---|
| Span P / R / F1 exact | exact observed source boundaries **only where human gold marks them resolvable**; report separate shared-surface boundary detection |
| Span P / R / F1 ±1 akṣara | each *resolvable* boundary within one observed syllable; report separately, never substitute for exact; no ±1 credit for invented fused offsets |
| Start-exact / end-exact | separately |
| Pāda boundary accuracy | among exact matches |
| Metre accuracy, variant accuracy | among matches |
| Partial-verse recall | by class: half, three, pāda, pratīka |
| **FP per 1,000 adjudicated prose words** | count one event for every predicted span covering only gold prose, **plus separate intrusion rate** for predicted spans that partially overlap a gold verse but swallow prose; 95% work/chapters clustered CI; denominator excludes unscorable text |
| Recall at FP budget | exact recall at ≤ 1 / ≤ 2 / ≤ 3 FP per 1,000 |
| Attribution accuracy | `primary_authority` exact; `via_digest` exact; reported for seen vs unseen reference works |
| Uncertain rate | share of syllables in `uncertain` |
| Calibration | Brier, ECE, reliability diagrams and precision–coverage; `calibrated_probability` only after grouped, held-out dev calibration; report slice sizes |
| Robustness | deltas under punctuation stripping, space collapse, Unicode variants, synthetic noise, real P↔R pairs |
| Runtime | per-stage wall/CPU time, syllables/s, peak RSS, candidate density, worst-case slowdowns, hardware/OS/Python/threads, config + model hashes |

---

## 12. Milestones and acceptance gates

| milestone | scope | gate (*initial targets; aspirational until a blind test exists*) |
|---|---|---|
| **M0 Skeleton** | repo, dataclasses, loader, SV-9 analysis view with spans, offset property tests, gold loaders, metrics, `build_gold_from_typeset.py`, `verse-detect selftest` | all INV/OFF property tests pass; selftest runs offline; **no speed promise** before hardware measurement |
| **M0.5 Data contract** | adapter for the cleaner contract (§29), validations, synthetic fixtures labelled as such when real outputs are absent | adapter refuses `reading_view` output, warns on `strip_accents`; round trip on real cleaner output |
| **M1 Scanner** | SV-1…10, SC-0…9, SC-12 surface cue detection; SC-10/11 **described and test-scaffolded but disabled** | ≥ 99.5% L/G, ≥ 99.9% count, 100% offset validity on adjudicated scanner gold |
| **M2 Anuṣṭubh, tier T** | **pathyā-only** baseline, bitmask prefilter + full gate, Tier A, Tier B (anuṣṭubh only), rhythm prose baseline, scorer, Viterbi + FB, NEG suite v1 | T-punct exact F1 ≥ 0.96, FP ≤ 0.5; T-stripped exact F1 ≥ 0.87, ±1 F1 ≥ 0.93, FP ≤ 1.0; T02/T04/T10 pass |
| **M2.5 Vipulās** | add one **independently verified** variant at a time (candidate order na → bha → ma → ra, not a fixed philological priority), each with primary reference, oracle comparison and paired near-negative fixtures (§25.1) | each enabled variant: no FP increase > 0.1 per 1,000 on T-stripped; recall gain reported per variant |
| **M3 Frames, partials, splits** | F-1…9, SC-12, A5, A6 (unresolved only), authorities.yaml | partial recall ≥ 0.82 at FP ≤ 1.5; attribution ≥ 0.92 on T; T03 pass |
| **M4 Classical vṛttas and jāti** | verified registry, **optional** Āryā/Vaitālīya tracks (off by default), language runs (off until validated), yati cues | metre accuracy ≥ 0.96; no M2/M3 regression > 0.5 pt; T16/T17 pass |
| **M5 OCR tiers** | banded aligner, budgets, `?`, tier-R delimiters, `unprocessable`, OCR ablation | P exact F1 ≥ 0.82 (±1 ≥ 0.92), FP ≤ 2.0; R ±1 F1 ≥ 0.75, FP ≤ 3.0; T07/T08 pass; ablation reported |
| **M6 Retrieval, review, calibration** | index, A6 resolution, review.html, tune.py, CAL-2 calibration | retrieval precision ≥ 0.98; pratīka recall ≥ 0.75; tuning improves dev F1; Brier/ECE reported; T14/T15 pass |
| **M7 Corpus run and export** | chunked run on **owner-provided licensed** Nirṇayasindhu, Dharmasindhu, Mitākṣarā samples; VTF export | deterministic chunked = whole (T09, T19); measured throughput and RSS declared; export validates against the owner-supplied VTF schema |

Each `reports/M<n>.md`: metric table, invariant pass/fail, the **enabled** fixture set T01–T42 (v6 §47), error taxonomy codes (§34), 20 worst errors with offsets, cause and planned fix, release-report template (§22/§48). Deferred-fixture status is explicit, not counted as passing.

---

## 13. Output formats (`padya/writer.py`)

### 13.1 `verses.jsonl` (legacy field names plus v4 §24 additions)

Required legacy fields (a v4 record must also include all §24 fields; a record missing any mandatory key is invalid):

```
source_id, source_sha256, cleaner_version, detector_version, metre_registry_version, config_sha256, run_id,
start, end, text, offset_unit, source_tier,
metre_id, variant, partial, half_position, quotation_type,
padas, boundary_status, sandhi_fused_boundaries,
raw_score, lattice_posterior, calibrated_probability, confidence_status, margin_to_next_best, evidence_completeness,
candidate_origin, tier_rule, lg_full, ocr_suspect, trimmed_opener, trimmed_closer,
attribution, source_match, split_pair, evidence
```

Offset-checked fixture **for resolvable boundaries only** (the source document is exactly this one line, length 91 code points, SHA-256 `5b8014f44480aa9ec2462ee67ff095cd5147e9126cd280bc191ef37340f89a32`):

```
अत्र केचिदाहुः अयं निजः परो वेति गणना लघुचेतसाम् उदारचरितानां तु वसुधैव कुटुम्बकम् इत्यादि।
```

```json
{
  "source_id": "fixture-001", "source_sha256": "5b8014f4…89a32",
  "cleaner_version": "3.0", "detector_version": "<v>", "metre_registry_version": "<v>", "config_sha256": "<sha>", "run_id": "<id>",
  "start": 15, "end": 82,
  "text": "अयं निजः परो वेति गणना लघुचेतसाम् उदारचरितानां तु वसुधैव कुटुम्बकम्",
  "offset_unit": "unicode_codepoint", "source_tier": "T",
  "metre_id": "anustubh", "variant": ["pathya","pathya","pathya","pathya"], "partial": "full", "half_position": null,
  "quotation_type": "unknown",
  "padas": [[15,32],[33,48],[49,64],[65,82]], "boundary_status": "inferred", "sandhi_fused_boundaries": [],
  "raw_score": 11.4, "lattice_posterior": 0.994, "calibrated_probability": null, "confidence_status": "uncalibrated",
  "margin_to_next_best": 7.9, "evidence_completeness": ["gate","prose_lm","frames","cues"],
  "candidate_origin": "anchored", "tier_rule": "A2",
  "lg_full": "LGLGLGGL LLGLLGLG LGLLLGGL LLGLLGLG",
  "ocr_suspect": [], "trimmed_opener": null, "trimmed_closer": "इत्यादि",
  "attribution": {"raw": "केचिदाहुः", "primary_authority": null, "via_digest": null},
  "source_match": null, "split_pair": null,
  "evidence": [["llr_model",5.8],["frame_open",2.0],["frame_close_ellipsis",2.0],["frame_synergy",1.2],["pada_word_boundaries",1.2],["metre_prior",0.0],["start_penalty",-1.0]]
}
```

Only the source length, hash, offsets and slices can be mechanically validated independently of a metrical implementation. The `lg_full`, `variant`, and scores are **illustrative expectations, not certified gold**; M1 must obtain an independently adjudicated scansion before enabling this fixture as a metre-accuracy assertion. See §47 for machine verifiers.

### 13.2 `regions.jsonl`
Two partitions, both complete and non-overlapping (INV-6): (i) every metrical syllable has exactly one label `prose | verse:<id> | uncertain | excluded | non_sanskrit | unprocessable`; (ii) character regions cover every code point `[0, len)` exactly once, with whitespace and punctuation assigned deterministically to the adjacent region or a `separator` run. Fields: `start, end, label, syllable_count, p_verse_lattice_mean, p_verse_lattice_max, alternatives (for uncertain)`.

### 13.3 `candidates.jsonl` (optional, `--emit-candidates`)
All scored candidates with features, for tuning and review; may overlap.

### 13.4 `report.json`
Metadata and hashes, cleaner manifest echo, region counts, metre/variant histograms, attribution histogram, candidate density, pruning counters (OPS-6), unscorable spans, review list (raw-score ordered until calibrated), thresholds, runtime telemetry.

### 13.5 VTF export (`tools/export_vtf.py`)
Verse → VTF Text Unit with Metre, Cross Reference (`source_match`) and Annotation (attribution), keyed by the document's VTF scripture id. Implemented only after the owner supplies the current schema (**ASK**, M7).

---

## 14. Repository layout, CLI, tests

```
padya/
  pyproject.toml            # python >= 3.11; runtime: numpy, pyyaml, regex, tqdm; dev: pytest, hypothesis, chanda, vidyut
  padya/
    config/ weights.yaml metres.yaml frames.yaml authorities.yaml profiles.yaml
    loader.py scanview.py scanner.py candidates.py scorer.py decoder.py annotate.py writer.py cli.py
    metres/ bitmask.py align.py anustubh.py vrtta.py jati.py registry.py
    evidence/ prose_model.py frames.py retrieval.py cues.py
  tools/ build_gold_from_typeset.py build_prose_lm.py build_reference_index.py tune.py calibrate.py export_vtf.py metrics.py
  data/ gold/ reference/ models/ metres/verification.tsv
  tests/ test_sv_rules.py test_sc_rules.py test_anustubh.py test_vrtta.py test_jati.py test_candidates.py
         test_decoder_math.py test_offsets.py test_properties.py fixtures/T01…T42
  reports/
```

CLI (target interface):

```
verse-detect selftest
verse-detect scan <file> [--strict] [--metres anustubh,...]
verse-detect run <cleaned_folder> --tier P [--profile classical_strict] [--no-retrieval] [--no-language-filter]
                 [--chunk-syllables N] [--emit-candidates] [--resume] [--out DIR]
verse-detect evaluate --gold data/gold/detect --split test --out reports/eval
verse-detect review <out_dir> --offline
verse-detect benchmark <file> --out reports/bench.json
verse-detect dry-run <cleaned_folder>          # candidate counts, memory estimate, no annotations
verse-detect diagnose-offset <file> <start> <end>
```

`selftest` needs no network, keys or private corpora.

**Mandatory property tests (hypothesis):** zero mutation (`doc.text[v.start:v.end] == v.text` for random Unicode input with random punctuation and OCR edits); partition completeness for both region partitions; `|α_N − β_0| < 1e−9` and all posteriors in `[0,1]`; **local cue monotonicity** (adding a valid end delimiter cannot reduce that candidate's local boundary-cue feature *with other input/features fixed*; **global lattice posterior need not be monotone** due to competition); deterministic rerun (identical ids, regions, scores in a fresh process).

Coding standards: type hints; frozen dataclasses; rule ids in comments; sorted/seeded determinism; core detector runtime uses standard library + NumPy, plus the explicitly pinned `regex` and PyYAML dependencies where grapheme-safe processing/config parsing needs them; `tqdm` is CLI-optional. `chanda`/`vidyut` are **development-only** oracles never imported by `padya/`.

---

## 15. ASK points

1. VTF JSON Schema and scripture-id conventions (before M7).
2. Reference corpus inventory, state and rights (before M6).
3. Authorial kārikās vs quotations — default in section 21 unless overridden (before M3).
4. SC-11 *muta cum liquida* leniency — enable or not, with corpus examples (during M2).
5. Any metre-table disagreement between Vṛttaratnākara, `chanda`, `vidyut-chandas` (during M0/M4).
6. Any manual change to `weights.yaml` outside `tune.py`.

---

## 16. Reference material

- `normalisation_spec_v2.md`; `clean_sanskrit_corpus.py` v3.1 (records sidecar, manifest, `to_slp1` tables; receipt in §49).
- Kedārabhaṭṭa, *Vṛttaratnākara* — primary authority for 5.2–5.4.
- Terdalkar & Bhattacharya, *Chandojñānam*, WSC 2023; `chanda` on PyPI (AGPL v3) — test oracle only.
- Ambuda `vidyut-chandas` (Rust, MIT, experimental) — second test oracle.
- Ollett, Anuṣṭubh notes (prakrit.info/vrddhi/meter/anustubh); Park 2018 on Āryā gaṇa restrictions (doi 10.29213/crbs..23.201806.91); Melnad, Goyal & Scharf 2013.
- Skrutable (skrutable.info) — pāda re-splitting for comparison on preselected candidates.

---

## 17. Invariants and offset safety

### 17.1 Source immutability
- **INV-1** `Document.text` is immutable and the sole reference; `verse.text == Document.text[start:end]`.
- **INV-2** `0 ≤ start < end ≤ len(text)` for every non-empty interval; code-point units unless a converted view says otherwise.
- **INV-3** Pāda **metrical slots** are ordered and non-overlapping. Observed source *covers* may share characters at verified fusion; every source cover lies inside the verse observed cover and carries a `BoundaryAnchor`. Internal whitespace is retained as-is.
- **INV-4** Final verse spans never overlap; alternatives live only in `candidates.jsonl` / review.
- **INV-5** Every vowel nucleus belongs to exactly one Akshara; non-syllable characters have an explicit attachment policy.
- **INV-6** Both partitions of 13.2 are complete and overlap-free.
- **INV-7** No normalisation, sandhi resolution or retrieved text ever modifies `Document.text`; proposals are evidence.
- **INV-8** Every output carries `source_sha256, cleaner_version, metre_registry_version, detector_version, config_sha256, run_id`; stable ids derive from source hash + canonical observed cover + parse id (when fused) + namespace, never detection order. Identical observations with different parses get distinct *candidate* ids, not duplicate accepted verses.
- **INV-9** No silent boundary adjustment after validation; an alternative split is a new candidate with its own gate result and score.

### 17.2 Alignment (Devanagari ↔ SLP1 ↔ OCR)
- **OFF-1** Each phonological token carries a **many-to-many ordered origin-edge set**, not just one `(slp_start, slp_end, src_start, src_end)` tuple. Edges may refer to a source span, analysis span, or a zero-output tombstone, with `rule_id`; the covering source interval is a derived view. A grapheme may map to several SLP1 characters or none. This supersedes the older one-interval shorthand in §17.
- **OFF-2** Work in code points; audit combining marks, nukta, avagraha, ZWJ/ZWNJ, accents, punctuation, NBSP; never split a grapheme at a verse boundary.
- **OFF-3** Alignment fixtures: composed/decomposed forms, zero-width marks, mixed punctuation, a word across a line, OCR confusions.
- **OFF-4** Where analysis drops/merges characters, keep a many-to-many interval alignment so **the observed covering interval** remains available. An exact underlying word boundary is *not* always recoverable (OFF-7).
- **OFF-5** Gold-projection tools emit source and destination hashes, a monotone edit map and an `unalignable` flag; projected spans are never assumed exact across inserted/deleted text.
- **OFF-6** The review UI converts code-point offsets to UTF-16 before slicing; Python/JS round-trip tests include non-BMP characters.

Property test: random Unicode text with random punctuation, spaces and edit spans → every accepted annotation's `text[start:end]` equals its serialised slice; abstention is allowed, invalid spans never.

---

## 18. Candidate safety, hard negatives, OCR robustness

### 18.1 Candidate families
- **CAND-1 anchored** — delimiter/number/frame cues are strong evidence, not proof.
- **CAND-2 free** — needs two coherent hemistichs or an externally supported partial.
- **CAND-3 retrieval-assisted** — confirmed on surviving words only (R-A).

### 18.2 Hard-negative suite (`NEG-*`, `data/gold/negatives/`)
Required negative classes, each with ≥ 30 human-labelled instances: (1) nibandha prose with accidental 8/16/32 totals; (2) four nearby 8-syllable windows without shared cadence; (3) formulaic prose with `अथ`, `तत्र`, `इति`, `उक्तं च` and no verse; (4) headings, colophons, headers, footnotes; (5) OCR duplicates, missing spaces, conflated glyphs, dropped vowel signs, false daṇḍas; (6) one genuine pāda inside unrelated prose; (7) bibliographic lines and numeric references; (8) Sanskrit inside Hindi/Marathi and vice versa; (9) densely metrical prose and planted repetitions; (10) a known verse text planted in a non-verse context.

- **NEG-1** A free full-verse candidate passes every pāda constraint — never "32 syllables + one matching 8".
- **NEG-2** Thresholds are calibrated per tier and candidate family when distributions differ; publish actual false positives and grouped uncertainty, never infer zero population error from zero sample events.
- **NEG-3** Partials need an independent anchor; the narrower the fragment, the heavier the burden.
- **NEG-4** A frame never overrides a failed exact gate unless the candidate carries an allowed, recorded edit.
- **NEG-5** Starting inside a collapsed word keeps exact offsets and flags `word_boundary_suspect`.
- **NEG-6** Language-run decisions can lower a prior but never delete quoted Sanskrit from eligibility.

### 18.3 OCR handling
- **OCR-1** Correct nothing; uncertainty = local alternatives backed by edit events and offsets.
- **OCR-2** Syllables are `observed | inferred | unscorable`; an inferred insertion has an anchor between code points, not a character range.
- **OCR-3** Prefer low-entropy edits supported by cleaner flags / a confusion table (`ि↔ी`, `ु↔ू`, dropped `ं`, dropped `्`), and require a meaningful score gain over the no-edit candidate.
- **OCR-4** Per-pāda/per-window edit caps plus **local** candidate-density and noise caps; high-noise regions abstain without suppressing neighbouring clean pages or silently dropping any text.
- **OCR-5** Evaluate on real P↔R pairs and on synthetic corruption separately; synthetic never replaces real.
- **OCR-6** Report a no-edit ablation so the recall gain and FP cost of tolerance are visible.

---

## 19. Implementation details: indexing, chunking, determinism

- **OPS-1** Compile verified fixed metres into length-indexed bitmask tables; anuṣṭubh and jāti have their own grammars.
- **OPS-2** Precompute L/G arrays, flags, word starts, delimiter positions, cumulative mātrās and offset maps once per document.
- **OPS-3** Tier A runs first but never irreversibly blocks Tier B; conflict zones get a second pass.
- **OPS-4** One canonical arc per `(s, e, metre_id, variant_id, parse)`; aliases aggregated.
- **OPS-5** Pruning is admissible under the tier budget (B4).
- **OPS-6** Diagnostic counters: `window_starts, gate_calls, prefilter_rejects, failed_first_pada, edit_expansions, candidate_arcs, density_cap_hits`.
- **OPS-7** Overlapping chunks with overlap ≥ longest enabled span + frame window + budget; no final decision at a seam.
- **OPS-8** Seam reconciliation by global offsets and candidate identity, then a global DP; chunked output must equal whole-file output.
- **OPS-9** Stress tests: multi-million syllables, one unbroken blob, dense punctuation, all-laghu prose, combining marks, adversarial OCR.
- **OPS-10** Every performance claim states CPU, Python version, cache state, per-stage time, peak RSS, candidate density.
- **API-1** `run(input, config) -> Result` per module. **API-2** `dry-run`. **API-3** flags listed in section 14. **API-4** `selftest` offline; `--strict` never alters gold or source files.

---

## 20. Statistical scoring, leakage control, calibration

- **PR-1** Emit reproducible feature vectors per candidate (metre strictness/coverage, pāda consistency, boundary plausibility, frame distance, edit profile, LLRs, tier, language cue).
- **PR-2** Retrieval splits into similarity and attribution.
- **PR-3** Natural-log units, per-syllable normalisation, no double-charged edits, no alias double counting.
- **PR-4** Retrieval may use only references allowed by the evaluation partition; otherwise results go in a separate `reference_seen` view.
- **PR-5** Prose LMs train on adjudicated prose only.

- **GOLD-1** Splits by underlying work/edition and near-duplicate family, never random verses.
- **GOLD-2** Gold has adjudicated positive AND negative spans, boundary-resolution class, and source/phonological annotations. Ambiguous/unresolvable exact boundaries are excluded from the **exact surface-offset denominator** but included in a separately reported `shared_surface` benchmark. Publish scorable counts.
- **GOLD-3** `quotation_type` is labelled separately from metre and partial.
- **GOLD-4** P/R pairs and T-punct/T-stripped pairs stay in one partition.
- **GOLD-5** Report silver / verified / ambiguous / unscorable counts; silver never enters headline test metrics.
- **GOLD-6** Two evaluation views for retrieval: closed-reference and novel-quotation (withheld work).
- **GOLD-7** Record annotator agreement on offsets, prose/verse and partial type; adjudicate without model predictions in view.

- **CAL-1** Lattice posterior ≠ calibrated probability.
- **CAL-2** Fit monotone calibration (isotonic if enough dev data, else Platt) per tier/family on dev only.
- **CAL-3** Report Brier, ECE, precision–coverage; calibrate on dev, never test.
- **CAL-4** `confidence_status ∈ {uncalibrated, calibrated, ood, incomplete_search}`; `calibrated_probability = null` unless `calibrated`.
- **CAL-5** The production threshold is set by the FP-per-1k budget, not by an appealing probability; `strict` and `review` operating points are both published.

---

## 21. Review workflow and owner defaults

- **QC-1** Reviewer sees original context, highlights, inferred pādas, evidence, competing hypotheses, retrieval claims, OCR events, raw-source toggle.
- **QC-2** Actions `Accept / Reject / Adjust span / Adjust pāda / Mark partial / Mark authorial / Resolve attribution / Uncertain` → append-only events with prior/new offsets, reviewer, timestamp, versions, reason.
- **QC-3** No inferred correction is applied to the original; suggestions appear in a separate `analysis_text` column.
- **QC-4** Offline; escaped data embedding; no script injection from text.
- **QC-5** Export/import and deterministic replay into the training pool; frozen test labels are never auto-replaced.

| question | default until overridden |
|---|---|
| Vedic metre detection | disabled; cleaner-tagged spans excluded with `source_tag = vedic` |
| Kārikās vs quotations | both `verse`; `quotation_type = unknown` unless F-1/F-2/F-3 evidence |
| Canonical reference text | cleaned Devanagari, code-point offsets, immutable |
| SC-10 ekādeśa, SC-11 leniency, AN-9 hypermetric, ta-vipulā, Āryā, Vaitālīya | off until verified and measured |
| Metre profile | `classical_strict` |
| Retrieval | off until corpus and rights are confirmed |
| Confidence | `null / uncalibrated` until CAL-2 passes |
| Text correction | never |
| LLM in `padya/` | never |
| VTF export | deferred until schema supplied |

---

## 22. Adversarial acceptance fixtures and release report

`tests/fixtures/T01…T42` **plus v6 T31–T42**, exact surface/code-point expectations where resolvable and typed boundary expectations otherwise; no private corpora:

| id | case | must assert |
|---|---|---|
| T01 | four pādas with and without daṇḍas | same content span after projection; no punctuation inside `text` |
| T02 | 32-syllable prose passage | abstain or `uncertain`; never a verse on count alone |
| T03 | 16-syllable half + `इत्यादि` | `partial = half`, exact span, `trimmed_closer` |
| T04 | genuine 8-syllable pāda, no context | abstain |
| T05 | overlapping 8/16/32 windows | one final non-overlapping span; alternatives retained |
| T06 | pāda boundary inside a fused word | metrical slots correct; boundary is typed `shared_surface` where exact offsets impossible; source covers valid |
| T07 | OCR-dropped vowel sign | edit event, source unchanged, abstention if ambiguous |
| T08 | wrong daṇḍa, roman `I/1` false delimiter | tier-aware; no forced segmentation |
| T09 | verse across a page/chunk seam | identical whole-file and chunked output |
| T10 | pure prose with `तथा च` | no verse without metrical proof |
| T11 | Sanskrit quote inside Hindi commentary | quote eligible; surrounding run excluded/reviewed |
| T12 | combining marks, non-BMP character | Python↔JS offset round trip; never split an extended grapheme cluster |
| T13 | tempting false yati / word split | no metre-invalid pāda shift |
| T14 | known half-line in the wrong place | retrieval does not over-extend or fabricate |
| T15 | two editions sharing a quotation | no train/test or retrieval leakage |
| T16 | unregistered metre in prose | must not invent a metre; `uncertain` only if independent poem evidence exists, otherwise prose |
| T17 | duplicate alias metre definitions | one canonical candidate; no inflated posterior |
| T18 | 1M-syllable adversarial input | bounded by declared workload limits; explicit `search_incomplete` or `unprocessable` for capped zones, no silent drops |
| T19 | rerun in a fresh process | identical source-derived ids, regions and scores; compare wall-clock `run_id` separately if non-deterministic |
| T20 | corrupted offset map | fail closed; no annotation emitted |
| T21 | fused `-इति` closer | exact trim **only if present as a safe source substring**; otherwise `frame_overlap`/typed boundary, no invented end |
| T22 | split ardhaśloka with gloss | two spans linked by `split_pair` |

| T23 | gold example's L/G vs initial v3 table | verify corrected expected sequence against independently adjudicated syllables; fail if unverified |
| T24 | standard bha-/ma-/ra-vipulā positives & near negatives | canonical `GLG+GLL`, `GLG+GGG`, strict caesura; prohibited variant not silently accepted |
| T25 | Hariṇī gaṇa/pattern mismatch deliberately injected | metre registry compiler fails closed with line-numbered diagnosis |
| T26 | fused opener `यथाहाष्टौ` | surface span exact, underlying vowel may be unrecoverable; `shared_surface` anchor, no fictional `अ` source |
| T27 | anusvāra before vowel and candrabindu ambiguity | default guru for anusvāra; optional alternate labelled; no zero-mātrā unknown |
| T28 | split halves plus prose gap | macro-arc bonus once; **gap remains prose**; Viterbi and FB agree with brute-force enumerator |
| T29 | clean paragraph next to extremely noisy OCR page | only the noisy region abstains; no file-wide `unprocessable` |
| T30 | retrieval half-line + competing unrelated passage | full-text coverage and contextual gate, exact alignment; no stock-string hallucination |

Release report template:

```
Commit / config sha / source hashes / registry version / model versions:
Train, dev, blind-test works and editions:
Tier: T-punct | T-stripped | P | R
Gold: positives N (verified/silver), negatives words M, partials by class, ambiguous N, unscorable N
Exact span: TP / FP / FN, P / R / F1, start-exact, end-exact
±1 akṣara: P / R / F1 (separate)
FP / 1,000 gold prose words, 95% CI by work
Metre / variant / pāda accuracy | partial recall by class | attribution (seen / unseen references)
Uncertain fraction | calibration Brier / ECE | precision–coverage at strict and review points
Candidates per 1k syllables | runtime | CPU | Python | peak RSS | chunks
Worst 20 errors: offsets, cause, planned fix
T01–T42 and property tests: pass / fail (xfail only with issue id)
```

---

## 23. Risk register

| risk | severity | mitigation / blocker |
|---|---|---|
| bad offset projection | critical | fail closed on any mismatch; INV/OFF property tests |
| accidental prose matches | critical | NEG suite, per-tier FP budget, independent test works, start penalty |
| wrong vipulā / Āryā rules | high | disabled-until-verified registry, `verification.tsv` |
| gold leakage through shared quotations | high | split by work; closed vs novel retrieval views |
| OCR tolerance fabricating verse | high | edit events, per-pāda caps, ablation, no text change |
| overconfident probabilities | high | posterior vs calibrated separation; CAL-* |
| memory/time on full books | high | sparse lattice, bounded chunks, stress tests |
| licence of third-party data/code | high | AGPL oracles dev-only; reference rights manifest |
| schema drift (cleaner / VTF) | medium | adapters, manifest handshake, fixtures |
| archaic or non-standard verse | medium | abstain/review; profiles |

**Handoff criterion.** An independent developer can run `selftest` and the benchmark clean-room, reproduce every reported number from the frozen splits, inspect any accepted verse's exact source coordinates and evidence, and see which statistical claims remain unvalidated.


---

## 24. v4 schema delta and versioned compatibility

These fields extend §13.1 and are **mandatory in schema v4**, in addition to the v3 required keys. Do not silently reinterpret an old v3 `start`/`end` as a fully recovered philological boundary.

| field | type | rule |
|---|---|---|
| `schema_version` | string | `4.0` |
| `observed_cover` | `[start,end]` | exact source substring; always present for detected spans |
| `start_boundary`, `end_boundary` | `BoundaryAnchor` | `exact_between_codepoints / inside_grapheme / shared_surface / unresolved` |
| `pada_boundaries` | array of `BoundaryAnchor` | may refer to source-sharing phonological parse |
| `surface_parse_id` | string | stable hash of alignment/interpretation |
| `source_alignment_trace` | array | versioned many-to-many edges; include elision/fusion |
| `metrical_slots` | integer ranges | slots of selected `ScansionPath` |
| `reconstructed_reading` | nullable string | labelled inference only; NEVER a source slice |
| `frame_overlap` | nullable object | surviving opener/closer material shared with verse |
| `parse_exhaustive` | boolean | false when local parse alternatives pruned |
| `search_incomplete` | boolean | true when local density/budget bounds drop possibilities |
| `arc_posterior`, `span_marginal` | nullable numbers | distinguish arc event from union of alternative arcs |
| `evidence_provenance` | list | origin rule/model, feature units, reference edition |

### 24.1 Schema and output invariants

- `verse.text` is **always** `Document.text[observed_cover.start:observed_cover.end]`; `start/end` are retained as *aliases for observed cover only* with equality assertions.
- If a boundary is `shared_surface`, `.offset` is `null`; its covering range must refer to an observed grapheme/token, and the relevant parse event must be present.
- `calibrated_probability` is null unless calibration is frozen and applicable to the tier/family and candidate-density regime.
- One `source_id` per input document and one accepted *surface region* partition. A paired quote produces two verse records with separate covers and a `split_pair` edge; intervening prose is never highlighted as verse.
- `regions.jsonl` and `verses.jsonl` are emitted atomically after validation (temp file + fsync/rename); failed validation leaves an error report and **no partial final outputs**.
- JSON Schema validation at each milestone with fixtures for v3-v4 migration and negative schema tests.

### 24.2 Suggested minimal fixture (no invented reconstruction)

```json
{
  "schema_version": "4.0",
  "source_id": "fixture-001",
  "observed_cover": [15, 82],
  "start_boundary": {"resolution":"exact_between_codepoints","offset":15,"covering_src":null,"analysis_left":null,"analysis_right":0,"transformation":null,"evidence_ids":["T01"]},
  "end_boundary": {"resolution":"exact_between_codepoints","offset":82,"covering_src":null,"analysis_left":31,"analysis_right":null,"transformation":null,"evidence_ids":["T01"]},
  "surface_parse_id": "source-unchanged",
  "reconstructed_reading": null,
  "text": "अयं निजः परो वेति गणना लघुचेतसाम् उदारचरितानां तु वसुधैव कुटुम्बकम्"
}
```

This JSON is a **schema fragment** illustrating new fields, not a complete §13.1 verse record. The canonical full fixture is still §13.1, with its L/G verified before use as a passing scanner example.

---

## 25. Automated metre registry compiler (`tools/verify_metres.py`)

Treat the registry as *code*, not a manually trusted list. Build on every commit:

```python
GANA = {
    "ma": "GGG", "ya": "LGG", "ra": "GLG", "sa": "LLG",
    "ta": "GGL", "ja": "LGL", "bha": "GLL", "na": "LLL",
    "la": "L", "ga": "G",
}

def compile_meter(entry):
    derived = "".join(GANA[x] for x in entry["gana_tokens"])
    assert len(derived) == entry["syllables_per_pada"], entry["id"]
    assert derived == entry["pattern"], entry["id"]
    assert entry["verification_status"] == "verified", entry["id"]
    return derived
```

Rules: (i) tokenize explicit gaṇa words, never substring-match transliterated metre names; (ii) check alias collisions; (iii) check composition for Upajāti mixtures and ardhasamavṛtta odd/even templates; (iv) generate known-positive and near-negative patterns automatically; (v) check that metres share an *identical emitted label* only if the registry explicitly declares an alias; (vi) store primary/secondary source and verification reviewer. The corrected Hariṇī candidate `LLLLLGGGGGLGLLGLG` is **formula-derived, not philologically certified** until checked.

### 25.1 Critical śloka grammar counterexamples

For an odd pāda with syllables 2–7 `GLGGLL` (2–4 `GLG`, 5–7 `GLL`), **bha-vipulā must not be rejected merely because of `GLG`**. The v3 bha table did so. With 2–7 `GLGGGG` and verified caesura after syllable 5, ma-vipulā is potentially eligible; without the required caesura under strict profile, it is not. A free 32-syllable window with the right fifth-to-seventh pattern but a forbidden 2–4 opening must fail. Create both positive and near-negative tests; a score threshold change cannot replace the grammar.

---

## 26. Computational safeguards and exhaustive reference implementations

1. **Small-instance oracle:** implement an intentionally slow exhaustive segmentation and phonological-path search for ≤ 12 analysis slots; compare to the optimised DP and bitmask gate across random fixtures.
2. **Search completeness flag:** whenever beam/candidate/density caps are reached, expose `search_incomplete=true`, downgrade score/confidence and write an explicit `uncertain` or `unprocessable` surface region. No silent tail-dropping.
3. **Feature trace:** an accepted verse carries a line-by-line score waterfall in *natural-log units*; note whether each evidence source uses the candidate itself (risk of circular confirmation).
4. **Deterministic partition:** no raw OCR markup, footnote text, Vedic exclusion, or page furniture can be labelled verse by a spanning arc. Page-break *markers alone* may be traversed.
5. **No premature metadata use:** authority names and retrieved verse texts do not change observed characters or overrule the metre gate without a declared exceptional path.
6. **Canonical output:** stable sorting by offsets and parse id; JSON with deterministic key order/float precision; `run_id` derived from run manifest or clearly separated from a deterministic content hash (do not expect wall-clock run ids to match).
7. **Low-memory operation:** stream document reading/offset construction where possible, reuse compact token arrays, avoid retaining full candidate text strings, and emit per-stage peak RSS. Make LMs/model files memory-mappable if warranted by measurement.
8. **Fault model:** invalid manifest, missing sidecar, orphan records, out-of-range offsets, inconsistent SLP1 map, corrupt registry, incompatible model hash, disk full, and interrupted write all fail with a classified error and no misleading partial success.
9. **Threat model:** sanitize paths/file names, protect against relative-path traversal in extraction, bound OCR uploads and HTML-embedded data, escape `review.html` content (`<`, `>`, `&`, U+2028/U+2029), never execute book text as script or regex.
10. **Rights:** source reference rights, attribution provenance, external metre-table licences and dependency SBOM are versioned before redistribution; test-only AGPL tools must not be imported or bundled as product dependencies.

---

## 27. Reproducible evaluation protocol and release blockers

### 27.1 Independent evaluation matrix

| axis | mandatory strata |
|---|---|
| Source quality | T-punct, T-stripped, real P, real R, synthetic perturbation *supplement* |
| Work type | smṛti nibandha, commentary, prose-heavy bhāṣya, kārikā-heavy work |
| Citation form | full verse, half, single pāda, three-pāda, split halves, pratīka, authorial verse |
| Boundary type | exact word, exact inside token, fused/absorbed, paragraph/page cross |
| Detector family | anchored A1/A2/A3, free B, retrieval R-A, paired macro |
| Search regime | default vs exhaustive oracle (small), chunked vs whole, high-density adversarial |
| Retrieval | off, reference-seen, reference-withheld; no hidden switch |
| Annotation | verified, ambiguous, silver, unscorable; *only verified scorable headline* |

### 27.2 Release blockers

A milestone may not be marked complete if any of the following holds: **unsafe offsets; untraceable synthesized characters; unverified enabled metre grammar; skipped-test counted as pass; data leakage; inflated confidence; unmatched chunk seams; unreported candidate caps; missing gold-negative denominator; or FP budget exceeded**.

Primary publication metrics: candidate recall before scoring; exact span F1 for resolvable boundaries; fused-boundary quality for unresolvable ones; verse intrusion/over-extension; FP events and precision at FP budget; partial recall; calibration conditional on deployment slice. All denominators and confidence intervals must be reported even when results are poor.

### 27.3 Practical execution order

1. **M0 prerequisite: data contract (internally called M0.5, not a new sequential milestone):** inspect actual cleaner outputs and implement an adapter; if absent, make synthetic fixtures explicitly labelled and stop before claiming compatibility.
2. **M1 surface scanner:** finish source origin tracing and the context-free phonological attributes; prove OFF-7…12 on sandhi and Unicode counterexamples.
3. **M2 strict śloka detector:** start with verified pathyā on T + hard prose negatives; use bitmask **only as prefilter** and full gate for final proof.
4. **M2.5 vipulā variants:** enable one at a time with primary reference, external oracle, positive and near-negative examples; never default-enable all.
5. **M3 citation frames and partials:** introduce genuine fused quote transitions only after typed boundary model passes; split-pair bonus zero until paired macro oracle passes.
6. **M4+** classical registry and optional mātrā tracks; only after manuscript/work-level data demonstrates recall benefit with FP cost acceptable.
7. **M5–M7** local OCR noise, external reference alignment, blinded evaluation, review, calibration, integrated corpus export.

---

## 28. External verification notes (not claims of experimental accuracy)

- Classical śloka common/vipulā constraints: [DHARMA prosody patterns](https://dharmalekha.info/prosody); [published discussion of vaktra/anuṣṭubh variants](https://dlbs.liberal.ntu.edu.tw/en/search/search_detail.jsp?seq=632685); [Ollett's metre notes](https://columbia.edu/~aso2101/meters/index.html). The **individual vipulā predicates still require checked examples** for the selected Sanskrit corpus/profile.
- Gaṇa expansion and independently stated fixed metres: [Learn Sanskrit Online — Gaṇas](https://www.learnsanskrit.org/prosody/ganas/); [RKMVERI chandas tutorial](https://cs.rkmvu.ac.in/~tamal/learn/sanskrit/Tutorials/22-chandas.html).
- Āryā half-count and sixth-gaṇa distinctions: [Ollett, Sanskrit and Prakrit meters](https://columbia.edu/~aso2101/meters/index.html).
- Sandhi reconstruction is not identical to source slicing; model separately, as illustrated by [Sanskrit Sandhi Splitting using seq2(seq)^2](https://arxiv.org/abs/1801.00428).

**Evidence limitations:** the above publications establish general rules and motivate representation choices. They do **not** validate this algorithm's OCR robustness, false-positive rate, execution speed or proposed numerical thresholds; all such figures remain targets pending released code and a frozen human-verified benchmark.


---

## 29. Cleaner data contract (M0.5) — attested against `clean_sanskrit_corpus.py` v3.1 (see §49)

The adapter in `padya/loader.py` targets this contract. In v7 it is **verified against the actual producer**: `clean_sanskrit_corpus.py` v3.1, SHA-256 `66e09ba8761205b50bf27f77171592454dc34d57941b15baf7a3fb1698501cf4`, was executed on a fixture covering every record kind and its emitted files are reproduced in §49 (`cleaner_receipt_v3.1.json`). The verifier (§47.2) re-checks the receipt's offsets and, when the cleaner file is present, its hash. The adapter still fails closed on any unrecognised offset convention and labels synthetic fixtures as synthetic; a newer cleaner version requires a new receipt.

### 29.1 Files

| file | content |
|---|---|
| `<folder>/cleaned_devanagari/<rel>` | UTF-8, `\n` line endings, text ends with exactly one `\n`, paragraphs separated by one blank line, runs of 3+ newlines collapsed to 2. Devanagari with accents kept unless `strip_accents` was on. |
| `<folder>/cleaned_records/<rel>.jsonl` | one JSON object per line, sorted by `(start, end)`; offsets are Python `str` indices into the **cleaned Devanagari file content** (including its final newline), 0-based, end-exclusive. |
| `<folder>/cleaned_slp1/<rel>` | SLP1 copy with accents removed. **Not detector input** (SV-9 derives its own view with spans). |
| `<folder>/cleaned_devanagari/manifest.json` (also in the other two folders) | provenance, see 29.3 |
| `<folder>/cleaned_report.json` | per-file statistics, see 29.4 |

### 29.2 Record kinds

```json
{"kind": "flag", "cls": "orphan_matra|double_virama|virama_then_matra|latin_in_word|long_unspaced_run", "start": int, "end": int}
{"kind": "vedic", "start": int, "end": int, "marks": int}        # one accented WORD (maximal non-space run)
{"kind": "verse_number", "start": int, "end": int, "number": str} # start/end cover the DIGITS only, not the dandas
```

Adapter mapping to §4.2: `flag` → SV-8 (phonological classes = first four; `long_unspaced_run` is typographic); `vedic` → SV-5 (merge rule applied by the detector, not the cleaner); `verse_number` → SV-4 (the surrounding `॥ … ॥` are found by SV-1 at `start−k` / `end+k` after whitespace).

Producer facts confirmed from the v3.1 source (v7):
- a `vedic` record is one maximal **non-whitespace** run containing at least one mark in `U+0951–U+0954`, `U+1CD0–U+1CFF`, `U+A8E0–U+A8F2`, `U+A8F5–U+A8FF`; it can therefore include an attached daṇḍa, digit or quote mark, which SV-5 strips before merging;
- `verse_number` matches `[।॥] ws* digits([.-]digits)* ws* [।॥]` only; `start/end` cover the digits; numerals without a daṇḍa on both sides are not recorded (SV-4 fallback);
- `orphan_matra` is emitted only for a mātrā that could not be re-attached: the cleaner first joins `consonant + space + mātrā` (L0-3.2), so the flag means "mātrā after a non-consonant";
- `double_virama` covers both virāmas (`end − start = 2`); `latin_in_word` covers the Latin run **and** its two flanking Devanagari characters; `long_unspaced_run` covers the whole run (≥ 40 Devanagari code points);
- records are computed on the text **after** all Layer 0 rules (and after Layer 2 if `reading_view` was on, which the adapter refuses anyway); flags are counted into `noise_per_1000` on the Layer 0 text before any Layer 2 change.

### 29.3 `manifest.json` keys

```
cleaner_version ("3.0"), source_folder, source_tier ("T"|"P"|"R"|"unspecified"), generated_at,
options: {slp1, reading_view, strip_accents, sandhi_join, records}, files (int),
offsets_refer_to ("cleaned_devanagari text (Python str indices, 0-based, end exclusive)"), output
```

### 29.4 `cleaned_report.json`

`files[]` entries carry `rel_path, success, error, orig_chars, clean_chars, encoding, counts{…}, noise_per_1000`. `noise_per_1000` = (orphan_matra + double_virama + virama_then_matra + latin_in_word + foreign_script_removed + pua_removed + replacement_char) per 1,000 akṣaras (consonant + independent-vowel count), **per file**. This is the unit §5.5 uses. v3.1 adds the count key `nonsanskrit_vowel_fixed` (L0-3.9); it is informational and not part of the noise score. The full key set emitted for the receipt fixture is listed in §49.

### 29.5 Adapter validations (fail closed)

| check | action |
|---|---|
| `offsets_refer_to` differs from the expected string | error |
| `options.reading_view == true` | **refuse**: Layer 2 output joins words and is not detection input |
| `options.strip_accents == true` | warn: no `vedic` records can exist; SV-5 has nothing to exclude; tier-R Vedic quotations will reach the gate |
| `options.sandhi_join == true` | note in run manifest: some word boundaries after dead consonants were closed; C-1/C-3 slightly weaker |
| record offsets outside `[0, len(text)]` or unsorted | error |
| `verse_number.number` not all digits (Devanagari or ASCII, with `.`/`-`) | warn, keep as D2 evidence only |
| file missing from report | `noise_per_1000 = None` → tier default budget, no bands |
| text hash differs between runs with the same cleaner manifest | error (source changed under the annotations) |

---

## 30. Stage interface contracts

All frozen dataclasses (`slots=True, frozen=True`); `src` fields are `Span` in code points.

```python
class ScanView:      # stage 2
    doc: Document
    tokens: tuple[Token, ...]          # Token(kind: "D1"|"D2"|"LS"|"PS"|"VN"|"PB", src: Span, conf: float, payload)
    excluded: tuple[Span, ...]         # SV-5 merged spans
    lang_runs: tuple[LangRun, ...]     # LangRun(src, label, conf)
    analysis: AnalysisView             # slp1: str; edges: tuple[AlignEdge, ...]  (OFF-1/OFF-9)
                                       # AlignEdge(slp: Span, src: Span, rule_id: str)   either side may be empty

class AksharaStream: # stage 3
    doc_id: str; aksharas: tuple[Akshara, ...]
    barriers: tuple[int, ...]          # akṣara indices where eligible runs end (DP-2)
    runs: tuple[Span, ...]             # eligible akṣara-index runs

class ScansionPath:  # local alternative parse (PH-7)
    path_id: str; slots: tuple[int, ...]; weights: str; edits: tuple[EditEvent, ...]; cost: float

class Candidate:     # stage 4 → 5
    cand_id: str                       # hash(s, e, metre_id, variant_id, path_id)
    s: int; e: int                     # akṣara indices, end exclusive
    metre_id: str; variant_id: str | None; k: int
    origin: Literal["anchored", "free", "retrieval"]; tier_rule: str
    path: ScansionPath
    gate: GateResult                   # ok, cost, alignment: tuple[tuple[int,int],...], pada_slots, edits
    frame: FrameMatch | None           # opener/closer matches with src spans and fused flags
    pair_id: str | None                # A5

class ScoredArc:     # stage 7 → 8
    arc_id: str; s: int; e: int; score: float; kind: Literal["verse", "pair"]
    components: tuple[Candidate, ...]  # one for verse, two for pair
    gaps: tuple[Span, ...]             # akṣara ranges annotated prose inside a pair envelope
    features: tuple[tuple[str, float], ...]

class DecodeResult:  # stage 8
    accepted: tuple[ScoredArc, ...]; log_Z: float
    arc_posterior: dict[str, float]; span_marginal: dict[tuple[int,int], float]
    p_prose: tuple[float, ...]         # per akṣara, DP-5 semantics
    margins: dict[str, float]; search_incomplete: bool; counters: dict[str, int]

class Region:        # stage 10
    src: Span; label: str; syllables: Span | None; p_verse_mean: float | None; alternatives: tuple[str, ...]
```

Every stage exposes `run(input, config: Config) -> Output` and a `version()` string folded into `config_sha256`.

---

## 31. Boundary sandhi inventory and attachment policy

Used by F-5 (fused openers), SC-12 (fused closers), SC-10 (junctions) and `BoundaryAnchor.transformation`. The table is finite; the agent implements it as data (`config/sandhi_boundary.yaml`), not as general sandhi.

### 31.1 Verse-end + closer (`… + इति / इत्यादि / इत्युक्तेः …`)

| verse-final | surface | transformation id | what is shared |
|---|---|---|---|
| `-म्` | `-मिति` | `m+i→mi` | grapheme `मि`: consonant belongs to verse, vowel to closer |
| `-त्` / `-द्` | `-दिति` | `t+i→di` | grapheme `दि` (and the voicing is surface-only) |
| `-न्` | `-निति` | `n+i→ni` | grapheme `नि` |
| `-ः` after a/ā | `-अ इति` / `- इति` (visarga dropped) | `aH+i→a·i` | nothing shared; visarga has **no surface** — reconstruction only |
| `-ः` after i/u/e/ai/o/au | `-रिति` | `iH+i→ri` | grapheme `रि`: `र्` reconstructs the visarga, `इ` is the closer |
| `-ा` / `-अ` | `-ेति` | `a+i→e` | grapheme `-े`: one vowel realises two underlying vowels → `shared_surface` |
| `-ि` / `-ी` | `-ीति` | `i+i→I` | grapheme shared |
| `-ु` / `-ू` | `-्विति` | `u+i→vi` | `व्` belongs to verse (as glide), `इ` to closer |
| `-े` | `-इति` with hiatus or `-यिति` (rare) | `e+i→a·i` / `e+i→ayi` | hiatus: exact boundary; `ayi`: `य्` shared |
| `-ो` | `-विति` (rare) | `o+i→avi` | `व्` shared |

### 31.2 Opener + verse-start (`… मनुः / यथाह / उक्तं च + verse`)

| opener-final + verse-initial | surface | transformation id |
|---|---|---|
| `-ः` + `अ` (nominative + a-) | `-ोऽ` | `aH+a→o'` — avagraha marks the elided verse vowel; boundary `shared_surface`, verse cover begins at the consonant after `ऽ`, `reconstructed_reading` restores `अ` |
| `-ः` + other vowel | `-र` + vowel (after non-a) or visarga dropped (after a) | `iH+V→rV` / `aH+V→a·V` |
| `-ः` + voiced consonant | `-ो` + C (after a) | `aH+C→oC` — exact boundary, no sharing |
| `-ा` / `-अ` + `अ` / `आ` | `-ा` + | `a+a→A` — one `ा` realises both: `shared_surface`; verse's initial vowel has no surface (`यथाहाष्टौ`) |
| `-अ` + `इ` / `ई` | `-े` | `a+i→e` |
| `-अ` + `उ` / `ऊ` | `-ो` | `a+u→o` |
| `-अ` + `ऋ` | `-र्` | `a+f→ar` |
| `-अ` + `ए` / `ऐ` | `-ै` | `a+e→E` |
| `-अ` + `ओ` / `औ` | `-ौ` | `a+o→O` |
| `-ं` + vowel | `-म` + vowel | `M+V→mV` — exact boundary after `म्`'s consonant? no: the `म` grapheme carries the verse vowel → `inside_grapheme` |
| `-च` (उक्तं च) + `अ` | `-चा` | `a+a→A` |
| `-इति` as opener (इति + verse) | `इत्य-` | `i+V→yV` |

### 31.3 Attachment policy (normative; closes the gap in OFF-10)

1. A grapheme shared between verse and frame is attached to the **verse's** `observed_cover` (so the verse text never loses a consonant that is metrically its own), and the boundary is recorded `inside_grapheme` with `covering_src` = that grapheme.
2. When the verse's own vowel has **no surface** (`a+a→A` at the start, `aH+i` at the end), the boundary is `shared_surface`, `offset = null`, the grapheme is attached to whichever side the *consonant* belongs to, and `reconstructed_reading` supplies the underlying form.
3. `frame_overlap` records the frame text as it survives (`इति`, `-ति`, `ऽ`), its `covering_src`, and the transformation id.
4. `regions.jsonl` surface partition follows the same attachment, so no code point is in two regions.
5. Metrics: an exact-offset score is computed only for boundaries gold marks `exact_between_codepoints`; `inside_grapheme` and `shared_surface` boundaries are scored on `(covering_src, transformation)` agreement (DATA-6).

---

## 32. Configuration files — seeds

### 32.1 `config/weights.yaml` (all *initial* values in one place)

```yaml
version: 1
prose_model:
  alpha_lex: 0.25
  shibboleth_penalty: -2.5
metre_prior:            # log P(m)
  anustubh: 0.0
  upajati: -2.2
  vasantatilaka: -2.5
  shardulavikridita: -2.8
  default_vrtta: -3.5
  arya: -3.0
partial_prior:          # log P(k | m), before frame/retrieval lift
  k4: 0.0
  k2: -1.2
  k3: -3.2
  k1: -4.0
variant_prior:          # anustubh odd pādas
  pathya: 0.0
  na_vipula: -2.5
  bha_vipula: -2.8
  ma_vipula: -2.8
  ra_vipula: -3.5
  ta_vipula: -4.2
  hypermetric9: -3.0
edits:
  lambda_edit: 1.6
  cost_uncertain: 0.5
  cost_sc10_split: 0.15
  cost_sc11_lenient: 0.20
frames:
  w_open: 2.0
  w_open_punct: 2.8
  w_close: 2.0
  w_synergy: 1.2
  ellipsis_lift_to: 0.0
retrieval:
  w_ret: 4.5
  shingle_overlap_min: 0.50
  shingle_consecutive_pratika: 3
  max_norm_edit_distance: 0.12
  distinctiveness_penalty_per_extra_occurrence: -0.8
cues:
  c1_soft_start: -1.0
  c1_inside_word: -2.5
  c2_end_word: 0.6
  c2_end_midword: -2.0
  c3_all_padas: 1.2
  c3_per_pada: 0.3
  c4_yati: 0.5
  c5_start_token: 1.2
  c6_end_token: 1.8
  c7_verse_number: 3.5
  c8_cross_d2: -3.0
  b3_cross_d1_offpada: -1.5
  b3_cross_ps_T: -1.5
  b3_cross_ps_PR: -0.3
decoder:
  nu_start: -1.0
  pair_bonus: 1.5
  pair_max_gap_words: 8
uncertain:
  p_low: 0.35
  p_high: 0.65
  min_run_syllables: 8
  near_miss_score: -2.0
language:
  non_sa_prior: -3.0
caps:
  candidates_per_1k_syllables: 400
  pair_arcs_per_1k_syllables: 20
  parse_alternatives_per_window: 4
tiers:
  T: {budget32: 0.0, indels32: 0, pada_cap: 0}
  P_lo: {budget32: 1.0, indels32: 0, pada_cap: 1, noise_max: 5}
  P_hi: {budget32: 2.0, indels32: 1, pada_cap: 1}
  R_lo: {budget32: 1.5, indels32: 1, pada_cap: 1, noise_max: 5}
  R_mid: {budget32: 2.5, indels32: 2, pada_cap: 1, noise_max: 20}
  R_unprocessable_noise: 20
```

### 32.2 `config/metres.yaml` entry schema

```yaml
- id: vasantatilaka
  display: Vasantatilakā
  class: sama              # sama | ardhasama | visama | jati | grammar
  syllables_per_pada: 14
  gana_tokens: [ta, bha, ja, ja, ga, ga]
  pattern: GGLGLLLGLLGLGG       # must equal expand(gana_tokens); compiler asserts
  final_anceps: true
  yati: []
  aliases: [simhonnata, uddharsini]
  verification_status: needs_verification   # verified | needs_verification | blocked
  primary_reference: "Vṛttaratnākara 3.x"
  second_reference: "chanda 0.x"
  verified_by: null
  fixtures: {positive: [], negative: []}
```

Grammar metres (`anustubh`) and jāti metres point to a module (`grammar: padya.metres.anustubh`) instead of `pattern`.

### 32.3 `config/frames.yaml` seed

```yaml
openers:
  single_authority:
    patterns: ["{AUTH_NOM}", "{AUTH_NOM} आह", "{AUTH_NOM} उवाच", "{AUTH_NOM}ऽपि", "तथा च {AUTH_NOM}", "अत्र {AUTH_NOM}", "यदाह {AUTH_NOM}", "यथाह {AUTH_NOM}", "उक्तं च {AUTH_INS}", "{AUTH_LOC}"]
  multi_hop:
    patterns: ["{DIGEST_LOC} {AUTH_NOM}", "{DIGEST_LOC} {AUTH_LOC}"]
  anonymous:
    literals: ["अत्र श्लोकाः", "तत्र श्लोकः", "अत्र श्लोकः", "संग्रहश्लोकः", "कारिका च", "वृद्धवाक्यम्", "अत्रोदाहरन्ति", "यथोक्तम्", "स्मृतिश्च", "उक्तं च", "उक्तं हि", "तदुक्तम्", "तदाह", "यथाह", "यदाह", "स्मृत्यन्तरे", "पुराणान्तरे", "पुराणे", "भारते", "गीतासु"]
  typographic:
    endings: ["ः", "ौ", "े", "षु"]
    marks: ["—", ":-", "-", "‘", "“"]
  fused:  # F-5: opener stem + sandhi outcome, see §31.2
    - {stem: "यथाह", surface: "यथाहा", transformation: "a+a→A"}
    - {stem: "उक्तं च", surface: "उक्तं चा", transformation: "a+a→A"}
    - {stem: "आह", surface: "आहा", transformation: "a+a→A"}
    - {stem: "इति", surface: "इत्य", transformation: "i+V→yV"}
closers:
  quotative: ["इति", "इति च"]
  ellipsis: ["इत्यादि", "इत्यादिना", "इत्युपक्रम्य", "इत्यन्तेन", "इत्यादिग्रन्थः"]
  causal: ["इति वचनात्", "इति स्मृतेः", "इति स्मरणात्", "इति निषेधात्", "इति श्रुतेः", "इत्युक्तेः", "इति दर्शनात्", "इत्युक्तत्वात्"]
  structural: ["’", "”", "{VERSE_NUMBER}"]
  fused_suffixes: ["मिति", "दिति", "निति", "रिति", "ेति", "ीति", "्विति"]   # SC-12 / §31.1
split_bridges: ["उत्तरार्धं तु", "उत्तरार्धम्", "अस्यार्थः", "इत्यर्धेन", "पूर्वार्धे", "उत्तरार्धे"]
shibboleths: ["इति चेन्न", "अत्रोच्यते", "तन्न", "ननु", "वाच्यम्", "व्याख्येयम्", "प्रकृतम्", "इत्यर्थः", "इति भावः", "इति चेत्"]
```

### 32.4 `config/authorities.yaml` seed

Each authority lists explicit surface forms (nominative, instrumental, locative, `-ऽपि` forms) because the matcher does not inflect.

```yaml
smrti:
  manu:        {canonical: "मनुः", forms: ["मनुः", "मनुना", "मनौ", "मनुरपि", "मनुश्च", "मानवे"]}
  yajnavalkya: {canonical: "याज्ञवल्क्यः", forms: ["याज्ञवल्क्यः", "याज्ञवल्क्येन", "याज्ञवल्क्ये", "याज्ञवल्क्योऽपि"]}
  parasara:    {canonical: "पराशरः", forms: ["पराशरः", "पराशरेण", "पराशरे", "पराशरोऽपि"]}
  vyasa:       {canonical: "व्यासः", forms: ["व्यासः", "व्यासेन", "व्यासे", "व्यासोऽपि"]}
  yama:        {canonical: "यमः", forms: ["यमः", "यमेन", "यमे", "यमोऽपि"]}
  satatapa:    {canonical: "शातातपः", forms: ["शातातपः", "शातातपेन", "शातातपे"]}
  brhaspati:   {canonical: "बृहस्पतिः", forms: ["बृहस्पतिः", "बृहस्पतिना", "बृहस्पतौ", "बृहस्पतिरपि"]}
  katyayana:   {canonical: "कात्यायनः", forms: ["कात्यायनः", "कात्यायनेन", "कात्यायने", "कात्यायनोऽपि"]}
  harita:      {canonical: "हारीतः", forms: ["हारीतः", "हारीतेन", "हारीते"]}
  devala:      {canonical: "देवलः", forms: ["देवलः", "देवलेन", "देवले"]}
  angiras:     {canonical: "अङ्गिराः", forms: ["अङ्गिराः", "अङ्गिरसा", "अङ्गिरसि"]}
  visnu:       {canonical: "विष्णुः", forms: ["विष्णुः", "विष्णुना", "विष्णौ"]}
  narada:      {canonical: "नारदः", forms: ["नारदः", "नारदेन", "नारदे"]}
  samvarta:    {canonical: "संवर्तः", forms: ["संवर्तः", "संवर्तेन", "संवर्ते"]}
  atri:        {canonical: "अत्रिः", forms: ["अत्रिः", "अत्रिणा", "अत्रौ"]}
  daksa:       {canonical: "दक्षः", forms: ["दक्षः", "दक्षेण", "दक्षे"]}
  gautama:     {canonical: "गौतमः", forms: ["गौतमः", "गौतमेन", "गौतमे"]}
  apastamba:   {canonical: "आपस्तम्बः", forms: ["आपस्तम्बः", "आपस्तम्बेन", "आपस्तम्बे"]}
  vasistha:    {canonical: "वसिष्ठः", forms: ["वसिष्ठः", "वसिष्ठेन", "वसिष्ठे"]}
  baudhayana:  {canonical: "बौधायनः", forms: ["बौधायनः", "बौधायनेन", "बौधायने"]}
  sankha_likhita: {canonical: "शङ्खलिखितौ", forms: ["शङ्खलिखितौ", "शङ्खलिखिताभ्याम्", "शङ्खः", "लिखितः"]}
purana:
  bhavisya: {canonical: "भविष्यपुराणम्", forms: ["भविष्ये", "भविष्यपुराणे", "भविष्योत्तरे"]}
  skanda:   {canonical: "स्कन्दपुराणम्", forms: ["स्कान्दे", "स्कन्दपुराणे"]}
  garuda:   {canonical: "गरुडपुराणम्", forms: ["गारुडे", "गरुडपुराणे"]}
  matsya:   {canonical: "मत्स्यपुराणम्", forms: ["मात्स्ये", "मत्स्यपुराणे"]}
  padma:    {canonical: "पद्मपुराणम्", forms: ["पाद्मे", "पद्मपुराणे"]}
  brahma:   {canonical: "ब्रह्मपुराणम्", forms: ["ब्राह्मे", "ब्रह्मपुराणे"]}
  markandeya: {canonical: "मार्कण्डेयपुराणम्", forms: ["मार्कण्डेये", "मार्कण्डेयः"]}
digest:   # via_digest when in locative before a primary
  hemadri:        {canonical: "हेमाद्रिः", forms: ["हेमाद्रौ", "हेमाद्रिः"]}
  madhaviya:      {canonical: "पराशरमाधवीयम्", forms: ["माधवीये", "माधवः", "माधवमते"]}
  mitaksara:      {canonical: "मिताक्षरा", forms: ["मिताक्षरायाम्"]}
  smrticandrika:  {canonical: "स्मृतिचन्द्रिका", forms: ["स्मृतिचन्द्रिकायाम्"]}
  kaladarsa:      {canonical: "कालादर्शः", forms: ["कालादर्शे"]}
  madanaratna:    {canonical: "मदनरत्नम्", forms: ["मदनरत्ने"]}
  ratnakara:      {canonical: "कृत्यरत्नाकरः", forms: ["रत्नाकरे"]}
  kaustubha:      {canonical: "कौस्तुभः", forms: ["कौस्तुभे"]}
  nirnayamrta:    {canonical: "निर्णयामृतम्", forms: ["निर्णयामृते"]}
  dipika:         {canonical: "दीपिका", forms: ["दीपिकायाम्", "दीपिकोक्तेः"]}
  divodasa:       {canonical: "दिवोदासः", forms: ["दिवोदासः", "दिवोदासेन", "दिवोदासोदाहृत"]}
```

The seed was taken from the Nirṇayasindhu passage supplied by the owner (हेमाद्रौ भविष्ये, माधवीये, स्कान्दे, निर्णयामृते, दीपिकोक्तेः, दिवोदासः, पराशरः, बृहस्पतिः, मार्कण्डेयः, विष्णुपुराणे) and must be extended from the gold set.

---

## 33. Prose language models and language classifier — implementation spec

### 33.1 Character model `P_prose^char`, `P_verse^char`
- Order 5, interpolated Kneser-Ney, absolute discount 0.75 (*initial*), over SLP1 characters with space and a sentinel for D1/D2. Vocabulary = SLP1 alphabet + space + sentinel + `<unk>`; no OOV at the character level, `<unk>` for anything else.
- Training: `tools/build_prose_lm.py` reads adjudicated prose paragraphs (train split), writes `data/models/prose_char5.npz` (counts as numpy arrays; no pickle of code). Verse model trained on gold verse text of the train split.
- Scoring: `log P(c) / n_chars` normalised, so spans of different length are comparable; the scorer multiplies back by syllable count for the final LLR (PR-3).
- Acceptance: held-out perplexity reported; prose model perplexity on verse must exceed its perplexity on prose by a margin (sanity), else the split leaked.

### 33.2 Rhythm model `P_prose^LG`
- Order 8 over `{L, G}`; `?` syllables are scored by marginalising both values. Same smoothing. Trained on the L/G stream of the prose paragraphs.
- `log P(LG | m)` for a metre is `0` for an exact match and `−λ_edit · cost` otherwise — i.e. the gate's cost is the only edit charge (PR-3); the prose rhythm model supplies the denominator.

### 33.3 Language classifier (SV-6)
- Multinomial naive Bayes over character 5-grams per paragraph; classes `sa, hi, mr, other`; uniform priors; decision only if `P(label) ≥ 0.8`, else `sa` with `conf = P(sa)`.
- Nukta count per paragraph (from the cleaner's counts, if propagated) is an additional feature for `hi/mr`.
- Off until M4; when on, its only effect is `S_lang` (§8.1) — never exclusion.

---

## 34. Error taxonomy for milestone reports

Every one of the "20 worst errors" is tagged with exactly one primary code, so reports are comparable across milestones.

| code | name | definition |
|---|---|---|
| E01 | candidate miss | gold span never generated as a candidate (reported against OBJ-2 candidate recall) |
| E02 | gate reject | candidate generated, failed the gate; sub-tag `metre_rule`, `budget`, `variant_blocked` |
| E03 | lost to prose | passed gate, `S(c) ≤ 0` |
| E04 | lost to competitor | positive score, overlapped by a better-scoring wrong span |
| E05 | over-extension | accepted span = gold + neighbouring prose (OBJ-3) |
| E06 | under-extension | accepted span ⊂ gold |
| E07 | boundary fused | gold boundary `shared_surface`/`inside_grapheme`, predicted exact (or vice versa) |
| E08 | wrong metre / variant | span right, label wrong |
| E09 | wrong pāda split | span right, pādas wrong |
| E10 | prose FP – accidental metre | FP with no frame; sub-tag by candidate family |
| E11 | prose FP – frame-induced | FP adjacent to an opener/closer |
| E12 | OCR-induced | FP or FN attributable to an edit event or `?` |
| E13 | excluded/non-Sanskrit leakage | accepted span intersects an excluded or non-`sa` region |
| E14 | attribution error | span right, authority wrong/missing |
| E15 | retrieval error | wrong source match or missed pratīka |
| E16 | partial-class error | half/pāda/three/pratīka label wrong |

---

## 35. Fixture file format (`tests/fixtures/T01…T22`)

```yaml
id: T03
title: half-verse with ellipsis closer
tier: T
profile: classical_strict
features: {sc10: false, sc11: false, retrieval: off, language: off}
text: |
  तथा च मनुः अयं निजः परो वेति गणना लघुचेतसाम् इत्यादि । ततः परं निर्णयः ।
expect:
  verses:
    - observed_cover: [11, 44]              # code points into `text` exactly as written above (verified)
      partial: half
      metre_id: anustubh
      padas: [[11, 28], [29, 44]]
      end_boundary: {resolution: exact_between_codepoints}
      trimmed_closer: "इत्यादि"
      attribution: {raw: "मनुः", primary_authority: "मनुः"}
  no_verse_in: [[55, 72]]                   # must contain no accepted span
  regions_partition: true
  allow_uncertain: false
```

The harness recomputes offsets from `text` at load time and fails if the YAML offsets do not match the stated substrings (`expect.verses[i].text_check`, optional). Fixtures T12 include a non-BMP character; T18 is generated, not stored.

---

## 36. Minimum viable path and deferral list

The full specification is large. To reach a first real number quickly and avoid building machinery before it is needed:

**Build first (M0 → M2, pathyā only):** loader + adapter (§29), SV-1/4/5/7/8/9, SC-0…9, bitmask pre-filter + full grammar check for pathyā-only anuṣṭubh, Tier A1–A3, Tier B for anuṣṭubh with `k ∈ {2, 4}` only, `P_prose^LG` only (no char model yet), cues C-2/C-3/C-5/C-6/C-7, scorer with `ν_start`, single-arc Viterbi + FB, `verses.jsonl` + `regions.jsonl`, metrics, NEG classes 1–3. Run on T-punct and T-stripped. **This yields the first FP/1k and recall numbers and decides whether the prose rhythm model alone separates verse from prose.**

**Defer until the M2 number exists:**

| item | defer because |
|---|---|
| paired macro arcs (DP-1…) | needs A5 cases from gold P; single arcs suffice for T |
| phonological parse alternatives (PH-1/2, ScansionPath) | tier T is deterministic; alternatives matter only at fused boundaries and OCR |
| SC-10, SC-11, AN-9, ta-vipulā, Āryā, Vaitālīya | each needs its own fixtures and measured frequency |
| language classifier | T texts are monolingual |
| retrieval index | depends on owner-supplied corpus; also a leakage risk during tuning |
| calibration | needs dev data from M3+ |
| review.html | useful from M3 when P-tier annotation starts |
| chunking (OPS-7/8) | only needed once a full book is run (M7); prove with T09 then |

**Critical path:** §29 adapter → SV-9 spans (OFF tests) → scanner gold → pathyā gate → T-stripped number. Everything else hangs off that number.

---

## 37. Gold and review schemas

### 37.1 `data/gold/detect/<tier>/<doc_id>.jsonl`

```json
{"gold_id": "ns-p1:g0042", "doc_id": "ns-p1", "source_sha256": "…",
 "observed_cover": [48213, 48339],
 "start_boundary": {"resolution": "exact_between_codepoints", "offset": 48213},
 "end_boundary": {"resolution": "inside_grapheme", "covering_src": [48337, 48339], "transformation": "m+i→mi"},
 "padas": [[48213,48240],[48241,48268],[48270,48299],[48300,48339]],
 "metre": "anustubh", "variant": ["pathya","pathya","pathya","pathya"],
 "partial": "full", "quotation_type": "cited",
 "attribution": {"raw": "तथा च मनुः", "primary_authority": "manu", "via_digest": null},
 "source": {"work": "manusmrti", "locator": "..."},
 "status": "verified", "annotators": ["A", "B"], "adjudicated_by": "owner", "notes": ""}
{"gold_id": "ns-p1:n0007", "doc_id": "ns-p1", "kind": "negative_prose", "observed_cover": [51000, 51400], "neg_class": 3, "status": "verified"}
```

### 37.2 `review_decisions.jsonl`

```json
{"event_id": "…", "run_id": "…", "doc_id": "…", "target": "verse:<id>|region:<id>|candidate:<id>",
 "action": "accept|reject|adjust_span|adjust_pada|mark_partial|mark_authorial|resolve_attribution|uncertain",
 "prior": {...}, "new": {...}, "reviewer": "…", "ts": "…", "detector_version": "…", "reason": "…"}
```

Replay (`tools/replay_reviews.py`) converts accepted/adjusted events into gold records with `status: verified` and the reviewer as annotator, never touching frozen test files (QC-5).

---

## 38. Glossary (for the agent)

| term | meaning here |
|---|---|
| akṣara | written syllable unit; here, one vowel nucleus with its onset consonants |
| laghu (L) / guru (G) | light / heavy syllable; 1 / 2 mātrās |
| mātrā | mora; the unit of jāti metres |
| pāda | quarter-verse; 8 syllables in anuṣṭubh |
| ardhaśloka | half-verse: pādas 1–2 or 3–4 |
| anceps (X) | position where L or G is allowed (pāda end) |
| gaṇa | three-syllable group (ma ya ra sa ta ja bha na) or, in jāti, a 4-mātrā group |
| yati | caesura inside a pāda, expected at a word boundary |
| vipulā | permitted deviations of the odd pādas of anuṣṭubh |
| sama / ardhasama / viṣama-vṛtta | metres with identical / alternating / four different pādas |
| jāti | mātrā-counted metres (Āryā family, Vaitālīya) |
| pratīka | citation by first words only (`… इत्यादि`) |
| ekādeśa | sandhi coalescence of two vowels into one |
| avagraha (ऽ) | sign marking an elided initial a- |
| sandhi | phonological fusion at word junctions; obligatory inside a hemistich |
| nibandha | digest of smṛti quotations with commentary (Nirṇayasindhu, Dharmasindhu) |
| kārikā / saṃgraha-śloka | a commentator's own summary verse (authorial, not a quotation) |
| ṭīkā | commentary; in some editions in Hindi/Marathi in the same script |
| daṇḍa (। ॥) | punctuation marking half-verse / verse end, or sentence end in prose |
| svara | Vedic accent marks; their presence identifies a Vedic quotation |


---

## 39. V6 product contract: what counts as a verse (DET-1…DET-12)

These definitions are **normative** when earlier descriptions are ambiguous. They separate *meter*, *span*, and *editorial intent* so the model cannot classify a prose sentence as a quotation merely because a 32-syllable window matches a pattern.

| object | definition | product decision |
|---|---|---|
| observed span | code-point cover on immutable Devanāgarī text; exact observed letters may include sandhi-shared graphemes | always serialised verbatim |
| metrical span | a sequence of phonological slots consistent with a named, verified classical metre | a candidate, not proof of intentional verse |
| verse event | text **presented as a verse** by context or sustained structure; includes authorial kārikā | emitted only after decoder + operating threshold |
| citation event | a verse event supported as quotation by a frame or independent textual match | attribution is a separate claim |
| incidental metrical prose | syntactically prose, though a chance metrical window passes | hard negative; never marked as positive merely from meter |
| unresolved span | plausible but insufficient evidence to assert a verse | review-only, counted as abstention |
| partial verse | observed single pāda, half, three-pāda or pratīka | requires external evidence as in AN-7/A6 |

- **DET-1** Primary label = `verse_event | prose | uncertain | excluded | unprocessable`; `metrical_form`, `intent`, `quotation_type`, `source_attribution` are separate dimensions. `non_sanskrit` remains a region label, not an automatic Vedic inference.
- **DET-2** A detected verse is *not necessarily a quotation*. `quotation_type=authorial|cited|unknown` may be unknown even for a high-confidence metrical event.
- **DET-3** If a word contains both an opener and a quote start, preserve the entire observed token plus `BoundaryAnchor`; a reconstruction is optional and always tagged hypothetical.
- **DET-4** Negative prose can contain an identical known śloka as part of a *discussion of its words*. Annotate the actual editorial presentation. In blind test, explain disputed cases with an adjudication code; mere retrieval identity is not enough.
- **DET-5** The detector is **not** a language-model rewriting or text-correction tool. OCR event records are diagnostics, not suggested silent substitutions.
- **DET-6** Treat line breaks, daṇḍas and verse numbers as *soft or strong evidence* according to tier; none alone settles versehood.
- **DET-7** For a full free Anuṣṭubh candidate, accept only if **both hemistichs and all four pādas pass** a verified grammar. Without structural/retrieval support, an isolated half stays in review unless a strict dev-set operating point shows acceptable FP.
- **DET-8** Preserve candidate discovery failures distinctly from scorer refusals; only the former require widening windows/anchors.
- **DET-9** Every source span belongs to exactly one **surface** region; phonological hypotheses may share source graphemes, but regions may not overlap.
- **DET-10** If gold intent is genuinely ambiguous, store `ambiguous` with adjudication notes. Never force it to prose or verse merely to simplify a denominator.
- **DET-11** The unit of correctness is a *span event*, not merely the label of a sentence. An accepted span that absorbs neighbouring prose is erroneous even if most of it is metrical.
- **DET-12** The release-level claim must name its enabled grammar profile, source tier, set of text genres and citation classes. A pathyā-only detector must not claim exhaustive Sanskrit śloka coverage.

**Precedence rule:** `DET-*`, then `OFF/PH/DP`, then earlier stage shorthand. For conflicts, record the exact conflict and regression fixture; do not silently choose a permissive reading.

## 40. V6 fast baseline and progressive detection (BASE-1…BASE-12)

### 40.1 Why an explicit baseline is necessary

The extensive v5 architecture should not conceal whether metrical structure alone gives sufficient separation from prose. **BASE-A** is a deterministic, punctuation-aware but punctuation-independent pathyā detector; **BASE-B** adds measured contextual evidence; **BASE-C** adds optional complex recovery. Every layer has an ablation, so the eventual system is not a black box.

| build | enabled | excluded | acceptance evidence |
|---|---|---|---|
| **BASE-A** | immutable loader, syllabifier, strict pathyā grammar, all-window full 32-slot search at eligible starts, DP, fixed transparent start penalty | retrieval, char LM, OCR edits, vipulās, fused sandhi restoration, language model | candidate recall; FPs on reviewed *unmarked* prose; T-punct and T-stripped scores |
| **BASE-B** | anchored chunks, opener/closer frames, end/word-boundary cues, train-only prose-LG model, dev-tuned threshold | optical corrections and external bibliography | delta exact-F1 and delta FP/1k, with error-by-cue waterfall |
| **BASE-C** | variant grammars one at a time, optional half spans, local phonological alternatives, scored retrieval | Vedic meter; unverified metres | independent feature ablations; no metric regression outside declared tolerance |

- **BASE-1** `baseline_mode={A,B,C}` maps to a **versioned frozen configuration**, never a mutable alias to the latest weights.
- **BASE-2** Candidate generation enumerates 32-slot pathyā windows and, when enabled, validated 16-slot halves at hard/soft word starts. A bounded *phrase-anchored* inside-word expansion is separate, measured under `BASE-C`.
- **BASE-3** Scan once and cache **intrinsic** phonological features; recompute closure/anceps for each candidate parse. Do not construct final L/G by concatenating independently scanned words when consonantal context crosses words.
- **BASE-4** For OCR tiers, the fast mask is a necessary-condition filter only. The complete grammar, parse consistency and uncertainty cost must be applied afterward.
- **BASE-5** Strong anchored detection can save work only with a proved second-pass recovery of overlapping conflict zones. `deferred ≠ rejected`.
- **BASE-6** The scorer uses a feature record containing boolean `evidence_present`, numerical evidence values, and model-version hashes. Missing retrieval or unavailable prose LM is *not* a zero-confidence assertion; it is an absent feature.
- **BASE-7** Predefine candidate-family budgets: free full, anchored full, anchored half, retrieval-supported partial and prose-negative region. Different families may require different operating thresholds, fitted on dev and frozen.
- **BASE-8** Zero externally supported partials must be accepted under `BASE-A`; this is deliberate precision-first behaviour, not a test failure.
- **BASE-9** Supply a `--no-models` deterministic mode for a full offline baseline even when `.npz` models are unavailable.
- **BASE-10** Before adding char language models, compare against a simpler held-out logistic baseline on explicit features to avoid unnecessary Kneser–Ney complexity. Retain Kneser–Ney as an **optional experiment**, not a prerequisite to the first number.
- **BASE-11** Emit a `candidate_recall` report *before* tuning scores; include `not_enumerated`, `failed_gate`, `lost_score`, and `lost_overlap` counts.
- **BASE-12** A nonzero metrical match alone is not evidence that a full verse was intentionally quoted. A no-frame, unmarked candidate needs a separately calibrated *free-candidate* rule whose FP exposure was evaluated on sufficient hard prose.

### 40.2 Core pseudocode: baseline full-śloka candidate

```python
# Contract sketch, not implementation code; scores are only after the full gate.
def propose_pathya_candidates(document, analysis, profile):
    for start in eligible_start_anchors(analysis, profile):
        for path in bounded_local_parses(analysis, start, max_alternatives=1):
            end = path.end_after_syllables(32)
            if end is None or path.crosses_barrier(start, end):
                continue
            if cheap_mask_lower_bound(path, start, end) > 0:
                continue  # fixed-length exact-T mode only
            scan = verify_all_four_padas(path, start, end, profile)
            if scan.ok:
                yield Candidate(span=path.observed_cover(start, end),
                                slots=(start, end), metre='anustubh',
                                grammar='classical_strict_pathya',
                                alignment=scan.trace,
                                source_hash=document.text_sha256)
```

**Important:** a successful candidate is *not yet an emitted verse*. Scoring, global conflict resolution, and a frozen operating threshold are subsequent steps.

## 41. Formal boundary and source-coordinate contract (EDGE-1…EDGE-11)

The v5 `BoundaryAnchor` design is retained. The source projection needs one further distinction: **a surface cover is always an interval, whereas the true boundary may be a relation**, not a numeric index.

```python
@dataclass(frozen=True, slots=True)
class OriginEdge:
    src: Span | None          # none = hypothetical/zero-input analysis operation
    analysis: Span | None     # none = omitted source punctuation/tombstone
    rule_id: str
    kind: Literal['copy','expand','contract','zero_src','zero_analysis']

@dataclass(frozen=True, slots=True)
class BoundaryHypothesis:
    resolution: Literal['exact_between_codepoints','inside_grapheme',
                        'shared_surface','unresolved']
    offset: int | None       # permitted iff resolution is exact
    covering_src: Span | None
    split_analysis_slot: int | None
    parse_id: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class CandidateGeometry:
    observed_cover: Span
    start_boundary: BoundaryHypothesis
    end_boundary: BoundaryHypothesis
    phonological_slot_span: Span
    origin_edge_ids: tuple[int, ...]
```

- **EDGE-1** Valid exact offsets are code-point boundaries **and Unicode extended-grapheme boundaries**. Test with `regex` `\X` (pinned version), not Python's code-point slicing alone.
- **EDGE-2** `offset is None` for every `inside_grapheme`, `shared_surface`, or `unresolved` anchor; the covering source span and analysis slot may still locate it unambiguously enough for review.
- **EDGE-3** Origin edges are monotone with respect to analysis order except explicit zero-length fusion edges; unusual reorderings demand a typed exception and fail-closed validation.
- **EDGE-4** Every analysis vowel slot has at least one origin edge **or an explicit hypothesis event** (`OCR_INFERRED_VOWEL`, `SANDHI_RESTORATION`). Zero-source analysis is never silently emitted as observed text.
- **EDGE-5** Every source character not emitted as an analysis phoneme must still have a tombstone, separator, or preserved source-view attachment.
- **EDGE-6** `observed_cover.start/end` are valid source offsets and `Document.text[cover]` exactly equals `surface_text`. If the surface cover includes a shared opener character, tag it; do not claim it is exclusively part of the verse.
- **EDGE-7** `verse_padas[].surface_cover` may intersect at **shared graphemes**, but the chapter's source-region partition follows one deterministic attachment policy and never double-counts characters.
- **EDGE-8** In a fused opener `यथाहाष्टौ` the surface may not contain the independently written first `अ` of the reconstructed verse. Report `shared_surface` with evidence; never claim `start` points before a nonexistent code point.
- **EDGE-9** Source offsets are anchored against a **SHA-256 of the full source bytes** and its Unicode decoding policy; no implicit newline stripping, normalization, or generated reflow.
- **EDGE-10** Coordinate conversion to UTF-16 and byte positions is an *explicit derived index*. Validate conversions against non-BMP and combining-mark fixtures at both boundaries.
- **EDGE-11** When OCR alignment is irreparably ambiguous, set `resolution='unresolved'`, keep the source cover, and exclude only that boundary from exact-offset metrics; do not exclude the entire verse from all recall reporting.

**Consistency refinement:** in v5 §31.3, "attach the shared grapheme to the verse" is a **region-allocation convention**, not a claim about ownership of that grapheme's phonology. Preserve `frame_overlap` independent of the region label.

## 42. Detection scoring and decoder proof obligations (DEC-11…DEC-23)

The existing DP-1…DP-10 remains normative. v6 supplies the missing invariants that distinguish *candidate existence*, *global path selection*, and *calibration*.

### 42.1 Unified arc protocol

```python
@dataclass(frozen=True, slots=True)
class VerseArc:
    start_slot: int
    end_slot: int
    candidate_id: str
    score: float
    verse_covers: tuple[Span, ...]      # length 1 for ordinary candidate
    prose_gap_covers: tuple[Span, ...]  # paired macros only
    feature_hash: str
```

- **DEC-11** `start_slot < end_slot`, positive-length accepted `verse_covers`, sorted covers, no internal overlap and no crossing an excluded/barrier edge.
- **DEC-12** Prose arcs cover every eligible slot. Candidate arcs are optional competitors; their score is a *discriminative energy*. A path is not a probability until its partition function is calculated.
- **DEC-13** A paired macro covers an interval envelope in decoding, contains **exactly two verse covers**, and assigns its interior gap explicitly to prose. The gap may **not** contain an independently selected verse arc while the macro is chosen. This limitation must be evaluated; the safer default is *post-decode relation-only linking* with zero selection bonus.
- **DEC-14** `lattice_posterior(c)` is for a *specific arc*. Event probability for a surface span is the **sum of disjoint chosen-arc alternatives** or a precisely defined union over compatible paths—not a sum of scores or a naively duplicated alias.
- **DEC-15** For any slot `i`, `P(prose_i)+P(verse_i)=1` within the eligible two-label sublattice. For macro arcs, compute the prose contribution from interior gap annotations; do not use only `P(edge i→i+1)`.
- **DEC-16** Confidence on a full emitted verse is nullable when search is incomplete, candidate family is out of calibration support, a primary grammar is unverified, or input tier is outside training.
- **DEC-17** `search_incomplete` must be a **surface-local reason** with a score-independent risk code; no artificially high posterior to compensate for truncated candidates.
- **DEC-18** A single source-cover candidate may have several verified metre/parse explanations. Keep a canonical **event** key and a separate explanation table so synonymous labels do not inflate event mass. If two real alternative parses exist, their probabilities reflect distinct hypotheses rather than copied evidence.
- **DEC-19** The scorer must not use a test-data reference match to raise the score in a reference-withheld evaluation, even transiently before a later filter.
- **DEC-20** The dynamic program is verified against exhaustive path enumeration for all generated small cases (including paired arcs), **not just manually chosen examples**. Check Viterbi score, all legal path totals, `logZ`, arc and slot marginals.
- **DEC-21** The observed surface partition is reconstructed **after** decoded metrical events using EDGE attachment policy; never assume one analysis slot maps to exactly one code-point interval.
- **DEC-22** `uncertain` is an explicit review action and reporting policy. It must not be treated as another undifferentiated prose arc whose inclusion silently improves F1.
- **DEC-23** Priors and cue weights are empirical *potentials*. `log P(m)` naming is retained for backward configuration compatibility but v6 reports them as `metre_log_weight` unless an actual normalised probability distribution is fitted. Do not add per-syllable average log-likelihoods and per-event log-weights without a documented exposure correction.

### 42.2 Partition sanity checks

For a single-arc-only DAG with arcs `(s,e,w)` and prose edges `(i,i+1,0)`, define

\[
\alpha(e) = \operatorname{LSE}_{(s,e,w)}[\alpha(s)+w], \qquad
\beta(s) = \operatorname{LSE}_{(s,e,w)}[w+\beta(e)].
\]

The complete arc set includes the prose edge at every eligible step. Then `Z=α(N)=β(0)` and `P(arc)=exp(α(s)+w+β(e)-Z)` on that exact DAG. For a paired macro, the same formula applies to the **envelope arc**; its interior prose/verse labelling is inspected for slot-state marginals. Two path alternatives that produce the *same observed verse event* must be canonicalized or modelled as explicit latent explanations with an event-level union calculation.

**Do not conflate** `P(arc ∈ decoded path)` with `P(detector prediction is correct)`. Calibrating the latter requires independent, fully reviewed data.

## 43. Candidate pruning, edit budgets, and search completeness (SRCH-1…SRCH-12)

- **SRCH-1** A bitmask reject is admissible **only** when its cost is a proven lower bound for *all allowed parses* of the segment. With indels or fused-sandhi alternatives, fall back to the banded lower-bound oracle, not the exact-string popcount.
- **SRCH-2** A zero Hamming mismatch does not settle pre-cadence restrictions, pāda boundary, yati, uncertain syllables, or edit budget; always run the full verified grammar.
- **SRCH-3** Precompile *verified* fixed metres into masks, grouped by pāda length; compile the true constraints separately for Anuṣṭubh and mātrā metres.
- **SRCH-4** Candidate-generation caps must be observable: report `starts_attempted`, `starts_skipped`, `parse_branches_created/pruned`, `candidate_count`, and `cap_hit_regions` per page or 1,000 syllables.
- **SRCH-5** For every cap-hit region, emit `search_incomplete=true` and a review region, **without** setting `unprocessable` unless the underlying source is itself too corrupt for segmentation.
- **SRCH-6** The default path is zero-edit and zero-fusion. Every OCR edit consumes a separate, typed budget; sandhi licences are not OCR repairs and must not be charged as such.
- **SRCH-7** A one-edit improvement in a window is not enough to emit a verse: require metrical validation *and* the scorer's threshold relative to the best no-edit/prose alternative.
- **SRCH-8** Local noise is estimated from source flags with a minimum denominator and smoothed file-level fallback. The smoothing recipe and thresholds are versioned; missing flags do not imply clean OCR.
- **SRCH-9** Very noisy material is isolated by page or short region; good neighbouring pages remain scorable. Reserve `unprocessable` for genuinely unsound source analysis, not a search budget hit.
- **SRCH-10** In long unspaced Sanskrit runs, candidate starts may be extended only under a **documented capped mode**. Report candidate recall and false positives before and after; do not silently enable unrestricted every-syllable starts.
- **SRCH-11** Chunked and whole-document candidate sets must be equal **modulo sorted canonical IDs** for every test ≤ a declared maximum span/context range; equality of only accepted verses is insufficient.
- **SRCH-12** Both re-scoring and Viterbi must use **global source-relative feature offsets and the same frozen model** after chunk reconciliation; do not average independent chunk posteriors.

## 44. Confidence, score calibration and abstention (CAL6-1…CAL6-11)

### 44.1 Three distinct numbers

| field | interpretation | permitted claim |
|---|---|---|
| `raw_score` | additive potential for a specific candidate/arc | model ranking only |
| `lattice_posterior` | conditional marginal under the **generated graph** | competition/ambiguity diagnostic |
| `calibrated_probability` | empirically estimated correctness frequency for an **emitted event** in its deployment stratum | reliability statement only after held-out calibration |

- **CAL6-1** Calibration data must include *all detector nominations* in the annotated sample, not just accepted/high-scoring ones; otherwise precision is inflated by selection bias.
- **CAL6-2** Train and calibration/test data are separated by underlying work and edition family. Do not reuse repeated quotations across partitions as independent negatives or positives without disclosed retrieval regimes.
- **CAL6-3** Calibrate the **event** label `exact_correct`, `overlap_correct`, or `boundary_correct` separately. A probability for "contains some verse" is not a probability for "correct exact endpoints."
- **CAL6-4** Isotonic is allowed only when the calibration set is large and covers score/tier/family ranges; otherwise use regularized logistic/Platt or set `uncalibrated`.
- **CAL6-5** Evaluate Brier, reliability diagram, ECE (with published binning), log loss and precision–coverage. Report per tier and family; report small-sample uncertainty.
- **CAL6-6** A **target FP/1,000 prose words** is a rate constraint, not a calibrated probability threshold. Freeze the threshold on dev and evaluate only once on blind test.
- **CAL6-7** Preserve score and completeness even on OOD candidates, but `confidence_status='ood'`, `calibrated_probability=null`; high raw score cannot override this.
- **CAL6-8** A sparse lattice posterior is conditional on the candidate generation policy. Larger search can lower its value without making the Sanskrit less metrical; do not compare across candidate caps as if it were a stable probability.
- **CAL6-9** Release decisions use one of `accepted_strict | accepted_review | uncertain | rejected`, with threshold bundle id and evidence-coverage status.
- **CAL6-10** If no candidate family has enough verified gold negatives, leave that family **review-only** rather than arbitrarily loosening the threshold.
- **CAL6-11** Explicitly distinguish `incomplete_search` from `unprocessable_source` and `ood_model` in confidence and region reason codes. Only the former may be resolved by a larger search budget.

### 44.2 Zero false positives does not mean zero risk

If a blind test produces **0 false positives** among `W` reviewed prose words, an approximate one-sided Poisson 95% upper bound on the *event* rate per 1,000 words is

\[
1000\cdot\frac{-\ln(0.05)}{W} \approx \frac{2996}{W}.
\]

Example: 0 false positives across 30,000 adjudicated prose words permits an upper bound of about **0.10 FP per 1,000 words**, **only if the sampling design supports a Poisson/exposure assumption**. Correlated quotations and clustered works demand blocked/bootstrap uncertainty and held-out-work replication. This rule does **not** replace the actual FP numerator or sufficient prose coverage.

## 45. Gold corpus design and no-leak evaluation (EVAL6-1…EVAL6-14)

### 45.1 Four annotation pools

1. **Blind continuous-text pool:** random complete pages/paragraphs sampled *before running the detector*, fully reviewed for verses and prose. It supplies an unbiased missed-verse audit and a genuine FP denominator.
2. **Positive-enriched pool:** verified full, half and difficult quotation examples. It estimates recall by class, but **not** unweighted field prevalence.
3. **Hard-negative pool:** expertly labelled accidental metre, pure śāstra prose, unquoted citation frames and typographic confusions. It tests discriminative resilience, but **not** the natural FP prevalence.
4. **Perturbation pool:** the same passages with punctuation removed, OCR variants or page splits, retaining a monotone projection map. These are paired sensitivity cases, not independent observations.

- **EVAL6-1** Underlying work, chapter, editorial edition, OCR generation and all transformed views form one `source_family_id`; no family crosses train/dev/test.
- **EVAL6-2** All headline results use **human-reviewed, contiguous** material sampled independently of the detector's nominations. Enriched examples are separate strata with weights or explicit caveats.
- **EVAL6-3** The prose denominator counts verified prose **word tokens** under a frozen word-tokenization rule. Hyphen and fused-word handling is documented; include `unknown_word_count` for uncertain regions.
- **EVAL6-4** A prediction's entire span is a true positive only under the declared matching regime (exact, ±1 syllable, or IoU threshold). Every unmatched prediction is an FP in event precision, even if it touches gold; also report `FP_zero_overlap` separately for the classical prose-exposure rate.
- **EVAL6-5** Use deterministic **one-to-one maximum-weight bipartite matching** by overlap with explicit tie breakers for TP/FP/FN, not a greedy many-to-one match. Gold and prediction spans may never each be credited twice.
- **EVAL6-6** `FP_zero_overlap / 1000 prose words` remains the historical metric; introduce `FP_all_unmatched / 1000 prose words` and `prose_intrusion_chars` to expose merged/overextended predictions.
- **EVAL6-7** For partials and `pratīka`, report subtype precision/recall separately; an isolated 8-syllable segment can be a metrical pāda without being confidently presented as a quotation.
- **EVAL6-8** For fused boundaries, use a second scorer for `(resolution, covering grapheme, phonological_slot)`. Do not back-convert a shared-surface label to a fictitious exact source position.
- **EVAL6-9** Silver-derived T-stripped spans can develop and debug code; final T-stripped results need a **blinded audit** of the stripped version, independent of its original punctuation.
- **EVAL6-10** Duplicated or near-duplicated classical quotations in different works create reference leakage. Publish retrieval-off, retrieval-allowed, and reference-work-withheld results.
- **EVAL6-11** Keep strict and review thresholds frozen; any changes after viewing test errors create a new evaluation version and new blind test.
- **EVAL6-12** Report the sample frame: works, editions, chapters, how paragraphs were selected, percentage of unmarked verse, and the unreviewed remainder. Never infer deployment FP/1k from a hard-negative-only set.
- **EVAL6-13** Primary CIs resample *works/chapters*, not isolated syllables. With very few works, show per-work results and admit the CI is unstable.
- **EVAL6-14** Report absolute counts and denominator for each metric; a target such as `exact_F1 ≥ 0.87` remains aspirational until a frozen blind test demonstrates it.

### 45.2 One-to-one span scoring

```python
# Evaluation sketch: compare source-relative predicted/gold covers.
# Scorable gold and predicted events are matched at most once.
# Construct all eligible edges (for exact, relaxed or IoU metric),
# then choose a deterministic maximum-weight bipartite assignment.
# Unmatched prediction => FP; unmatched gold => FN.
# Publish every count and the exact matching criterion.
```

**Important:** Surface geometry and editor intent are not interchangeable. Exact offset evaluation applies only to exact-resolvable spans; all observed verses remain part of the intent/detection recall report under their own boundary-resolution classes.

## 46. Retrieval, frames and split quotations without circular evidence (LINK6-1…LINK6-11)

- **LINK6-1** Frames are **context evidence**, not text for the metrical syllable count. If punctuation or `इति` coalesces, use a typed local parse (SC-12) instead of deleting characters until 32 syllables appear.
- **LINK6-2** Retrieval hit scores need a separate `retrieval_similarity_score` and `source_attribution_probability` (if calibrated). The latter can remain null even when matching text is found.
- **LINK6-3** A reference hit should identify a **work+edition+locator** and its normalization/rights provenance; "Manu" alone is not a source locator.
- **LINK6-4** Reference matches cannot create source characters missing after OCR or sandhi. Aligned but nonidentical readings are reported as variant correspondences, with edit/coverage statistics.
- **LINK6-5** Stock formulae (`इति`, `तथा च`, common half-lines) receive inverse-document-frequency penalties and minimum-distinctive-content rules, which are validated against known negative contexts.
- **LINK6-6** A citation frame and a reference match may derive from the **same** editor's repeated attribution. Do not count this as two statistically independent proofs; include a joint-feature interaction learned on dev.
- **LINK6-7** Fused-opener discovery uses a finite verified sandhi table; a successful frame match is not permission for arbitrary word-internal segmentation.
- **LINK6-8** Split-half association is, by default, a **post-decoding relation** with zero selection bonus. It can connect detected halves without altering which spans are selected.
- **LINK6-9** If paired macros are enabled, the joint arc occupies its envelope, correctly labels the prose gap and is verified against exhaustive small-case enumeration (DP-9/DEC-20). Document the cost of forbidding another independent verse in its gap.
- **LINK6-10** Underlying authorial kārikās and cited verses are both detected as verse events, but the citation graph is populated only when attribution evidence supports it.
- **LINK6-11** `pratika_unresolved` belongs in the review queue; do not emit it into the accepted verse inventory as if it were a complete verse span.

## 47. V6 machine-checkable specification and adversarial fixtures (TEST6-1…TEST6-14)

### 47.1 Required additional cases

| id | input family | assertion |
|---|---|---|
| **T31** | free pathyā vs same-length prose with one forbidden opening | passes only the metrical example; prose remains undecided/rejected |
| **T32** | rare vipulā with wrong caesura | blocked under strict profile, or explicitly uncertain; no silent pathyā fallback |
| **T33** | unknown weight `?` at an otherwise exact fixed-template slot | full gate incurs configured uncertainty cost; bitmask zero cannot accept for free |
| **T34** | fused opener and fused closer sharing grapheme(s) | origin edges valid; `offset=null` for unresolvable boundary; surface partition total |
| **T35** | punctuation-stripped T passage and its annotated original | both stay in the same split; projection monotone; no silver headline metric |
| **T36** | zero true FPs in very small prose sample | report positive uncertainty upper bound; never claim perfect specificity |
| **T37** | two overlapping predictions for one gold span | one-to-one matcher credits at most one TP, remaining prediction an FP |
| **T38** | candidate alias duplicates | deduplicated explanation does not increase event posterior |
| **T39** | macro pair with internal prose and optional competing verse | gap is prose; competing path handled deterministically; oracle matches DP |
| **T40** | same source under whole-file and chunked scanning | canonical candidates, exact selected spans and scores are equal |
| **T41** | candidate cap triggered on clean but unspaced text | `search_incomplete`, not `unprocessable_source`, and null calibration |
| **T42** | reference-withheld versus reference-enabled run | no withheld text enters candidate features in the former; scores explain delta |

### 47.2 Structural validators for the blueprint itself

The repository must include `tools/verify_spec.py` — seeded by the shipped `verify_verse_detector_v7.py` (§50.2) — which checks: (1) unique rule IDs within normative definition rows; (2) all YAML seeds parse; (3) all fixed-metre `n` and gaṇa expansions match; (4) disabled metres cannot leak into the active registry; (5) fixture source hash/offsets agree; (6) all code fences are balanced; (7) no unavailable companion file is implied as validated without a receipt/hash; (8) CLI option names and enum strings exist in the schema; (9) each active rule has at least one corresponding test; (10) no two tunable numerical constants have conflicting definitions across the base spec and actual config. A verification failure blocks claims about code readiness, **not** use of the document for planning.

- **TEST6-1** A `gold` fixture must include a `source_sha256` matching the exact UTF-8 source bytes; source offsets refer to decoded Unicode code points under the declared newline policy.
- **TEST6-2** Every `pāda` span is valid and monotone in its own coordinate system; sharing is explicit only in analysis alignment, never hidden source overlap.
- **TEST6-3** Fixture regex/Devanāgarī and manually entered metrical labels must be reconciled by independent adjudication. Example `lg_full` in §13.1 is **not** gold merely because its length is 32.
- **TEST6-4** Compile each gaṇa formula with the verified alphabet `ya=LGG, ma=GGG, ta=GGL, ra=GLG, ja=LGL, bha=GLL, na=LLL, sa=LLG, la=L, ga=G`.
- **TEST6-5** For a fixed template, `len(expand(formula))=declared_n=len(pattern)`; for a grammar or multi-template metre, use dedicated validators.
- **TEST6-6** The fast gate and an exhaustive slow gate agree for random 8–16-slot inputs in exact zero-edit mode; then expand to bounded edited 32-slot fixtures.
- **TEST6-7** For all DAGs ≤ 12 eligible slots, brute-force Viterbi/logZ/marginal comparison must pass (including macros after they are enabled).
- **TEST6-8** Randomized Unicode text does not crash the adapter; unsupported mapping fails with a typed error, never character deletion.
- **TEST6-9** The complete source-region partition is reconstructible as `[0,len(Document.text))`, including zero-syllable punctuation.
- **TEST6-10** All derived source token ids and output region ids remain stable across fresh-process reruns; timestamps/run IDs are excluded from deterministic equality.
- **TEST6-11** A deliberately corrupt metadata hash, edition mismatch or out-of-range record fails closed without a partial success artifact.
- **TEST6-12** A test marked `skipped/xfail` is explicitly reported and never credited as successful acceptance.
- **TEST6-13** All matched gold/predicted span pairs are unique; FP numerator is independently reproducible.
- **TEST6-14** `version` fields, run manifest, model hashes, grammar profile and threshold bundle are present in every benchmark.

### 47.3 Minimal acceptance command sequence for an implementation agent

```bash
# Commands are specified target CLI, not a claim that this implementation exists.
verse-detect selftest
verse-detect dry-run DATASET_DIR
verse-detect run DATASET_DIR --profile classical_strict --no-retrieval --out OUT_DIR
verse-detect evaluate --gold GOLD_DIR --split dev --out REPORT_DIR
verse-detect benchmark DATASET_DIR --out REPORT_DIR/benchmark.json
```

Do not assert command success until the corresponding program and fixtures exist and have actually run. `--no-models` and `--no-retrieval` must be supported explicitly or rejected with a documented error, never ignored silently.

## 48. V6 release gates, priorities, and unresolved inputs (REL6-1…REL6-12)

### 48.1 Scoped shipping levels

| level | product guarantee | minimum validation |
|---|---|---|
| **Developer alpha** | deterministic pathyā candidate spans for hand inspection | loader/offset invariants; candidate-recall and first blind prose-negative baseline; no precision claim |
| **Reviewer beta** | ranked verse regions with visible uncertainty and provenance | frozen evaluation split, full-region review UI, calibrated event confidence if enough dev data; FP/1k and errors published |
| **Corpus production** | versioned stand-off annotations usable as Granthanidhi citation input | per-tier/work blind tests, audited source-coordinate mapping, reproducible run manifest, regression suite, review correction path |

- **REL6-1** M0/M0.5 must validate **real emitted cleaner files**, not a guessed manifest copied from §29. If unavailable, produce a synthetic-only adapter and stop short of compatibility claims.
- **REL6-2** M1 scanner correctness is a prerequisite; downstream score tuning cannot compensate for invalid SLP1/source correspondence.
- **REL6-3** M2 should report pathyā-only *candidate recall* and field FP before any vipulā experiment. Unverified variants remain off.
- **REL6-4** A failed blind-test target does not authorize changing thresholds and reusing the same test as blind. Freeze a new holdout family.
- **REL6-5** Named metres in §5.3 require both gaṇa mechanical equality and philological evidence; mechanical equality alone does not establish metre correctness.
- **REL6-6** A higher recall accompanied by higher uncontrolled prose FP is not automatically an improvement. Report the recall–FP frontier for every feature gate.
- **REL6-7** Retrieval is a separately licensed and benchmarked optional module; no external text is implicitly bundled.
- **REL6-8** No agent or tool may fabricate a test result, performance measurement, primary-source attestation or companion-program hash.
- **REL6-9** Before production, compare at least a simple transparent feature scorer, an optional prose-LG model and the full scored pipeline; retain the smallest reproducibly superior model.
- **REL6-10** Every accepted detection includes parse profile and feature availability; `confidence_status` uses the canonical machine enum from §20/§44.
- **REL6-11** A run lacking a reviewed negative denominator may still be called a *candidate extraction*, never a validated verse detector.
- **REL6-12** Report release blockers in machine-readable JSON and stop on source-integrity defects, unverified enabled grammar, unknown coordinate conventions, test leakage or incomplete search represented as certainty.

### 48.2 Still-needed external inputs, without blocking basic implementation

| input | blocks what | safe default |
|---|---|---|
| ~~Actual `clean_sanskrit_corpus.py`~~ **supplied: v3.1, receipt in §49** | — | adapter built against the receipt; a new cleaner version needs a new receipt |
| `normalisation_spec_v2.md` (rule rationale; not needed for compatibility) | nothing in the build; informs L0-rule tests | proceed |
| Human-verified mixed prose/verse gold | claims about recall, FP and calibration | unit fixtures and unscored review queue |
| Primary metre-text verification for optional vipulās and full registry | enabling those grammars | pathyā-only strict profile |
| Licence-reviewed reference texts | citation retrieval | disabled |
| VTF schema | VTF export | JSONL stand-off output |

**Final engineering priority:** complete `M0 + M0.5 + M1 + BASE-A/M2` first; publish the first honest *T-stripped, no-retrieval* detection report. Only then spend effort on complex Sanskrit sandhi, citation linking, OCR tolerance, exotic metres or large neural models.


---

## 49. Integration receipt — cleaner v3.1 (v7)

Generated by running the actual producer on a fixture that exercises every record kind. The receipt file `cleaner_receipt_v3.1.json` is shipped with this blueprint; `verify_verse_detector_v7.py` re-validates it.

| item | value |
|---|---|
| cleaner file | `clean_sanskrit_corpus.py`, version string `3.1` |
| cleaner SHA-256 | `66e09ba8761205b50bf27f77171592454dc34d57941b15baf7a3fb1698501cf4` |
| cleaner self-test | `SELFTEST: PASSED` (Python 3.13.16) |
| fixture source SHA-256 | `940ff1a218c830eab4415234c3f31e7a3e496ec526061dbddf427175f0c4529c` |
| cleaned text SHA-256 | `7ebd2248014d819eca28b6746cf1e13049df81aad1c2309bf87ea3c67684e35f` |
| `manifest.offsets_refer_to` | `cleaned_devanagari text (Python str indices, 0-based, end exclusive)` |
| manifest keys | `cleaner_version, files, generated_at, offsets_refer_to, options, output, source_folder, source_tier` |
| manifest options | `{"slp1": true, "reading_view": false, "strip_accents": false, "sandhi_join": true, "records": true}` |
| report per-file fields | `clean_chars, counts, encoding, error, noise_per_1000, orig_chars, rel_path, success` |
| report count keys (this fixture) | `accents_present, detached_matra, flag_double_virama, flag_latin_in_word, flag_long_unspaced_run, flag_orphan_matra, flag_virama_then_matra, hyphen_not_joined, latin_s_to_avagraha, pipes_to_danda, records_written, slp1_accents_removed, slp1_stray_virama` |
| `noise_per_1000` (this fixture) | `13.7` |
| all record offsets reproduce their slices | `True` |

Fixture as cleaned (exact file content; the final newline is part of the offset space):

```text
तथा च मनुः अयं निजः परो वेति गणना लघुचेतसाम् इत्यादि । ततः परं निर्णयः ।
अ॑ग्निꣳ ई॒ळे पुरो॑हितं यज्ञस्य देवमृत्विजम् । होतारं रत्नधातमम् ॥ १ ॥

का ख्् ग । सोऽब्रवीत् ॥ २ ॥
```

Emitted `cleaned_records/fixture.txt.jsonl`:

```json
[
 {
  "kind": "vedic",
  "start": 73,
  "end": 80,
  "marks": 1
 },
 {
  "kind": "vedic",
  "start": 81,
  "end": 85,
  "marks": 1
 },
 {
  "kind": "vedic",
  "start": 86,
  "end": 95,
  "marks": 1
 },
 {
  "kind": "verse_number",
  "start": 139,
  "end": 140,
  "number": "१"
 },
 {
  "kind": "flag",
  "cls": "double_virama",
  "start": 148,
  "end": 150
 },
 {
  "kind": "verse_number",
  "start": 168,
  "end": 169,
  "number": "२"
 }
]
```

What the fixture demonstrates: the three accented words become three `vedic` records (the detector's SV-5 merges them); `॥ १ ॥` and `॥ २ ॥` become `verse_number` records whose offsets cover only the digit; `क ा` was re-attached to `का` by L0-3.2 so no `orphan_matra` flag exists; `ख््` yields one `double_virama` flag of length 2; `|` became `।`; `सो S ब्रवीत्` became `सोऽब्रवीत्`. The `noise_per_1000` of 13.7 on this tiny fixture illustrates why §5.5 bands are per file with a minimum denominator (SRCH-8), not per sentence.

**Receipt policy (REC-1…REC-4).**
- **REC-1** A receipt binds one cleaner SHA-256 to one record schema. The adapter stores the receipt's hash and compares it with the cleaner named in `manifest.cleaner_version`; a mismatch is a warning in dev and an error in `--strict`.
- **REC-2** Any change to the cleaner's record kinds, offset convention or manifest keys requires a new receipt and a schema version bump in the adapter.
- **REC-3** The receipt is generated by a script, never hand-edited; `verify_verse_detector_v7.py` recomputes every offset check from the receipt's own text.
- **REC-4** A receipt demonstrates the producer's **format**; it is not evidence about detector accuracy.

---

## 50. v7 reconciliation ledger and verifier

### 50.1 Ledger

| tension | governing reading in v7 |
|---|---|
| v6 §29 "schema expectation" vs v5 "verified against source" | verified, by receipt (§49); REL6-1 satisfied for v3.1 only |
| DEC-23 (no mixing of per-syllable averages with per-event weights) vs §33.1 per-syllable normalisation | §33.1 describes model storage; `S(c)` uses totals; `ν_start` is the sole exposure term (§8.1, v7 note) |
| `confidence_status` enum spellings (`OOD` in prose, `ood` in enum) | enum is canonical: `uncalibrated \| calibrated \| ood \| incomplete_search`; prose may say OOD |
| v5 §31.3 "attach shared grapheme to the verse" vs EDGE-7/§41 | attachment is a region-allocation convention; `frame_overlap` records the phonological sharing independently (as §41 already states) |
| A5 pair bonus (v5) vs LINK6-8 zero bonus default | zero selection bonus by default; macro arcs only after DEC-20/T39 pass |
| M2 "pathyā + verified vipulās" (v5) vs M2 pathyā-only (v6) | pathyā-only; vipulās enter one at a time in M2.5 |
| §12 fixture range (T01–T22 in v5, T01–T42 in v6) | T01–T42; the verifier checks all 42 labels are present |
| `verse_number` detection (cleaner) vs numerals without flanking daṇḍas | SV-4 fallback tokenises them at reduced confidence; numerals never enter the syllable stream |
| `orphan_matra` meaning | "mātrā with no consonant to attach to" (cleaner re-attaches the common case first) |
| SC-11 *muta cum liquida* | still **ASK**; T32-style near-negatives required before any enablement |
| Performance figures anywhere in the text | targets; none measured |

### 50.2 Verifier

`verify_verse_detector_v7.py` (shipped) checks, offline: version string; §39–§50 each present once; balanced code fences; all fixed-metre rows expand from their gaṇa formulas and match declared lengths; §13.1 fixture length/hash/offsets; T03 offsets; T01–T42 labels; all four YAML seeds in §32 parse; the receipt JSON (when present) has `all_offsets_valid = true` and its offsets re-verify from its own text; when `--cleaner PATH` is given, the file's SHA-256 equals the receipt's. Output: a JSON report (`verse_detector_v7_validation.json`) and a non-zero exit on any failure. It is the seed of `tools/verify_spec.py` (§47.2) and must be extended there with the repository-level checks (rule-id ↔ test mapping, config ↔ spec constant agreement) that cannot be done from the Markdown alone.
