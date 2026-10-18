"""Generated pages use Adishila for Devanagari and Sanskrit 2003 for verses (local fonts only)."""
from pathlib import Path

from tools.devanagari_fonts import FONT_FACES

TAGGER = Path(__file__).resolve().parents[1] / "tools" / "tagger" / "verse_tagger.html"


def test_tagger_template_carries_the_shared_font_faces_verbatim():
    assert FONT_FACES in TAGGER.read_text(encoding="utf-8")


def test_font_faces_are_local_and_script_scoped():
    assert 'local("Adishila")' in FONT_FACES and 'local("Sanskrit 2003")' in FONT_FACES
    assert "url(" not in FONT_FACES and "http" not in FONT_FACES  # nothing downloaded or embedded: offline pages
    assert FONT_FACES.count("unicode-range:") == FONT_FACES.count("@font-face")
    assert FONT_FACES.count("unicode-range: U+0900-097F") == 4  # only the Devanagari faces cover Devanagari


def test_tiro_fonts_serve_every_non_devanagari_script_and_latin():
    for name in ("Tiro Tamil", "Tiro Telugu", "Tiro Kannada", "Tiro Bangla", "Tiro Gurmukhi", "Tiro Devanagari Sanskrit"):
        assert f'local("{name}")' in FONT_FACES
    assert "U+0B80-0BFF" in FONT_FACES and "U+0000-024F" in FONT_FACES
    assert '--font-ui: "Deva", "Tiro",' in FONT_FACES and '--font-deva: "Deva", "Tiro",' in FONT_FACES


def test_verse_marks_and_verse_list_use_the_verse_font():
    page = TAGGER.read_text(encoding="utf-8")
    assert "mark.verse, mark.typo { font-family: var(--font-verse); }" in page
    assert "#verses .snip { color: var(--muted); font-family: var(--font-verse);" in page
