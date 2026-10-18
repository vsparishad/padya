#!/usr/bin/env python3
"""Which vṛtta metres can be detected strictly (no prose false positives, no label clash)?

usage: python3 tools/strict_vrttas.py --sources EXT --corpus FOLDER --runs out/digests/runs
                                      --cache corpus.pkl --out reports/strict_vrttas.md [--json strict.json]

EXT holds clones of three independent public metre lists, used only for cross-checking
patterns (they are GPL/AGPL; nothing is copied into this repository):
  EXT/sanskrit       github.com/shreevatsa/sanskrit   (Vṛttaratnākara by D. Patel; Mishra list)
  EXT/chandojnanam   github.com/hrishikeshrt/chandojnanam (Vṛttaratnākara + Śabdakalpadruma)
  EXT/vidyut         github.com/ambuda-org/vidyut     (vidyut-chandas meters.tsv, derived from VR)

For every metre pattern it measures, on the corpus (detected verses masked out):
  * anchored windows of the half/full length (start at line/daṇḍa, end at daṇḍa/line end);
  * the expected number of chance matches under an order-2 Markov L/G model of prose;
  * anchored exact matches actually observed (inside and outside current detections);
and checks cross-source agreement, anuṣṭubh compatibility, Hamming-1 neighbours and
pāda-doubling collisions. Tiers and thresholds are the named constants below.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import json
import pickle
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

MIN_STRICT_PADA = 9            # 8-syllable pādas live inside the anuṣṭubh space
MIN_PATTERN_PADA = 6           # shorter pādas are not analysed at all
EXPECTED_FULL_MAX = 0.001      # chance full stanzas allowed in the whole corpus
EXPECTED_HALF_MAX = 0.01       # chance halves allowed in the whole corpus
EXPECTED_HALF_TYPO_MAX = 0.1   # chance halves within one substitution
INDEPENDENT = ("VR", "Mishra", "Chandojñānam")
MAX_WINDOW = 4 * 26
TIER_ORDER = ["strict", "strict_full_only", "needs_second_source", "risky"]


@dataclass(frozen=True)
class Metre:
    padas: tuple[str, str, str, str]  # final syllable of each pāda replaced by X (anceps)

    @property
    def kind(self) -> str:
        p = self.padas
        if p[0] == p[1] == p[2] == p[3]:
            return "sama"
        return "ardhasama" if (p[0], p[1]) == (p[2], p[3]) else "visama"

    @property
    def half(self) -> str:
        return self.padas[0] + self.padas[1]

    @property
    def full(self) -> str:
        return "".join(self.padas)


@dataclass
class Entry:
    metre: Metre
    names: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))  # source -> names


# ---------------------------------------------------------------- sources

def _lg(s: str) -> str:
    return re.sub(r"[^LG]", "", s.replace("ल", "L").replace("ग", "G"))


def _anceps(p: str) -> str:
    return p[:-1] + "X" if p else p


def _metre(padas: list[str]) -> Metre | None:
    padas = [_lg(p) for p in padas]
    if len(padas) == 1:
        padas *= 4
    elif len(padas) == 2:
        padas *= 2
    if len(padas) != 4 or min(map(len, padas)) < MIN_PATTERN_PADA:
        return None
    return Metre(tuple(_anceps(p) for p in padas))


def _shreevatsa(path: Path) -> list[tuple[str, list[str]]]:
    out = []
    for name, v in json.loads(path.read_text(encoding="utf-8"))["metres"]:
        if isinstance(v, dict):
            v = v.get("pattern")
        if isinstance(v, str):
            out.append((name, [v]))
        elif isinstance(v, list) and all(isinstance(x, str) for x in v):
            out.append((name, v))
    return out


def _chandojnanam(folder: Path) -> list[tuple[str, list[str]]]:
    out = []
    with (folder / "chanda_sama.csv").open(encoding="utf-8") as fh:
        out += [(r["वृत्त"], [r["लक्षण (raw)"]]) for r in csv.DictReader(fh)]
    for name in ("chanda_ardhasama.csv", "chanda_vishama.csv"):
        rows = defaultdict(dict)
        with (folder / name).open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["वृत्त"] and r["पद"].isdigit():
                    rows[r["वृत्त"]][int(r["पद"])] = r["लक्षण (raw)"]
        out += [(n, [p[k] for k in sorted(p)]) for n, p in rows.items()]
    return out


def _vidyut(path: Path) -> list[tuple[str, list[str]]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        name, kind, pattern = line.split("\t")
        if kind == "vrtta":
            out.append((name, pattern.split("/")))
    return out


def _registry() -> list[tuple[str, list[str]]]:
    metres = yaml.safe_load((ROOT / "padya/config/metres.yaml").read_text(encoding="utf-8"))["metres"]
    out = []
    for m in metres:
        if "pattern" in m:
            out.append((m["id"], [m["pattern"]]))
        elif "odd_pattern" in m:
            out.append((m["id"], [m["odd_pattern"], m["even_pattern"]]))
    return out


def load_sources(ext: Path) -> dict[Metre, Entry]:
    lists = {
        "VR": _shreevatsa(ext / "sanskrit/data/vrttaratnakara.json"),
        "Mishra": _shreevatsa(ext / "sanskrit/data/mishra.json"),
        "Chandojñānam": _chandojnanam(ext / "chandojnanam/data"),
        "vidyut (from VR)": _vidyut(ext / "vidyut/vidyut-chandas/data/meters.tsv"),
        "Shreevatsa curated": _shreevatsa(ext / "sanskrit/data/curated.json") + _shreevatsa(ext / "sanskrit/data/ganesh.json"),
        "padya registry": _registry(),
    }
    entries: dict[Metre, Entry] = {}
    for source, items in lists.items():
        for name, padas in items:
            m = _metre(padas)
            if m is not None:
                entries.setdefault(m, Entry(m)).names[source].add(name)
    return entries


# ---------------------------------------------------------------- corpus

def build_cache(corpus: Path, runs: Path, cache: Path, jobs: int) -> dict:
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    files = sorted(corpus.rglob("*.txt"))
    with ProcessPoolExecutor(jobs) as ex:
        data = dict(ex.map(_scan_one, files, [runs] * len(files)))
    cache.write_bytes(pickle.dumps(data))
    return data


def _scan_one(path: Path, runs: Path):
    from padya.loader import load_plain_text
    from padya.scanner import scan
    aks = scan(load_plain_text(path)).aksharas
    n = len(aks)
    start = bytes(1 if (a.line_start or a.para_start or a.delim_before or i == 0) else 0 for i, a in enumerate(aks))
    end = bytes(1 if (a.delim_after or a.verse_num_after or i + 1 == n or aks[i + 1].line_start) else 0
                for i, a in enumerate(aks))
    starts = [a.src.start for a in aks]
    mask = bytearray(n)
    for name in ("verses.jsonl", "suspects.jsonl"):
        for p in runs.glob(f"*/{path.stem}/{name}"):
            for r in map(json.loads, p.open(encoding="utf-8")):
                i = bisect.bisect_left(starts, r["start"])
                while i < n and starts[i] < r["end"]:
                    mask[i] = 1
                    i += 1
    hard = bytes(2 if (a.delim_after == "D2" or a.verse_num_after) else (1 if a.delim_after else 0) for a in aks)
    return path.stem, {"w": "".join(a.weight for a in aks), "start": start, "end": end, "hard": hard,
                       "verse": bytes(mask)}


def markov2(data: dict) -> dict[str, float]:
    """Order-2 L/G model of prose (verse akṣaras and '?' excluded): 'L', 'L>G', 'LG>G' keys."""
    uni, bi, tri = Counter(), Counter(), Counter()
    for d in data.values():
        w, v = d["w"], d["verse"]
        for i, c in enumerate(w):
            if v[i] or c == "?":
                continue
            uni[c] += 1
            if i >= 1 and not v[i - 1] and w[i - 1] != "?":
                bi[w[i - 1] + c] += 1
                if i >= 2 and not v[i - 2] and w[i - 2] != "?":
                    tri[w[i - 2:i + 1]] += 1
    probs = {c: uni[c] / sum(uni.values()) for c in "LG"}
    for a in "LG":
        probs.update({f"{a}>{b}": bi[a + b] / max(1, bi[a + "L"] + bi[a + "G"]) for b in "LG"})
    for ctx in ("LL", "LG", "GL", "GG"):
        probs.update({f"{ctx}>{b}": tri[ctx + b] / max(1, tri[ctx + "L"] + tri[ctx + "G"]) for b in "LG"})
    return probs


def pattern_prob(pattern: str, probs: dict[str, float]) -> float:
    """Probability that a prose window realises *pattern* (X = either weight)."""
    states = {"": 1.0}
    for ch in pattern:
        nxt = defaultdict(float)
        for ctx, p in states.items():
            for c in ("LG" if ch == "X" else ch):
                key = c if not ctx else f"{ctx}>{c}"
                nxt[(ctx + c)[-2:]] += p * probs[key]
        states = nxt
    return sum(states.values())


def typo_prob(pattern: str, probs: dict[str, float]) -> float:
    """Probability of a match within exactly one substitution (non-anceps slot)."""
    flip = {"L": "G", "G": "L"}
    return sum(pattern_prob(pattern[:i] + flip[c] + pattern[i + 1:], probs)
               for i, c in enumerate(pattern) if c != "X")


def _anchored(d: dict):
    """Yield (start, end) anchored windows of at most MAX_WINDOW akṣaras that do not cross
    a stanza end (॥ or verse number) before their last akṣara (the detector's crossing rule)."""
    ends = [i for i, e in enumerate(d["end"]) if e]
    stops = [i for i, h in enumerate(d["hard"]) if h == 2]
    for s in (i for i, x in enumerate(d["start"]) if x):
        k = bisect.bisect_left(stops, s)
        limit = stops[k] if k < len(stops) else len(d["w"]) - 1
        j = bisect.bisect_left(ends, s)
        while j < len(ends) and ends[j] <= limit and ends[j] - s + 1 <= MAX_WINDOW:
            yield s, ends[j]
            j += 1


def scan_windows(data: dict, metres: list[Metre]) -> tuple[Counter, dict[Metre, Counter]]:
    """Prose-only anchored window counts by length, and anchored exact matches per metre."""
    by_len = defaultdict(lambda: defaultdict(dict))  # length -> anceps slots -> {pattern: [(metre, part)]}
    for m in metres:
        for part, pat in (("half", m.half), ("full", m.full)):
            slots = tuple(i for i, c in enumerate(pat) if c == "X")
            by_len[len(pat)][slots].setdefault(pat, []).append((m, part))
    prose, matches = Counter(), defaultdict(Counter)
    for d in data.values():
        w, verse = d["w"], d["verse"]
        pref = [0]
        for v in verse:
            pref.append(pref[-1] + v)
        for s, e in _anchored(d):
            L = e - s + 1
            groups = by_len.get(L)
            if not groups:
                continue
            inside = pref[e + 1] != pref[s]
            if not inside:
                prose[L] += 1
            seg = w[s:e + 1]
            for slots, table in groups.items():
                win = list(seg)
                for k in slots:
                    win[k] = "X"
                for m, part in table.get("".join(win), ()):
                    matches[m][f"{part}_{'detected' if inside else 'missed'}"] += 1
    return prose, matches


# ---------------------------------------------------------------- checks

ODD_CADENCES = {"LGG", "LLL", "GLL", "GGG", "GLG"}


def _odd(p: str) -> bool:
    return len(p) == 8 and p[4:7] in ODD_CADENCES and p[1:3] != "LL"


def _even(p: str) -> bool:
    return len(p) == 8 and p[4:7] == "LGL"


def anustubh_compatible(m: Metre) -> bool:
    """Could a pāda (8) or pāda-as-half (16) of this metre also scan as anuṣṭubh?"""
    pads = [p.replace("X", "G") for p in m.padas]
    if any(len(p) == 8 and (_odd(p) or _even(p)) for p in pads):
        return True
    return any(len(p) == 16 and _odd(p[:8]) and _even(p[8:]) for p in pads)


def hamming1(m: Metre, others: list[Metre]) -> list[Metre]:
    a = m.full
    out = []
    for o in others:
        b = o.full
        if o == m or len(a) != len(b) or [len(p) for p in o.padas] != [len(p) for p in m.padas]:
            continue
        if sum(1 for x, y in zip(a, b) if x != y and "X" not in (x, y)) == 1:
            out.append(o)
    return out


def doubling(m: Metre, pada_set: set[str]) -> bool:
    """Is a pāda of m two detectable (≥MIN_STRICT_PADA) known pādas glued together? Then one
    stanza of m also reads as two stanzas of the shorter metre: a label risk, not a prose risk."""
    for p in set(m.padas):
        for k in range(MIN_STRICT_PADA, len(p) - MIN_STRICT_PADA + 1):
            if _anceps(p[:k]) in pada_set and p[k:] in pada_set:
                return True
    return False


def tier(r: dict, shortest: int) -> str:
    if shortest < MIN_STRICT_PADA or r["anustubh_compatible"] or r["expected_full"] > EXPECTED_FULL_MAX:
        return "risky"
    if len(r["support"]) < 2:
        return "needs_second_source"
    if r["expected_half"] <= EXPECTED_HALF_MAX and r["expected_half_typo"] <= EXPECTED_HALF_TYPO_MAX:
        return "strict"
    return "strict_full_only"


# ---------------------------------------------------------------- report

def name_of(e: Entry) -> str:
    for src in ("padya registry", "VR", "Chandojñānam", "Mishra", "Shreevatsa curated", "vidyut (from VR)"):
        if e.names.get(src):
            return sorted(e.names[src])[0]
    return "?"


def evaluate(entries: dict[Metre, Entry], data: dict) -> list[dict]:
    metres = list(entries)
    probs = markov2(data)
    prose, matches = scan_windows(data, metres)
    pada_set = {p for m in metres for p in m.padas}
    rows = []
    for m in metres:
        e = entries[m]
        row = {
            "name": name_of(e), "kind": m.kind, "syllables": "/".join(dict.fromkeys(str(len(p)) for p in m.padas)),
            "padas": list(m.padas), "names": {k: sorted(v) for k, v in e.names.items()},
            "support": [s for s in INDEPENDENT if e.names.get(s)], "in_registry": bool(e.names.get("padya registry")),
            "anustubh_compatible": anustubh_compatible(m), "doubling": doubling(m, pada_set),
            "hamming1": sorted(name_of(entries[o]) for o in hamming1(m, metres)),
            "expected_half": prose[len(m.half)] * pattern_prob(m.half, probs),
            "expected_full": prose[len(m.full)] * pattern_prob(m.full, probs),
            "expected_half_typo": prose[len(m.half)] * typo_prob(m.half, probs),
            "observed": dict(matches.get(m, {})),
        }
        row["tier"] = tier(row, min(len(p) for p in m.padas))
        rows.append(row)
    return sorted(rows, key=lambda r: (TIER_ORDER.index(r["tier"]), -_seen(r), r["name"]))


def _seen(r: dict) -> int:
    return sum(r["observed"].values())


def _fmt(x: float) -> str:
    return "0" if x == 0 else (f"{x:.0e}" if x < 0.01 else f"{x:.2f}")


def markdown(rows: list[dict], n_aks: int) -> str:
    c = Counter(r["tier"] for r in rows)
    out = [
        "# Strict vṛtta list: where verse detection is possible without risk", "",
        f"Corpus: 36 digest texts, {n_aks:,} akṣaras. {len(rows)} distinct vṛtta patterns (pādas ≥{MIN_PATTERN_PADA}) "
        "from three independent public lists: the Vṛttaratnākara transcription by Dhaval Patel (via Shreevatsa's "
        "`sanskrit` repo), the Mishra/Heidelberg list, and Chandojñānam (IIT Kanpur; Vṛttaratnākara + Śabdakalpadruma). "
        "vidyut-chandas `meters.tsv` is derived from the same Vṛttaratnākara data, so it is shown but not counted as "
        "independent. Agreement between digital lists is **not** primary-source verification (REL6-5/8). "
        "Jāti (mātrā) metres such as āryā are outside this list by construction.", "",
        "## Rules", "",
        f"* **strict**: identical L/G pattern in ≥2 independent lists; every pāda ≥{MIN_STRICT_PADA} syllables; not "
        "anuṣṭubh-compatible; expected chance matches in this "
        f"corpus's prose ≤{EXPECTED_FULL_MAX} full stanzas, ≤{EXPECTED_HALF_MAX} halves and ≤{EXPECTED_HALF_TYPO_MAX} "
        "one-substitution typo halves. Full stanzas, halves and typo review are all safe.",
        "* **strict_full_only**: as strict, but halves (or typo halves) are not safe; emit full stanzas only.",
        "* **needs_second_source**: passes the corpus test but only one independent list has this exact pattern.",
        f"* **risky**: a pāda <{MIN_STRICT_PADA}, anuṣṭubh-compatible, or chance full stanzas above the limit.", "",
        f"*Glued pādas* (a note, not a tier): a pāda equals two detectable (≥{MIN_STRICT_PADA}) known pādas, so a stanza "
        "could also be read as two stanzas of the shorter metre; the decoder must prefer the longer reading.", "",
        "*Expected* = anchored prose windows of that length (start at line/daṇḍa, end at daṇḍa/line end, no detected "
        "akṣara inside) × probability of the pattern under an order-2 Markov model of prose L/G. *Seen* = anchored "
        "exact matches anywhere in the corpus: inside a current detection / outside (a missed verse, or prose). "
        "*Hamming-1* = another known metre of the same shape one syllable away: detection is safe, but one OCR error "
        "changes the metre label.", "",
        f"Totals: strict {c['strict']}, strict_full_only {c['strict_full_only']}, "
        f"needs_second_source {c['needs_second_source']}, risky {c['risky']}.", "",
    ]
    out += recommendations(rows)
    for t in TIER_ORDER:
        sel = [r for r in rows if r["tier"] == t]
        if t in ("needs_second_source", "risky"):
            out += [f"## {t}: {len(sel)} patterns (listed: in the registry or seen in the corpus)", ""]
            sel = [r for r in sel if r["in_registry"] or _seen(r)]
        else:
            out += [f"## {t}: {len(sel)} patterns", ""]
        out += ["| Metre (other names) | Kind | Syll. | Pattern | Lists | Reg. | Exp. half | Exp. typo half | "
                "Exp. full | Seen full det/out | Seen half det/out | Hamming-1 | Notes |",
                "|---|---|---|---|---|---|---:|---:|---:|---|---|---|---|"]
        out += [_md_row(r) for r in sel]
        out.append("")
    return "\n".join(out)


def recommendations(rows: list[dict]) -> list[str]:
    """Registry actions implied by the tiers (the registry itself is not changed by this tool)."""
    def names(sel):
        return ", ".join(r["name"] for r in sel) or "—"
    reg = [r for r in rows if r["in_registry"]]
    add = [r for r in rows if not r["in_registry"] and r["tier"] == "strict" and r["observed"].get("full_missed")]
    return [
        "## Recommendation for the registry", "",
        f"* **Detect full stanzas, halves and typo verses** (strict): {names([r for r in reg if r['tier'] == 'strict'])}.",
        f"* **Full stanzas only; no halves, no typo verses** (strict_full_only): "
        f"{names([r for r in reg if r['tier'] == 'strict_full_only'])}. Upajāti mixtures inherit this from their components.",
        f"* **Disable** (risky): {names([r for r in reg if r['tier'] == 'risky'])}.",
        f"* **Candidates to add** (strict, full stanzas seen outside current detections; check each instance first): "
        f"{names(add)}.", "",
    ]


def _md_row(r: dict) -> str:
    o = r["observed"]
    pat = " / ".join(dict.fromkeys(r["padas"]))
    notes = [k for k, v in (("anuṣṭubh-compatible", r["anustubh_compatible"]), ("glued pādas", r["doubling"])) if v]
    others = sorted({n for v in r["names"].values() for n in v} - {r["name"]})
    label = r["name"] + (f" ({', '.join(others[:3])}{'…' if len(others) > 3 else ''})" if others else "")
    return (f"| {label} | {r['kind']} | {r['syllables']} | `{pat}` | {', '.join(r['support']) or '—'} | "
            f"{'yes' if r['in_registry'] else ''} | {_fmt(r['expected_half'])} | {_fmt(r['expected_half_typo'])} | "
            f"{_fmt(r['expected_full'])} | {o.get('full_detected', 0)}/{o.get('full_missed', 0)} | "
            f"{o.get('half_detected', 0)}/{o.get('half_missed', 0)} | {', '.join(r['hamming1'][:3])} | {'; '.join(notes)} |")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--runs", type=Path, required=True)
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args(argv)
    entries = load_sources(a.sources)
    data = build_cache(a.corpus, a.runs, a.cache, a.jobs)
    rows = evaluate(entries, data)
    a.out.write_text(markdown(rows, sum(len(d["w"]) for d in data.values())), encoding="utf-8")
    if a.json:
        a.json.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(dict(Counter(r["tier"] for r in rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
