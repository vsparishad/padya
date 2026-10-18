"""Stage 3: akṣara scanner (§4.3, SC-0…SC-9, SV-1…SV-8, INV-5).

Attachment policy for non-syllable characters (INV-5):
* consonants before a vowel inside one orthographic word are that vowel's onset
  (written-akṣara convention); word-final dead consonants attach to the last akṣara;
* modifiers (ं ः ँ) and avagraha attach to the preceding akṣara;
* combining marks attach to the preceding character;
* spaces, punctuation, digits and daṇḍas belong to no akṣara.

`Akshara.weight` is the default surface parse (PH-7): consonant lookahead crosses
spaces but stops at daṇḍas and foreign-script barriers (SC-8). Contextual
recomputation at a candidate's end is `contextual_final_weight`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import bisect
import re

from padya.devanagari import HEAVY_MODIFIERS, LONG_VOWELS, SHORT_VOWELS
from padya.loader import PHONOLOGICAL_FLAGS, Document
from padya.phonology import AnalysisView, Item, analysis_view, tokenize
from padya.types import Span

Weight = Literal["L", "G", "?"]
DELIM_CONF = {"T": 1.0, "P": 0.95, "R": 0.90, "unspecified": 1.0}  # SV-1
VERSE_NUM_CONF = {"T": 1.0, "P": 0.75, "R": 0.70, "unspecified": 0.70}  # SV-4
VERSE_NUM_FALLBACK_FACTOR = 0.6  # SV-4 (v7): numeral next to one daṇḍa / at line end
_NUMERAL_RE = re.compile(r"[0-9\u0966-\u096f]+(?:[.\-][0-9\u0966-\u096f]+)*")
_EDITORIAL_RE = re.compile(r"\([^()\n।॥]*\)")  # one-line `( … )` group without daṇḍas
# A Latin citation siglum with its number (`[MDh 5․125]`, `ĀpDhS 1․1․1․6cd`, `cf. GDh 17․8-9`): a run of
# non-Devanagari text that starts with a Latin letter and ends in a number (plus pāda letters a–d).
_CITATION_RE = re.compile(r"(?<![\u0900-\u097f])[A-Za-z\u00c0-\u024f\u1e00-\u1eff][^\n\u0900-\u097f]{0,56}?"
                          r"[0-9]+(?:[\u2024.,:\-/][0-9]+)*[a-d]{0,2}>?")


@dataclass(slots=True, frozen=True)
class Akshara:
    idx: int
    src: Span
    slp1: str
    vowel: str
    weight: Weight
    matra: int | None  # never zero (SC-7)
    word_start: bool
    soft_start: bool
    word_end: bool
    line_start: bool
    para_start: bool
    delim_before: str | None
    delim_after: str | None
    delim_conf: float
    verse_num_after: str | None  # SV-4: numeral token right after this akṣara (C-7 evidence)
    verse_num_conf: float
    intrinsic_heavy: bool
    coda_count: int  # word-final consonants attached to this akṣara
    cons_after: int  # consonants before the next vowel (default parse)
    closed_by_pause: bool
    nasal: bool  # SC-3 candrabindu trait
    possible_parses: tuple[str, ...]
    excluded: bool
    flags: frozenset[str]


@dataclass(slots=True, frozen=True)
class AksharaStream:
    doc_id: str
    aksharas: tuple[Akshara, ...]
    runs: tuple[Span, ...]  # eligible akṣara-index runs (DP-2)
    items: tuple[Item, ...]
    analysis: AnalysisView
    orphan_chars: int  # Devanagari letters with no vowel nucleus


@dataclass(slots=True)
class _Draft:  # mutable only inside `scan`, frozen into Akshara before return
    items: list[int]
    nucleus: int
    word_start: bool = False
    soft_start: bool = False
    word_end: bool = False
    line_start: bool = False
    para_start: bool = False
    delim_before: str | None = None
    delim_after: str | None = None
    verse_num_after: str | None = None
    verse_num_conf: float = 0.0


def _group_words(items: tuple[Item, ...]) -> list[tuple[list[int], list[int]]]:
    """Return (separator item ids before the word, letter item ids) pairs."""
    words, seps, letters = [], [], []
    for i, item in enumerate(items):
        if item.kind in ("SEP", "PAUSE", "BARRIER"):
            if letters:
                words.append((seps, letters))
                seps, letters = [], []
            seps.append(i)
        else:
            letters.append(i)
    if letters:
        words.append((seps, letters))
    elif seps and words:
        words.append((seps, []))  # trailing separators (e.g. a final daṇḍa) still mark the last word
    return words


def _word_drafts(items: tuple[Item, ...], letters: list[int]) -> list[_Draft]:
    drafts: list[_Draft] = []
    pending: list[int] = []
    for i in letters:
        if items[i].kind == "V":
            drafts.append(_Draft(items=pending + [i], nucleus=i))
            pending = []
        elif items[i].kind == "C" or not drafts or pending:
            pending.append(i)  # onset of the next akṣara (keeps spans contiguous)
        else:
            drafts[-1].items.append(i)  # M or AVA attach to the preceding akṣara
    if drafts:
        drafts[-1].items.extend(pending)  # word-final consonants and marks
    return drafts


def _mark_soft_from_avagraha(drafts: list[_Draft], items: tuple[Item, ...]) -> None:
    for prev, cur in zip(drafts, drafts[1:]):
        if any(items[i].kind == "AVA" for i in prev.items):
            cur.soft_start = True


def _separator_context(items: tuple[Item, ...], seps: list[int], first: bool) -> dict:
    details = [items[i].detail for i in seps]
    kinds = [items[i].kind for i in seps]
    newlines = details.count("newline")
    hyphen_only = bool(seps) and all(d == "hyphen" for d in details)
    pauses = [items[i].detail for i in seps if items[i].kind == "PAUSE"]
    delim = None
    if pauses:
        delim = "D2" if "D2" in pauses or pauses.count("D1") >= 2 else "D1"
    return {
        "word_start": first or (bool(seps) and not hyphen_only),
        "soft_start": hyphen_only,
        "line_start": first or newlines >= 1,
        "para_start": first or newlines >= 2,
        "delim": delim,
        "barrier": "BARRIER" in kinds,
    }


def _stronger(a: str | None, b: str | None) -> str | None:
    return "D2" if "D2" in (a, b) else (a or b)


def _merge_ctx(a: dict | None, b: dict) -> dict:
    """Combine the separator contexts on both sides of a skipped fragment (strongest wins)."""
    if a is None:
        return b
    return {"word_start": a["word_start"] or b["word_start"], "soft_start": a["soft_start"] and b["soft_start"],
            "line_start": a["line_start"] or b["line_start"], "para_start": a["para_start"] or b["para_start"],
            "delim": _stronger(a["delim"], b["delim"]), "barrier": a["barrier"] or b["barrier"]}


def _lookahead(items: tuple[Item, ...]) -> dict[int, tuple[int, bool]]:
    """For each vowel item: (consonants before the next vowel, stopped by pause/end)."""
    result: dict[int, tuple[int, bool]] = {}
    count, stopped, first_cons = 0, True, ""
    for i in range(len(items) - 1, -1, -1):
        item = items[i]
        if item.kind == "V":
            # SC-13 (Pāṇini 6.1.73 che ca): छ after a vowel takes the tuk augment and
            # counts as a cluster (c-ch); a short vowel before it is therefore heavy.
            result[i] = (count + 1 if first_cons == "C" and count >= 1 else count, stopped)
            count, stopped, first_cons = 0, False, ""
        elif item.kind == "C":
            count += 1
            first_cons = item.slp1
        elif item.kind in ("PAUSE", "BARRIER"):
            count, stopped, first_cons = 0, True, ""
    return result


def _weight(vowel: str, mods: str, cons_after: int, stopped: bool, flagged: bool) -> tuple[Weight, bool]:
    """SC-0…SC-5, SC-7: return (weight, intrinsic_heavy)."""
    intrinsic = vowel in LONG_VOWELS or any(m in HEAVY_MODIFIERS for m in mods)
    if flagged or (vowel not in LONG_VOWELS and vowel not in SHORT_VOWELS):
        return "?", intrinsic
    if intrinsic or cons_after >= 2 or (cons_after >= 1 and stopped):
        return "G", intrinsic
    if "~" in mods:  # SC-3: candrabindu is not automatically anusvāra
        return "?", intrinsic
    return "L", intrinsic


def _record_labels(doc: Document) -> list[tuple[int, int, str]]:
    """(start, end, label) for flag and vedic records; label 'vedic' drives SV-5 exclusion."""
    out = []
    for r in doc.records:
        if r.kind == "flag":
            out.append((r.start, r.end, str(r.payload.get("cls", ""))))
        elif r.kind == "vedic":
            out.append((r.start, r.end, "vedic"))  # SV-5: no bridging across records
    return sorted(out)


def _project_records(spans: list[Span], records: list[tuple[int, int, str]]) -> list[frozenset[str]]:
    """Labels overlapping each akṣara span, by one ordered sweep (OPS-2; linear, not quadratic)."""
    out: list[frozenset[str]] = []
    active: list[tuple[int, int, str]] = []
    i = 0
    for span in spans:
        while i < len(records) and records[i][0] < span.end:
            active.append(records[i])
            i += 1
        active = [r for r in active if r[1] > span.start]
        out.append(frozenset(c for s, e, c in active if s < span.end))
    return out


def _verse_number_tokens(doc: Document) -> list[tuple[int, str, float]]:
    """SV-4: (offset, number, conf) from cleaner records, plus the v7 fallback for numerals
    the cleaner does not record (daṇḍa on one side only, or at a line end)."""
    base = VERSE_NUM_CONF[doc.tier]
    tokens = {r.start: (str(r.payload.get("number", "")), base) for r in doc.records if r.kind == "verse_number"}
    text = doc.text
    for m in _NUMERAL_RE.finditer(text):
        if m.start() in tokens:
            continue
        before = text[:m.start()].rstrip(" \t")
        after = text[m.end():].lstrip(" \t")
        near_danda = before.endswith(("।", "॥")) or after.startswith(("।", "॥"))
        line_end = after == "" or after.startswith("\n")
        if near_danda or (line_end and before.endswith(("।", "॥", "॥\n"))):
            tokens[m.start()] = (m.group(0), base * VERSE_NUM_FALLBACK_FACTOR)
    return sorted((off, num, conf) for off, (num, conf) in tokens.items())


def _attach_verse_numbers(drafts: list[_Draft], spans: list[Span], doc: Document) -> None:
    """Each numeral token is attached to the last akṣara that ends before it."""
    ends = [sp.end for sp in spans]
    for off, num, conf in _verse_number_tokens(doc):
        k = bisect.bisect_right(ends, off) - 1
        if k >= 0 and not drafts[k].verse_num_after:
            drafts[k].verse_num_after, drafts[k].verse_num_conf = num, conf


def _draft_span(d: _Draft, items: tuple[Item, ...]) -> Span:
    members = [items[i] for i in d.items]
    return Span(min(m.src.start for m in members), max(m.src.end for m in members))


def _mask_spans(items: tuple[Item, ...], groups: list[tuple[int, int]], detail: str) -> tuple[Item, ...]:
    """Items lying inside one of the (start, end) text spans become separators with `detail`."""
    if not groups:
        return items
    starts = [g[0] for g in groups]

    def inside(span: Span) -> bool:
        k = bisect.bisect_right(starts, span.start) - 1
        return k >= 0 and span.end <= groups[k][1]

    return tuple(Item("SEP", "", it.src, detail=detail) if inside(it.src) else it for it in items)


def _mask_editorial(items: tuple[Item, ...], text: str, max_chars: int) -> tuple[Item, ...]:
    """Editorial brackets (owner's rule, 2026-10-18; BASE-C `editorial_brackets`): a one-line
    `( … )` group of at most `max_chars` characters inside the brackets, with no daṇḍa, is an
    editor's correction or gloss (`यतेस्सायं (यत्र सायं)`). Its items become separators, so it
    yields no akṣara and its consonants close no preceding syllable. The text is untouched (INV-1)."""
    groups = [(m.start(), m.end()) for m in _EDITORIAL_RE.finditer(text) if m.end() - m.start() - 2 <= max_chars]
    return _mask_spans(items, groups, "editorial")


def _mask_citations(items: tuple[Item, ...], text: str) -> tuple[Item, ...]:
    """Citation sigla (BASE-C `editorial_brackets.citation_tokens`, 2026-10-18): `MDh 5․125`,
    `BDhS 1․1․1․6cd` are apparatus, not text. As Latin they would be foreign-script barriers and
    split a śloka printed as two numbered half-sūtras; as separators they are simply skipped."""
    return _mask_spans(items, [(m.start(), m.end()) for m in _CITATION_RE.finditer(text)], "citation")


def scan(doc: Document, editorial_max_chars: int | None = None, citation_tokens: bool = False) -> AksharaStream:
    """`editorial_max_chars` and `citation_tokens` (BASE-C only) enable `_mask_editorial` /
    `_mask_citations`; the defaults keep BASE-A scanning byte-identical."""
    items = tokenize(doc.text)
    if editorial_max_chars is not None:
        items = _mask_editorial(items, doc.text, editorial_max_chars)
    if citation_tokens:
        items = _mask_citations(items, doc.text)
    look = _lookahead(items)
    drafts: list[_Draft] = []
    barrier_before: list[bool] = []
    orphans = 0
    carry = None  # separator context of skipped vowel-less fragments, merged into the next word
    for wi, (seps, letters) in enumerate(_group_words(items)):
        ctx = _separator_context(items, seps, first=(wi == 0))
        word = _word_drafts(items, letters)
        if not word:
            # A vowel-less fragment (e.g. `म्` in an edition reference `॥ [म् ३․१६]`) yields no
            # akṣara; its separators must not be lost, or a ॥ silently disappears.
            orphans += sum(1 for i in letters if items[i].kind == "C")
            if drafts and ctx["delim"]:
                drafts[-1].delim_after = _stronger(drafts[-1].delim_after, ctx["delim"])
            carry = _merge_ctx(carry, ctx)
            continue
        if carry is not None:
            ctx, carry = _merge_ctx(carry, ctx), None
        _mark_soft_from_avagraha(word, items)
        head = word[0]
        head.word_start, head.line_start, head.para_start = ctx["word_start"], ctx["line_start"], ctx["para_start"]
        head.soft_start = head.soft_start or ctx["soft_start"]
        head.delim_before = ctx["delim"]
        if drafts and ctx["delim"]:
            drafts[-1].delim_after = ctx["delim"]
        word[-1].word_end = True
        barrier_before.extend([ctx["barrier"]] + [False] * (len(word) - 1))
        drafts.extend(word)
    conf = DELIM_CONF[doc.tier]
    spans = [_draft_span(d, items) for d in drafts]
    _attach_verse_numbers(drafts, spans, doc)
    labels = _project_records(spans, _record_labels(doc))
    aksharas = tuple(_freeze(k, d, src, lab, items, look, conf)
                     for k, (d, src, lab) in enumerate(zip(drafts, spans, labels)))
    return AksharaStream(doc.doc_id, aksharas, _runs(aksharas, barrier_before), items,
                         analysis_view(items), orphans)


def _freeze(k, d: _Draft, src: Span, labels: frozenset[str], items, look, conf) -> Akshara:
    members = [items[i] for i in d.items]
    nuc = items[d.nucleus]
    mods = "".join(m.slp1 for m in members if m.kind == "M")
    coda = sum(1 for i in d.items if i > d.nucleus and items[i].kind == "C")
    cons_after, stopped = look[d.nucleus]
    flag_set = set(labels) - {"vedic"}
    if nuc.detail:
        flag_set.add(nuc.detail)
    phon_flagged = bool(flag_set & (PHONOLOGICAL_FLAGS | {"orphan_matra"}))
    weight, intrinsic = _weight(nuc.slp1, mods, cons_after, stopped, phon_flagged)
    return Akshara(
        idx=k, src=src, slp1="".join(m.slp1 for m in members if m.kind != "AVA"),
        vowel=nuc.slp1, weight=weight, matra={"L": 1, "G": 2}.get(weight),
        word_start=d.word_start, soft_start=d.soft_start, word_end=d.word_end,
        line_start=d.line_start, para_start=d.para_start,
        delim_before=d.delim_before, delim_after=d.delim_after,
        delim_conf=conf if (d.delim_before or d.delim_after) else 0.0,
        verse_num_after=d.verse_num_after, verse_num_conf=d.verse_num_conf,
        intrinsic_heavy=intrinsic, coda_count=coda, cons_after=cons_after,
        closed_by_pause=stopped and cons_after >= 1, nasal="~" in mods,
        possible_parses=("L", "G") if weight == "?" else (weight,),
        excluded="vedic" in labels, flags=frozenset(flag_set),
    )


def _runs(aksharas: tuple[Akshara, ...], barrier_before: list[bool]) -> tuple[Span, ...]:
    """Eligible runs split at foreign-script barriers and excluded akṣaras (DP-2)."""
    runs, start = [], None
    for a in aksharas:
        if a.excluded or (barrier_before[a.idx] and start is not None):
            if start is not None:
                runs.append(Span(start, a.idx))
            start = None
        if not a.excluded and start is None:
            start = a.idx
    if start is not None:
        runs.append(Span(start, len(aksharas)))
    return tuple(runs)


def contextual_final_weight(a: Akshara) -> Weight:
    """PH-3/BASE-3: weight of a span-final syllable with no lookahead past the span.

    A closing consonant attached to the akṣara itself (word-final coda) still closes
    it; consonants belonging to following text do not.
    """
    if a.weight == "?":
        return "?"
    if a.intrinsic_heavy or a.coda_count >= 1:
        return "G"
    return "L"
