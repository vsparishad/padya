# Contributing to पद्यज्ञापिनी (`padya`)

The specification is [`verse_detector_blueprint_v7.md`](verse_detector_blueprint_v7.md). Its §0 rules
govern every change:

1. **Never mutate source text (INV-1).** Every emitted record satisfies `text == source[start:end]`
   in code-point offsets. OCR damage is reported (typo verses), never corrected.
2. **No LLM, no network in `padya/`.** Same input, config and version give the same output.
3. **Fail closed.** Unknown metres, invalid registry entries and offset mismatches are errors.
4. **`BASE-A` is frozen.** New behaviour goes into `BASE-C` behind a key in
   `padya/config/profiles.yaml`, read with `mode.get(key, default)`, with a test that BASE-A is
   unaffected, and a bump of `frozen_id` with a one-line reason.
5. **Keep detection strict.** Do not add metres, enlarge edit budgets or relax anchors without
   first measuring the expected chance matches in prose (`tools/strict_vrttas.py`) and reviewing a
   sample of what the change recovers.
6. **Tunables live in config**, not in code: `weights.yaml`, `profiles.yaml`, `metres.yaml`.
7. **Rule traceability.** Name the blueprint rule ids (`SV-3`, `AN-2`, `INV-1`, …) in docstrings,
   tests and commit messages.

## Working method

- Test first: a reported stanza becomes a fixture (`tests/test_fixed_metres.py`,
  `tests/test_ocr_suspects.py`, `tests/test_vipula_and_halves.py`), then the implementation.
- `pytest -q` must stay green; `python tools/verify_metres.py` must pass.
- Commits use conventional prefixes (`feat:`, `fix:`, `docs:`, `test:`, `data:`) and say which rule
  applies and why.
- Do not add corpus text whose rights are not cleared. Short verse quotations as test fixtures are fine.
- External metre lists (shreevatsa/sanskrit, Chandojñānam, vidyut-chandas) are GPL/AGPL: use them for
  cross-checks from local clones; never copy their data into this repository.
