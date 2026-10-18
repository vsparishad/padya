"""Anuṣṭubh (śloka) grammar: pathyā plus the four classical vipulās (§5.2 AN-1…AN-6, §25.1, M2.5).

`gate` is the exact verdict. The bitmask prefilter in `bitmask.py` may only reject
early; acceptance always comes from here (SRCH-2). `slow_gate` is the deliberately
naive exhaustive oracle used to test `gate` (TEST6-6).

Odd-pāda variants (§5.2 table; syllables are 1-based, `lg` slots 0-based):

| variant     | 5–7   | syl 4 | 2–4 constraint                         | caesura (strict profile) |
| pathyā      | L G G | any   | not LLL / LLG                          | none                     |
| na-vipulā   | L L L | G     | in {GGG, LGG, GLG}                     | none                     |
| bha-vipulā  | G L L | G     | GLG; exceptional GGG                   | after 4 for the GGG form |
| ma-vipulā   | G G G | G     | GLG                                    | after 5                  |
| ra-vipulā   | G L G | G     | not LL*                                | after 4                  |

A caesura is a *visible* word end at that syllable. A boundary fused by sandhi is not
visible to the scanner (OFF-7); profile `vipula_caesura: lenient` then admits the pāda
and reports `caesura_unverified` instead of rejecting it (T32: never a silent pathyā).
Even pādas have a single form (AN-1). Only variants listed in the baseline mode are
tried, in the fixed order pathyā → na → bha → ma → ra (deterministic, DEC-22).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from math import log
from typing import Mapping, Sequence

from padya.errors import ConfigError

PADA = 8
VERSE = 32
HALF = 16
CONSTRAINED = range(1, 7)  # 0-based slots 2–7; slots 1 and 8 are free/anceps
PATHYA = "pathya"
VARIANT_ORDER = (PATHYA, "na_vipula", "bha_vipula", "ma_vipula", "ra_vipula")
IMPLEMENTED = frozenset(VARIANT_ORDER)
CADENCE = {PATHYA: "LGG", "na_vipula": "LLL", "bha_vipula": "GLL", "ma_vipula": "GGG", "ra_vipula": "GLG"}
EVEN_CADENCE = "LGL"
# word-end slot (0-based) that must be visible for the variant under a strict profile
CAESURA_AFTER = {"ma_vipula": 4, "ra_vipula": 3}


@dataclass(slots=True, frozen=True)
class GateResult:
    ok: bool
    cost: float  # uncertainty cost charged for `?` slots (SC-7, T33)
    variants: tuple[str, ...]  # per pāda, e.g. ("pathya", "even", "ra_vipula", "even")
    uncertain_slots: tuple[int, ...]
    reason: str  # first failing rule, or "ok"
    caesura_unverified: tuple[int, ...] = ()  # pāda indexes admitted without a visible caesura


@dataclass(slots=True, frozen=True)
class Profile:
    odd_forbidden: frozenset[str]
    even_forbidden: frozenset[str]
    cost_uncertain: float
    caesura: str = "required"  # "required" | "lenient"

    @classmethod
    def from_config(cls, profile: Mapping, weights: Mapping) -> "Profile":
        caesura = str(profile.get("vipula_caesura", "required"))
        if caesura not in ("required", "lenient"):
            raise ConfigError(f"vipula_caesura must be required|lenient, not {caesura!r}")
        return cls(
            odd_forbidden=frozenset(profile["odd_pada_forbidden_2_4"]),
            even_forbidden=frozenset(profile["even_pada_forbidden_2_4"]),
            cost_uncertain=float(weights["edits"]["cost_uncertain"]),
            caesura=caesura,
        )


def check_variants(enabled: Sequence[str]) -> None:
    """Fail closed on any variant that has no implemented predicate (AN-3)."""
    unknown = [v for v in enabled if v not in IMPLEMENTED]
    if unknown:
        raise ConfigError(f"anuṣṭubh variants {unknown} are not implemented (ta-vipulā/AN-9 are off)")
    if PATHYA not in enabled:
        raise ConfigError("anuṣṭubh variants must include pathya")


def pada_ok(lg: str, odd: bool, profile: Profile) -> bool:
    """AN-1/AN-2 pathyā test on a fully specified 8-slot L/G string."""
    return odd_variant_ok(lg, PATHYA, profile) if odd else even_ok(lg, profile)


def even_ok(lg: str, profile: Profile) -> bool:
    return lg[4:7] == EVEN_CADENCE and lg[1:4] not in profile.even_forbidden


def odd_variant_ok(lg: str, variant: str, profile: Profile, caesura_visible: bool = True) -> bool:
    """Structural predicate for one odd-pāda variant on a fully specified string.

    `caesura_visible` says whether the word end the variant may require is visible;
    it is only consulted when the profile requires caesurae.
    """
    if lg[4:7] != CADENCE[variant]:
        return False
    mid = lg[1:4]
    if variant == PATHYA:
        return mid not in profile.odd_forbidden
    if lg[3] != "G":
        return False
    need_caesura = profile.caesura == "required" and not caesura_visible
    if variant == "na_vipula":
        return mid in ("GGG", "LGG", "GLG")
    if variant == "bha_vipula":
        if mid == "GLG":
            return True
        return mid == "GGG" and not need_caesura  # exceptional ma-bha form needs caesura after 4
    if variant == "ma_vipula":
        return mid == "GLG" and not need_caesura
    if variant == "ra_vipula":
        return not mid.startswith("LL") and not need_caesura
    raise ConfigError(f"unknown variant {variant!r}")


def _caesura_slot(variant: str, mid: str) -> int | None:
    if variant == "bha_vipula":
        return 3 if mid == "GGG" else None
    return CAESURA_AFTER.get(variant)


def _odd_pada_gate(lg: str, variants: Sequence[str], profile: Profile, word_ends: Sequence[bool] | None,
                   ) -> tuple[str | None, int, bool]:
    """First variant (in VARIANT_ORDER) some completion of `?` slots satisfies.

    Returns (variant, charged ? count, caesura_unverified).
    """
    unknown = [i for i, w in enumerate(lg) if w == "?"]
    for variant in VARIANT_ORDER:
        if variant not in variants:
            continue
        for values in product("LG", repeat=len(unknown)):
            chars = list(lg)
            for i, v in zip(unknown, values):
                chars[i] = v
            full = "".join(chars)
            slot = _caesura_slot(variant, full[1:4])
            visible = slot is None or (word_ends is not None and bool(word_ends[slot]))
            if odd_variant_ok(full, variant, profile, caesura_visible=visible):
                charged = sum(1 for i in unknown if i in CONSTRAINED)
                return variant, charged, (slot is not None and not visible)
    return None, 0, False


def _even_pada_gate(lg: str, profile: Profile) -> tuple[bool, int]:
    unknown = [i for i, w in enumerate(lg) if w == "?"]
    for values in product("LG", repeat=len(unknown)):
        chars = list(lg)
        for i, v in zip(unknown, values):
            chars[i] = v
        if even_ok("".join(chars), profile):
            return True, sum(1 for i in unknown if i in CONSTRAINED)
    return False, 0


def gate(lg: str, profile: Profile, budget: float, variants: Sequence[str] = (PATHYA,),
         word_ends: Sequence[bool] | None = None) -> GateResult:
    """Gate for a full verse (32 slots, AN-5) or one hemistich (16 slots, AN-6).

    `word_ends[i]` says whether slot i ends a visible word (caesura evidence).
    """
    if len(lg) not in (VERSE, HALF):
        return GateResult(False, 0.0, (), (), "length")
    if word_ends is not None and len(word_ends) != len(lg):
        raise ValueError("word_ends must align with lg")
    charged = 0
    found: list[str] = []
    unverified: list[int] = []
    for p in range(len(lg) // PADA):
        seg = slice(p * PADA, (p + 1) * PADA)
        if p % 2 == 0:
            variant, n, no_caesura = _odd_pada_gate(lg[seg], variants, profile,
                                                   None if word_ends is None else word_ends[seg])
            if variant is None:
                return GateResult(False, 0.0, (), (), f"pada{p + 1}")
            found.append(variant)
            if no_caesura:
                unverified.append(p)
        else:
            ok, n = _even_pada_gate(lg[seg], profile)
            if not ok:
                return GateResult(False, 0.0, (), (), f"pada{p + 1}")
            found.append("even")
        charged += n
    cost = charged * profile.cost_uncertain
    uncertain = tuple(i for i, w in enumerate(lg) if w == "?" and (i % PADA) in CONSTRAINED)
    if cost > budget + 1e-12:
        return GateResult(False, cost, (), uncertain, "budget")
    return GateResult(True, cost, tuple(found), uncertain, "ok", tuple(unverified))


def slow_gate(lg: str, profile: Profile, budget: float, variants: Sequence[str] = (PATHYA,),
              word_ends: Sequence[bool] | None = None) -> tuple[bool, float]:
    """Exhaustive oracle: enumerate every completion of the whole string and every variant."""
    if len(lg) not in (VERSE, HALF):
        return False, 0.0
    unknown = [i for i, w in enumerate(lg) if w == "?"]
    accepted = False
    for values in product("LG", repeat=len(unknown)):
        chars = list(lg)
        for i, v in zip(unknown, values):
            chars[i] = v
        s = "".join(chars)
        ok = True
        for p in range(len(s) // PADA):
            seg = s[p * PADA:(p + 1) * PADA]
            if p % 2 == 1:
                ok = even_ok(seg, profile)
            else:
                ok = False
                for variant in variants:
                    slot = _caesura_slot(variant, seg[1:4])
                    visible = slot is None or (word_ends is not None and bool(word_ends[p * PADA + slot]))
                    if odd_variant_ok(seg, variant, profile, caesura_visible=visible):
                        ok = True
                        break
            if not ok:
                break
        if ok:
            accepted = True
            break
    if not accepted:
        return False, 0.0
    cost = sum(1 for i in unknown if (i % PADA) in CONSTRAINED) * profile.cost_uncertain
    return cost <= budget + 1e-12, cost


@lru_cache(maxsize=None)
def _variant_count(variant: str, profile: Profile) -> int:
    """Fully specified 8-slot strings the variant admits (caesura taken as visible)."""
    if variant == "even":
        return sum(even_ok("".join(s), profile) for s in product("LG", repeat=PADA))
    return sum(odd_variant_ok("".join(s), variant, profile) for s in product("LG", repeat=PADA))


def pada_language_size(variant: str, profile: Profile) -> int:
    return _variant_count(variant, profile)


def language_size(profile: Profile, variants: Sequence[str] = (PATHYA,)) -> int:
    """Number of fully specified 32-slot strings admitted by the enabled variants."""
    odd = sum(_variant_count(v, profile) for v in variants)
    return (odd * _variant_count("even", profile)) ** 2


def log_language_size(profile: Profile, variants: Sequence[str] = (PATHYA,)) -> float:
    return log(language_size(profile, variants))


def log_language_size_for(per_pada: Sequence[str], profile: Profile) -> float:
    """log of the product of per-pāda set sizes for a concrete variant assignment (BASE-9)."""
    return sum(log(_variant_count(v, profile)) for v in per_pada)
