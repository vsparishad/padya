"""Fonts for the generated HTML pages (owner's choices, 2026-10-17/18).

Adishila for all Devanagari; Sanskrit 2003 for verse text; Tiro Typeworks fonts for every other
script and for Latin/IAST (Tiro Tamil, Tiro Telugu, Tiro Kannada, Tiro Bangla, Tiro Gurmukhi, and
the Latin glyphs of Tiro Devanagari Sanskrit). All faces are used through `local()` only (installed
fonts, nothing embedded or downloaded: the pages work offline), and each face is limited to its
script's ranges, so a Tamil commentary, an English header and a Devanagari verse each get their own
font. Hindi or Marathi written in Devanagari cannot be told apart from Sanskrit and stay in Adishila.
On a machine without a font the page falls back to the system font for that script.

tools/tagger/verse_tagger.html carries a verbatim copy of FONT_FACES (it is a static,
offline template); tests/test_devanagari_fonts.py keeps the two identical.
"""
DEVANAGARI_RANGE = "U+0900-097F, U+1CD0-1CFF, U+A8E0-A8FF, U+200C-200D, U+25CC"
LATIN_RANGE = "U+0000-024F, U+1E00-1EFF, U+2000-206F"
TIRO_SCRIPTS = (  # (family name as installed, unicode range)
    ("Tiro Tamil", "U+0B80-0BFF"),
    ("Tiro Telugu", "U+0C00-0C7F"),
    ("Tiro Kannada", "U+0C80-0CFF"),
    ("Tiro Bangla", "U+0980-09FF"),
    ("Tiro Gurmukhi", "U+0A00-0A7F"),
    ("Tiro Devanagari Sanskrit", LATIN_RANGE),  # Latin and IAST glyphs; Devanagari itself stays Adishila
)
_TIRO_FACES = "\n".join(
    f'@font-face {{ font-family: "Tiro"; src: local("{name}"), local("{name.replace(" ", "")}"), local("{name.replace(" ", "")}-Regular"); unicode-range: {rng}; }}'
    for name, rng in TIRO_SCRIPTS)

FONT_FACES = f"""/* Fonts (tools/devanagari_fonts.py): Adishila for Devanagari, Sanskrit 2003 for verses, Tiro for other scripts and Latin */
@font-face {{ font-family: "Deva"; font-weight: 400; src: local("Adishila"), local("Adishila-Regular"); unicode-range: {DEVANAGARI_RANGE}; }}
@font-face {{ font-family: "Deva"; font-weight: 700; src: local("Adishila Bold"), local("Adishila-Bold"); unicode-range: {DEVANAGARI_RANGE}; }}
@font-face {{ font-family: "Deva"; font-style: italic; src: local("Adishila Italic"), local("Adishila-Italic"); unicode-range: {DEVANAGARI_RANGE}; }}
@font-face {{ font-family: "DevaVerse"; src: local("Sanskrit 2003"), local("Sanskrit2003"); unicode-range: {DEVANAGARI_RANGE}; }}
{_TIRO_FACES}
:root {{ --font-ui: "Deva", "Tiro", -apple-system, "Segoe UI", Roboto, sans-serif;
        --font-deva: "Deva", "Tiro", "Kohinoor Devanagari", "Devanagari Sangam MN", serif;
        --font-verse: "DevaVerse", "Deva", "Tiro", "Kohinoor Devanagari", serif; }}"""
