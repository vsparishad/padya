"""Bit-parallel necessary-condition prefilter (§5.1, SRCH-1…SRCH-3, BASE-4).

Masks encode only cadence slots that every enabled variant fixes: pathyā-only mode
fixes slots 5–7 of every pāda; with vipulās enabled the odd cadences vary, so only
the even cadences (and syllable 4 of nothing, since pathyā leaves it free) remain. A nonzero
mismatch count is a proven lower bound only in zero-edit mode with a fixed-length
parse, which is the only mode BASE-A runs. A zero count proves nothing: callers
must still run `anustubh.gate` (SRCH-2).
"""
from __future__ import annotations

from dataclasses import dataclass

ODD_CADENCE, EVEN_CADENCE = "LGG", "LGL"


@dataclass(slots=True, frozen=True)
class Masks:
    req_l: int
    req_g: int


def pathya_masks(padas: int = 4) -> Masks:
    return masks_for(("pathya",), padas)


def masks_for(variants: tuple[str, ...], padas: int = 4) -> Masks:
    """Necessary-condition masks for the given odd-pāda variant set (SRCH-1)."""
    req_l = req_g = 0
    odd_fixed = variants == ("pathya",)
    for pada in range(padas):
        if pada % 2 == 0 and not odd_fixed:
            continue
        cadence = ODD_CADENCE if pada % 2 == 0 else EVEN_CADENCE
        for j, w in enumerate(cadence):
            bit = 1 << (pada * 8 + 4 + j)
            if w == "L":
                req_l |= bit
            else:
                req_g |= bit
    return Masks(req_l, req_g)


def encode(lg: str) -> tuple[int, int]:
    """Return (L bits, G bits); `?` sets neither, so it never counts as a mismatch."""
    l_bits = g_bits = 0
    for i, w in enumerate(lg):
        if w == "L":
            l_bits |= 1 << i
        elif w == "G":
            g_bits |= 1 << i
    return l_bits, g_bits


def mismatch_lower_bound(lg: str, masks: Masks) -> int:
    l_bits, g_bits = encode(lg)
    return (masks.req_l & g_bits).bit_count() + (masks.req_g & l_bits).bit_count()
