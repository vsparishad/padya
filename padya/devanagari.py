"""Devanagari character classes and SLP1 tables (SV-9, SC-0…SC-4, SC-9).

Each code point gets exactly one class; the scanner never edits text, it only
classifies it. Unknown characters are classified, never deleted (TEST6-8).
"""
from __future__ import annotations

from enum import Enum


class CharClass(Enum):
    CONSONANT = "consonant"
    VOWEL = "vowel"  # independent vowel letter
    MATRA = "matra"  # dependent vowel sign
    VIRAMA = "virama"
    MODIFIER = "modifier"  # anusvāra, visarga, candrabindu, jihvāmūlīya, upadhmānīya
    AVAGRAHA = "avagraha"
    OM = "om"
    MARK = "mark"  # nukta, accents, ZWJ/ZWNJ: attach to the preceding character
    DANDA = "danda"
    DOUBLE_DANDA = "double_danda"
    DIGIT = "digit"
    NEWLINE = "newline"
    SPACE = "space"
    HYPHEN = "hyphen"
    PUNCT = "punct"
    FOREIGN = "foreign"  # other scripts: a barrier for candidates (DP-2)


CONSONANTS = {
    "क": "k", "ख": "K", "ग": "g", "घ": "G", "ङ": "N",
    "च": "c", "छ": "C", "ज": "j", "झ": "J", "ञ": "Y",
    "ट": "w", "ठ": "W", "ड": "q", "ढ": "Q", "ण": "R",
    "त": "t", "थ": "T", "द": "d", "ध": "D", "न": "n",
    "प": "p", "फ": "P", "ब": "b", "भ": "B", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v",
    "श": "S", "ष": "z", "स": "s", "ह": "h", "ळ": "L",
    # precomposed nukta forms map to their base; the nukta is recorded as a flag
    "क़": "k", "ख़": "K", "ग़": "g", "ज़": "j",
    "ड़": "q", "ढ़": "Q", "फ़": "P", "य़": "y",
    "ऩ": "n", "ऱ": "r", "ऴ": "L",
}

VOWELS = {
    "अ": "a", "आ": "A", "इ": "i", "ई": "I", "उ": "u", "ऊ": "U",
    "ऋ": "f", "ॠ": "F", "ऌ": "x", "ॡ": "X",
    "ए": "e", "ऐ": "E", "ओ": "o", "औ": "O",
}

MATRAS = {
    "ा": "A", "ि": "i", "ी": "I", "ु": "u", "ू": "U",
    "ृ": "f", "ॄ": "F", "ॢ": "x", "ॣ": "X",
    "े": "e", "ै": "E", "ो": "o", "ौ": "O",
}

# Non-classical vowel letters/signs (short e/o, candra e/o). They occur as typing or OCR
# variants in Sanskrit editions; the text is never corrected (DET-5), the vowel is
# scanned with unknown weight "?" (SC-7) instead of being treated as a foreign barrier.
NONSTANDARD_VOWELS = {"\u090e": "?", "\u0912": "?", "\u090d": "?", "\u0911": "?"}  # ऎ ऒ ऍ ऑ
NONSTANDARD_MATRAS = {"\u0946": "?", "\u094a": "?", "\u0945": "?", "\u0949": "?"}  # ॆ ॊ ॅ ॉ
VOWELS = {**VOWELS, **NONSTANDARD_VOWELS}
MATRAS = {**MATRAS, **NONSTANDARD_MATRAS}

MODIFIERS = {
    "ं": "M",  # anusvāra (SC-1, SC-2)
    "ः": "H",  # visarga (SC-4)
    "ँ": "~",  # candrabindu (SC-3): nasalisation trait, not automatically guru
    "ᳵ": "Z",  # jihvāmūlīya (SC-4)
    "ᳶ": "V",  # upadhmānīya (SC-4)
    "ꣳ": "M",  # ꣳ Vedic anusvāra letter: a real sound, guru (cleaner v3.1 keeps it)
    "ꣴ": "M",  # ꣴ Vedic anusvāra letter
    "ᳲ": "H",  # ᳲ ardhavisarga (SC-4)
    "ᳳ": "H",  # ᳳ ardhavisarga (SC-4)
}

# SC-0: short vowels are laghu, long vowels and diphthongs guru.
SHORT_VOWELS = frozenset("aiufx")
LONG_VOWELS = frozenset("AIUFXeEoO")
# SC-1, SC-2, SC-4: these modifiers make the syllable guru.
HEAVY_MODIFIERS = frozenset("MHZV")

VIRAMA = "्"
AVAGRAHA = "ऽ"
OM = "ॐ"
DANDA = "।"
DOUBLE_DANDA = "॥"
NUKTA = "़"

_MARK_RANGES = (
    (0x0951, 0x0954),  # Vedic svara marks
    (0x1CD0, 0x1CF4),  # Vedic extensions
    (0x1CF7, 0x1CFF),
    (0xA8E0, 0xA8F1),  # Devanagari extended combining marks
    (0x200C, 0x200D),  # ZWNJ, ZWJ
    (0x093C, 0x093C),  # nukta
    (0xFE00, 0xFE0F),  # variation selectors
)
_SPACE_CHARS = frozenset(" \t\r        　﻿")


def classify(ch: str) -> CharClass:
    """Return the single class of one code point."""
    if ch in CONSONANTS:
        return CharClass.CONSONANT
    if ch in VOWELS:
        return CharClass.VOWEL
    if ch in MATRAS:
        return CharClass.MATRA
    if ch == VIRAMA:
        return CharClass.VIRAMA
    if ch in MODIFIERS:
        return CharClass.MODIFIER
    if ch == AVAGRAHA:
        return CharClass.AVAGRAHA
    if ch == OM:
        return CharClass.OM
    if ch == DANDA:
        return CharClass.DANDA
    if ch == DOUBLE_DANDA:
        return CharClass.DOUBLE_DANDA
    if ch == "\n":
        return CharClass.NEWLINE
    if ch in _SPACE_CHARS:
        return CharClass.SPACE
    if ch == "-":
        return CharClass.HYPHEN
    cp = ord(ch)
    if any(lo <= cp <= hi for lo, hi in _MARK_RANGES):
        return CharClass.MARK
    if 0x0966 <= cp <= 0x096F or "0" <= ch <= "9":
        return CharClass.DIGIT
    if _is_punct(ch):
        return CharClass.PUNCT
    return CharClass.FOREIGN


def _is_punct(ch: str) -> bool:
    import unicodedata

    return unicodedata.category(ch)[0] in ("P", "S", "Z", "C") or ch == "॰"
