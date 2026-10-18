"""Shared frozen value types (§4.1, §4.4, §41)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from padya.errors import OffsetError

BoundaryResolution = Literal[
    "exact_between_codepoints", "inside_grapheme", "shared_surface", "unresolved"
]


@dataclass(slots=True, frozen=True)
class Span:
    """Code-point interval into Document.text, end exclusive (INV-2)."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise OffsetError(f"invalid span [{self.start},{self.end})")

    def as_list(self) -> list[int]:
        return [self.start, self.end]


@dataclass(slots=True, frozen=True)
class OriginEdge:
    """Many-to-many alignment edge between source and analysis (OFF-1, §41)."""

    src: Span | None  # None = hypothetical/zero-input analysis operation
    analysis: Span | None  # None = omitted source character (tombstone)
    rule_id: str
    kind: Literal["copy", "expand", "contract", "zero_src", "zero_analysis"]


@dataclass(slots=True, frozen=True)
class BoundaryAnchor:
    """Typed boundary (OFF-7…OFF-12, EDGE-2): offset only when exact."""

    resolution: BoundaryResolution
    offset: int | None
    covering_src: Span | None
    analysis_left: int | None
    analysis_right: int | None
    transformation: str | None
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        exact = self.resolution == "exact_between_codepoints"
        if exact != (self.offset is not None):
            raise OffsetError(f"EDGE-2: offset must be set iff exact ({self.resolution})")

    def to_json(self) -> dict:
        return {
            "resolution": self.resolution,
            "offset": self.offset,
            "covering_src": self.covering_src.as_list() if self.covering_src else None,
            "analysis_left": self.analysis_left,
            "analysis_right": self.analysis_right,
            "transformation": self.transformation,
            "evidence_ids": list(self.evidence_ids),
        }
