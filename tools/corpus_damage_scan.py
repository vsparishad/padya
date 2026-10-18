"""OCR-damage scan of a Devanagari corpus: counts per damage class, impossible-cluster hits and
per-file noise scores (reports/corpus_damage_scan.md, 2026-10-18).

Usage: python tools/corpus_damage_scan.py LIBRARY_FOLDER data/impossible_clusters.txt OUT.json
Reads every .txt under the folder (skipping cleaned_* folders); writes a JSON of counts and
short context snippets only. The output may hold fragments of private corpus text: keep it in
out/ or the scratchpad, never in a tracked file."""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT, CLUSTERS, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
DEV = "ऀ-ॿ"
CONS = "क-ह"
MATRA = "ा-ौॢॣ"
IVOW = "ऄ-औ"
clusters = [c.strip() for c in CLUSTERS.read_text(encoding="utf-8").splitlines() if c.strip()]
# longest-first alternation so 3-member clusters win over their 2-member prefixes
CL_RE = re.compile("|".join(re.escape(c) for c in sorted(set(clusters), key=len, reverse=True)))

PATTERNS = {
    # --- characters that change metrical weight or syllable count ---
    "colon_as_visarga":        rf"[{CONS}{MATRA}{IVOW}]:(?=[\s{DEV}।॥)]|$)",
    "latin_inside_word":       rf"[{DEV}][A-Za-z]{{1,3}}[{DEV}]",
    "digit_inside_word":       rf"[{CONS}{MATRA}][0-9०-९][{CONS}{MATRA}]",
    "orphan_matra":            rf"(?<![{CONS}])[{MATRA}]",
    "virama_then_matra":       rf"्[{MATRA}]",
    "double_virama":           r"््",
    "double_anusvara":         r"ंं",
    "double_visarga":          r"ःः",
    "anusvara_plus_visarga":   r"ंः|ःं",
    "visarga_mid_word":        rf"ः(?=[{CONS}])",            # रामःस्य : visarga glued to next consonant
    "indep_vowel_after_cons":  rf"[{CONS}][{IVOW}]",              # कअ : lost space or wrong vowel
    "matra_after_matra":       rf"[{MATRA}][{MATRA}]",
    "nukta":                   r"़",
    "zwj_zwnj":                r"[‌‍]",
    "replacement_char":        r"�",
    "question_mark_in_text":   r"\(\?\)|\?",
    "avagraha_run":            r"ऽ{2,}",
    "avagraha_after_cons":     rf"[{CONS}]ऽ",                     # consonant + ऽ without vowel: OCR
    # --- punctuation / layout ---
    "pipe_as_danda":           r"\|",
    "ascii_period_as_danda":   rf"[{DEV}]\.(?=\s|$)",
    "danda_space_danda":       r"।[ \t]+।",
    "danda_at_line_start":     r"(?m)^[ \t]*[।॥]",
    "hyphen_line_end":         rf"[{DEV}]-[ \t]*\n",
    "hyphen_inside_word":      rf"[{DEV}]-[{DEV}]",
    "verse_num_spaced":        r"॥[ \t]+[०-९0-9]+[ \t]+॥",
    "verse_num_unspaced":      r"॥[०-९0-9]+॥",
    "verse_num_one_sided":     r"॥[ \t]*[०-९0-9]+(?![ \t]*॥)",
    "verse_num_ascii_digits":  r"॥[ \t]*[0-9]+",
    "bracket_group":           r"\([^()\n]*\)",
    "square_bracket_group":    r"\[[^\[\]\n]*\]",
    "tamil_chars":             r"[஀-௿]",
    "iast_latin_word":         r"\b[a-zA-ZĀ-ɏḀ-ỿ]{3,}\b",
    "long_unspaced_run":       rf"[{DEV}]{{40,}}",
    "line_ends_without_punct": rf"(?m)[{CONS}{MATRA}ंः्][ \t]*$",
    "blank_line":              r"\n[ \t]*\n",
}
COMPILED = {k: re.compile(v) for k, v in PATTERNS.items()}
NO_EXAMPLES = {"blank_line", "tamil_chars", "line_ends_without_punct"}


def snippet(text, s, e, w=22):
    return text[max(0, s - w):min(len(text), e + w)].replace("\n", "⏎")


totals = Counter(); per_file = {}; examples = defaultdict(list)
cluster_hits = Counter(); cluster_examples = defaultdict(list)
aksharas_total = 0; lines_total = 0
for path in sorted(ROOT.rglob("*.txt")):
    if any(part.startswith("cleaned_") for part in path.parts):
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = str(path.relative_to(ROOT))
    aks = len(re.findall(rf"[{IVOW}{CONS}]", text)); aksharas_total += aks
    lines_total += text.count("\n")
    row = {"aksharas": aks, "chars": len(text)}
    for k, rx in COMPILED.items():
        n = 0
        for m in rx.finditer(text):
            n += 1
            if len(examples[k]) < 3 and k not in NO_EXAMPLES:
                examples[k].append(snippet(text, m.start(), m.end()))
        if n:
            row[k] = n; totals[k] += n
    nc = 0
    for m in CL_RE.finditer(text):
        nc += 1; cluster_hits[m.group(0)] += 1
        if len(cluster_examples[m.group(0)]) < 2:
            cluster_examples[m.group(0)].append(snippet(text, m.start(), m.end(), 14))
    row["impossible_clusters"] = nc; totals["impossible_clusters"] += nc
    row["noise_per_1000"] = round(1000 * (row.get("orphan_matra", 0) + row.get("virama_then_matra", 0) + row.get("double_virama", 0)
                                          + row.get("latin_inside_word", 0) + nc) / max(aks, 1), 2)
    per_file[rel] = row

out = {
    "files": len(per_file), "aksharas": aksharas_total, "lines": lines_total,
    "totals": dict(totals.most_common()),
    "per_1000_aksharas": {k: round(1000 * v / aksharas_total, 3) for k, v in totals.items()},
    "examples": dict(examples),
    "impossible_cluster_top": [(c, n, cluster_examples[c]) for c, n in cluster_hits.most_common(40)],
    "impossible_cluster_distinct": len(cluster_hits),
    "noisiest_files": sorted(((r["noise_per_1000"], f) for f, r in per_file.items()), reverse=True)[:15],
    "per_file": per_file,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: out[k] for k in ("files", "aksharas", "lines", "totals", "impossible_cluster_distinct")}, ensure_ascii=False, indent=1))
print("noisiest:", out["noisiest_files"][:8])
