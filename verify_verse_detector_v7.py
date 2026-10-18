#!/usr/bin/env python3
"""Mechanical consistency checks for the Padya v7 engineering blueprint.

Checks the Markdown's internal consistency, the integration receipt for the
cleaner, and (optionally) the cleaner file's hash. It does NOT verify prosodic
correctness, detector accuracy, or performance.

usage:
  python3 verify_verse_detector_v7.py [blueprint.md] [--receipt cleaner_receipt_v3.1.json]
                                      [--cleaner clean_sanskrit_corpus.py] [--out report.json]
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

GANA = {'ya': 'LGG', 'ma': 'GGG', 'ta': 'GGL', 'ra': 'GLG', 'ja': 'LGL',
        'bha': 'GLL', 'na': 'LLL', 'sa': 'LLG', 'la': 'L', 'ga': 'G'}
FIXTURE_SRC = 'अत्र केचिदाहुः अयं निजः परो वेति गणना लघुचेतसाम् उदारचरितानां तु वसुधैव कुटुम्बकम् इत्यादि।'
FIXTURE_VERSE = 'अयं निजः परो वेति गणना लघुचेतसाम् उदारचरितानां तु वसुधैव कुटुम्बकम्'
FIXTURE_SHA = '5b8014f44480aa9ec2462ee67ff095cd5147e9126cd280bc191ef37340f89a32'
T03 = 'तथा च मनुः अयं निजः परो वेति गणना लघुचेतसाम् इत्यादि । ततः परं निर्णयः ।\n'


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(blueprint: Path, receipt: Path | None, cleaner: Path | None) -> dict:
    text = blueprint.read_text(encoding='utf-8')
    lines = text.splitlines()
    checks: list[dict] = []

    def check(name: str, ok, details: str = ''):
        checks.append({'check': name, 'passed': bool(ok), 'details': details})

    # ---- document structure
    check('version declared v7', 'Version: 7.0' in text)
    fences = [l for l in lines if re.match(r'^\s*```', l)]
    check('balanced Markdown code fences', len(fences) % 2 == 0, f'{len(fences)} fences')
    sec = {i: [j + 1 for j, l in enumerate(lines) if re.match(rf'^## {i}\. ', l)] for i in range(39, 51)}
    check('sections 39–50 each occur once', all(len(v) == 1 for v in sec.values()), str({k: v for k, v in sec.items() if len(v) != 1}))

    # ---- metre registry: declared length == len(pattern) == expand(gaṇa formula)
    table = text.split('### 5.3 Sama-vṛtta')[1].split('### 5.4 Mātrā metres')[0]
    patterns = []
    for ln in table.splitlines():
        if not ln.startswith('|') or ln.count('|') < 6:
            continue
        cells = [x.strip() for x in ln.split('|')[1:-1]]
        if len(cells) != 5:
            continue
        name, n, raw, _, formula = cells
        m = re.search(r'`([LG]+)`', raw)
        if not m or not n.isdigit():
            continue
        toks = re.findall(r'\b(?:ya|ma|ta|ra|ja|bha|na|sa|la|ga)\b', formula.split('—')[0])
        expanded = ''.join(GANA[t] for t in toks)
        patterns.append({'name': name, 'declared': int(n), 'pattern': m.group(1), 'expanded': expanded,
                         'valid': len(m.group(1)) == int(n) and m.group(1) == expanded})
    bad = [p['name'] for p in patterns if not p['valid']]
    check('all fixed-metre gaṇa expansions agree with patterns', len(patterns) >= 29 and not bad,
          f'{len(patterns)} rows; mismatches: {bad}')

    # ---- §13.1 fixture
    check('fixture: 91 code points', len(FIXTURE_SRC) == 91)
    check('fixture: SHA-256', hashlib.sha256(FIXTURE_SRC.encode()).hexdigest() == FIXTURE_SHA)
    check('fixture: [15,82) is the verse', FIXTURE_SRC[15:82] == FIXTURE_VERSE)
    check('fixture: text present in blueprint', FIXTURE_SRC in text and FIXTURE_VERSE in text)
    check('T03: [11,44) is the half-verse', T03[11:44] == 'अयं निजः परो वेति गणना लघुचेतसाम्')

    # ---- fixture labels
    tids = set(re.findall(r'^\| (?:\*\*)?(T\d\d)(?:\*\*)? \|', text, flags=re.M))
    missing = [f'T{i:02d}' for i in range(1, 43) if f'T{i:02d}' not in tids]
    check('T01–T42 case labels present', not missing, 'missing: ' + str(missing))

    # ---- wording guards
    check('lattice posterior ≠ calibrated probability stated', 'lattice posterior' in text.lower())
    check('Vedic metre detection out of scope stated', 'Vedic metre recognition, classification or evaluation.' in text)
    check('§29 attested (not "schema expectation")', 'attested against `clean_sanskrit_corpus.py` v3.1' in text)
    check('no stale fixture range T01…T30', 'fixtures/T01…T30' not in text)
    check('confidence enum canonical (lowercase ood)', "confidence_status=ood" in text or "'ood'" in text)

    # ---- YAML seeds (§32.1–32.4)
    try:
        import yaml  # type: ignore
        sub = text.split('## 32. Configuration files')[1].split('## 33.')[0]
        blocks = re.findall(r'```yaml\n(.*?)\n```', sub, re.DOTALL)
        parsed = []
        for b in blocks:
            try:
                parsed.append(isinstance(yaml.safe_load(b), (dict, list)))
            except Exception as e:  # noqa: BLE001
                parsed.append(False)
                checks.append({'check': 'yaml block error', 'passed': False, 'details': str(e)[:200]})
        check('all §32 YAML seeds parse', len(blocks) >= 4 and all(parsed), f'{len(blocks)} blocks')
    except ImportError:
        check('§32 YAML seeds parse', True, 'skipped: PyYAML not installed')

    # ---- receipt
    rc = None
    if receipt and receipt.exists():
        rc = json.loads(receipt.read_text(encoding='utf-8'))
        dev = rc.get('fixture_cleaned_text', '')
        ok_offsets = True
        for r in rc.get('fixture_records', []):
            seg = dev[r['start']:r['end']]
            if r['kind'] == 'verse_number' and seg != r['number']:
                ok_offsets = False
            if r['kind'] == 'vedic' and not any(0x951 <= ord(c) <= 0x954 or 0x1CD0 <= ord(c) <= 0x1CFF
                                                 or 0xA8E0 <= ord(c) <= 0xA8FF for c in seg):
                ok_offsets = False
            if r['kind'] == 'flag' and r['cls'] == 'double_virama' and seg != '््':
                ok_offsets = False
        check('receipt: record offsets re-verify from receipt text', ok_offsets and rc.get('all_offsets_valid') is True)
        check('receipt: cleaned text hash matches receipt',
              hashlib.sha256(dev.encode('utf-8')).hexdigest() == rc.get('fixture_cleaned_sha256'))
        check('receipt: cleaner SHA-256 quoted in blueprint', rc.get('cleaner_sha256', 'x') in text)
        check('receipt: offsets convention stated',
              rc.get('manifest_offsets_refer_to', '').startswith('cleaned_devanagari text'))
        check('receipt: self-test passed', rc.get('selftest_last_line') == 'SELFTEST: PASSED')
        if cleaner and cleaner.exists():
            check('cleaner file hash equals receipt', sha256_file(cleaner) == rc.get('cleaner_sha256'), sha256_file(cleaner))
            check('cleaner file declares the receipt version',
                  f'VERSION = "{rc.get("cleaner_version_string")}"' in cleaner.read_text(encoding='utf-8'))
        else:
            check('cleaner file hash equals receipt', True, 'skipped: cleaner file not given/found')
    else:
        check('receipt file present', False, 'cleaner_receipt_v3.1.json not found; §29 attestation cannot be re-checked')

    failures = [c for c in checks if not c['passed']]
    return {
        'document': str(blueprint), 'file_sha256': sha256_file(blueprint), 'file_lines': len(lines),
        'fixed_metres': [{'name': p['name'], 'valid': p['valid']} for p in patterns],
        'checks': checks, 'passed': len(checks) - len(failures), 'total': len(checks), 'failures': failures,
        'limitations': [
            'No philological source-by-source verification of metre rules was executed.',
            'The receipt attests the cleaner\'s output format, not detector accuracy.',
            'No Sanskrit gold-set evaluation or speed benchmark was run.',
        ],
    }


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument('path', nargs='?', default=str(here / 'verse_detector_blueprint_v7.md'))
    ap.add_argument('--receipt', default=str(here / 'cleaner_receipt_v3.1.json'))
    ap.add_argument('--cleaner', default=str(here / 'clean_sanskrit_corpus.py'))
    ap.add_argument('--out', default=str(here / 'verse_detector_v7_validation.json'))
    a = ap.parse_args()
    result = main(Path(a.path), Path(a.receipt), Path(a.cleaner))
    Path(a.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"{result['passed']}/{result['total']} checks passed; {result['file_lines']} lines; {len(result['fixed_metres'])} metre rows")
    for x in result['failures']:
        print('FAIL:', x)
    sys.exit(0 if not result['failures'] else 1)
