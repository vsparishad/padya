"""Metre registry compiler (§25, §32.2, TEST6-4/5, T25).

The registry is code: every fixed-pattern entry must satisfy
`len(pattern) == syllables_per_pada == len(expand(gana_tokens))` and
`expand(gana_tokens) == pattern`, or compilation fails with a line-level diagnosis.
Only `verified` entries may become active (§5.3); BASE-A activates none of them.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from padya.errors import RegistryError

GANA = {
    "ya": "LGG", "ma": "GGG", "ta": "GGL", "ra": "GLG", "ja": "LGL",
    "bha": "GLL", "na": "LLL", "sa": "LLG", "la": "L", "ga": "G",
}
STATUSES = frozenset({"verified", "needs_verification", "blocked"})


@dataclass(slots=True, frozen=True)
class CompiledMetre:
    id: str
    cls: str
    pattern: str | None
    status: str
    n: int | None = None  # syllables per pāda (sama/mixture) or per odd pāda (ardhasama)
    final_anceps: bool = True
    components: tuple[str, ...] = ()  # mixture: component ids
    odd_pattern: str | None = None  # ardhasama
    even_pattern: str | None = None
    mixed_lengths: bool = False  # mixture whose components differ in length (11/12 upajāti)

    def pada_patterns(self, by_id: Mapping[str, "CompiledMetre"]) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """(odd-pāda patterns, even-pāda patterns) admitted by this metre."""
        if self.cls == "sama":
            return (self.pattern,), (self.pattern,)
        if self.cls == "mixture":
            pats = tuple(by_id[c].pattern for c in self.components)
            return pats, pats
        if self.cls == "ardhasama":
            return (self.odd_pattern,), (self.even_pattern,)
        raise RegistryError(f"{self.id}: no fixed patterns for class {self.cls}")


def expand(tokens: Iterable[str]) -> str:
    out = []
    for tok in tokens:
        if tok not in GANA:
            raise RegistryError(f"unknown gaṇa token {tok!r}")
        out.append(GANA[tok])
    return "".join(out)


def _compile_entry(entry: Mapping) -> tuple[CompiledMetre | None, list[str]]:
    mid, cls = entry.get("id", "?"), entry.get("class")
    status = entry.get("verification_status")
    errors = []
    if status not in STATUSES:
        errors.append(f"{mid}: invalid verification_status {status!r}")
    if cls == "sama":
        pattern, n = entry.get("pattern", ""), entry.get("syllables_per_pada")
        try:
            derived = expand(entry.get("gana_tokens", []))
        except RegistryError as exc:
            return None, [f"{mid}: {exc}"]
        if len(pattern) != n:
            errors.append(f"{mid}: len(pattern)={len(pattern)} != syllables_per_pada={n}")
        if derived != pattern:
            errors.append(f"{mid}: expand({list(entry.get('gana_tokens', []))})={derived} != pattern {pattern}")
        return (None if errors else CompiledMetre(mid, cls, pattern, status, n, bool(entry.get("final_anceps", True)))), errors
    if cls == "ardhasama":
        for key in ("odd_pattern", "even_pattern"):
            if not set(entry.get(key, "")) <= set("LG") or not entry.get(key):
                errors.append(f"{mid}: {key} must be a non-empty L/G string")
        return (None if errors else CompiledMetre(mid, cls, None, status, len(entry.get("odd_pattern", "")),
                                                   bool(entry.get("final_anceps", True)), (),
                                                   entry.get("odd_pattern"), entry.get("even_pattern"))), errors
    if cls == "mixture":
        comps = tuple(entry.get("components", ()) or ())
        if not comps:
            errors.append(f"{mid}: mixture without components")
        return (None if errors else CompiledMetre(mid, cls, None, status, entry.get("syllables_per_pada"),
                                                   bool(entry.get("final_anceps", True)), comps,
                                                   mixed_lengths=bool(entry.get("mixed_lengths")))), errors
    if cls == "grammar":
        return (None if errors else CompiledMetre(mid, cls, None, status)), errors
    return None, errors + [f"{mid}: unknown class {cls!r}"]


def compile_registry(registry: Mapping) -> tuple[CompiledMetre, ...]:
    """Compile all entries; raise RegistryError listing every failure (fail closed)."""
    compiled, errors, ids, aliases = [], [], set(), {}
    for pos, entry in enumerate(registry.get("metres", ())):
        metre, errs = _compile_entry(entry)
        errors.extend(f"entry #{pos + 1} {e}" for e in errs)
        mid = entry.get("id")
        if mid in ids:
            errors.append(f"entry #{pos + 1} duplicate id {mid!r}")
        ids.add(mid)
        for alias in entry.get("aliases", ()) or ():
            if alias in aliases or alias in ids:
                errors.append(f"entry #{pos + 1} alias collision {alias!r}")
            aliases[alias] = mid
        if metre:
            compiled.append(metre)
    known = {c.id: c for c in compiled}
    for entry in registry.get("metres", ()):
        for comp in entry.get("components", ()) or ():
            if comp not in known:
                errors.append(f"{entry.get('id')}: mixture component {comp!r} not compiled")
            elif not entry.get("mixed_lengths") and known[comp].n != entry.get("syllables_per_pada"):
                errors.append(f"{entry.get('id')}: component {comp!r} has a different pāda length")
    if errors:
        raise RegistryError("metre registry failed to compile:\n" + "\n".join(errors))
    return tuple(compiled)


def active_metres(compiled: Iterable[CompiledMetre], requested: Iterable[str], allow_unverified: bool) -> tuple[str, ...]:
    """§5.3: unverified entries cannot leak into the active set unless explicitly allowed."""
    by_id = {c.id: c for c in compiled}
    active = []
    for mid in requested:
        metre = by_id.get(mid)
        if metre is None:
            raise RegistryError(f"requested metre {mid!r} is not in the registry")
        if metre.status == "blocked" or (metre.status != "verified" and not allow_unverified):
            raise RegistryError(f"metre {mid!r} has status {metre.status}; refusing to enable it")
        active.append(mid)
    return tuple(active)
