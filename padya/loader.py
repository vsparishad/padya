"""Stage 1: loader and cleaner adapter (§4.1, §29, M0.5).

`Document.text` is exactly the decoded file content and is never altered
(INV-1, INV-7, EDGE-9). The §29 cleaner contract is a *schema expectation*
pending integration against real cleaner output; documents loaded through the
plain-text path are labelled `cleaner_version = "none"`.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping

from padya.config import freeze
from padya.errors import ContractError, OffsetError
from padya.types import Span

TierType = Literal["T", "P", "R", "unspecified"]
EXPECTED_OFFSETS = "cleaned_devanagari text (Python str indices, 0-based, end exclusive)"
PHONOLOGICAL_FLAGS = frozenset({"orphan_matra", "virama_then_matra", "double_virama", "latin_in_word"})
KNOWN_KINDS = frozenset({"flag", "vedic", "verse_number"})
RECEIPTS_DIR = Path(__file__).parent / "config"
_VERSE_NUMBER_RE = re.compile(r"^[0-9०-९][0-9०-९.\-]*$")


@dataclass(slots=True, frozen=True)
class CleanerRecord:
    kind: str
    start: int
    end: int
    payload: Mapping[str, Any]  # recursively frozen


@dataclass(slots=True, frozen=True)
class Document:
    doc_id: str
    path: str
    tier: TierType
    noise_per_1000: float | None
    text: str
    text_sha256: str
    cleaner_version: str
    records: tuple[CleanerRecord, ...]
    paragraphs: tuple[Span, ...]
    lines: tuple[Span, ...]
    warnings: tuple[str, ...] = ()
    synthetic: bool = False


def sha256_text(text: str) -> str:
    """SHA-256 of the UTF-8 bytes of the decoded source (EDGE-9)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _line_spans(text: str) -> tuple[Span, ...]:
    spans, start = [], 0
    for m in re.finditer("\n", text):
        spans.append(Span(start, m.start()))
        start = m.end()
    if start < len(text):
        spans.append(Span(start, len(text)))
    return tuple(spans)


def _paragraph_spans(text: str) -> tuple[Span, ...]:
    spans, start = [], 0
    for m in re.finditer(r"\n[ \t]*\n+", text):
        if m.start() > start:
            spans.append(Span(start, m.start()))
        start = m.end()
    if start < len(text):
        spans.append(Span(start, len(text)))
    return tuple(spans)


def _validate_records(records: Iterable[CleanerRecord], n: int) -> tuple[list[CleanerRecord], list[str]]:
    """§29.5: out-of-range or unsorted offsets fail closed."""
    out, warnings, prev = [], [], (-1, -1)
    for rec in records:
        if not (0 <= rec.start <= rec.end <= n):
            raise OffsetError(f"record {rec.kind} [{rec.start},{rec.end}) outside [0,{n}]")
        if (rec.start, rec.end) < prev:
            raise ContractError("cleaner records are not sorted by (start, end)")
        prev = (rec.start, rec.end)
        if rec.kind not in KNOWN_KINDS:
            warnings.append(f"unknown record kind {rec.kind!r} tolerated and ignored")
        if rec.kind == "verse_number" and not _VERSE_NUMBER_RE.match(str(rec.payload.get("number", ""))):
            warnings.append(f"verse_number {rec.payload.get('number')!r} is not numeric; D2 evidence only")
        out.append(rec)
    return out, warnings


def document_from_text(
    text: str,
    *,
    doc_id: str = "inline",
    path: str = "<inline>",
    tier: TierType = "T",
    records: Iterable[CleanerRecord] = (),
    cleaner_version: str = "none",
    noise_per_1000: float | None = None,
    warnings: Iterable[str] = (),
    synthetic: bool = False,
) -> Document:
    recs, rec_warnings = _validate_records(records, len(text))
    return Document(
        doc_id=doc_id, path=path, tier=tier, noise_per_1000=noise_per_1000,
        text=text, text_sha256=sha256_text(text), cleaner_version=cleaner_version,
        records=tuple(recs), paragraphs=_paragraph_spans(text), lines=_line_spans(text),
        warnings=tuple(warnings) + tuple(rec_warnings), synthetic=synthetic,
    )


def _read_text(path: Path) -> str:
    try:
        # newline="" keeps \r\n exactly as on disk (no implicit reflow, EDGE-9)
        with path.open("r", encoding="utf-8", newline="") as fh:
            return fh.read()
    except UnicodeDecodeError as exc:
        raise ContractError(f"{path}: not valid UTF-8 ({exc})") from exc


def load_plain_text(path: Path, *, tier: TierType = "unspecified") -> Document:
    """Load a plain UTF-8 file that did not come from the cleaner."""
    text = _read_text(path)
    return document_from_text(
        text, doc_id=path.stem, path=str(path), tier=tier,
        warnings=("plain-text input: no cleaner records, flags or Vedic exclusions",),
    )


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read {path}: {exc}") from exc


def known_receipts() -> dict[str, str]:
    """REC-1: cleaner version string → SHA-256 of the producer the adapter was attested against."""
    out = {}
    for path in sorted(RECEIPTS_DIR.glob("cleaner_receipt_*.json")):
        rc = _read_json(path)
        out[str(rc["cleaner_version_string"])] = str(rc["cleaner_sha256"])
    return out


def _receipt_check(manifest: Mapping[str, Any], strict: bool) -> list[str]:
    version = str(manifest.get("cleaner_version", "unknown"))
    if version in known_receipts():
        return []
    msg = f"REC-1: no integration receipt for cleaner version {version!r}; attested versions: {sorted(known_receipts())}"
    if strict:
        raise ContractError(msg)
    return [msg]


def _manifest_warnings(manifest: Mapping[str, Any]) -> list[str]:
    """§29.5 manifest handshake; raises for fatal conditions."""
    if manifest.get("offsets_refer_to") != EXPECTED_OFFSETS:
        raise ContractError(f"unexpected offsets_refer_to: {manifest.get('offsets_refer_to')!r}")
    options = manifest.get("options") or {}
    if options.get("reading_view"):
        raise ContractError("reading_view output joins words and is not detector input")
    warnings = []
    if options.get("strip_accents"):
        warnings.append("strip_accents: no vedic records exist; SV-5 has nothing to exclude")
    if options.get("sandhi_join"):
        warnings.append("sandhi_join: some word boundaries were closed; C-1/C-3 are weaker")
    if manifest.get("synthetic"):
        warnings.append("SYNTHETIC cleaner fixture: no compatibility claim with clean_sanskrit_corpus.py")
    return warnings


def _read_records(path: Path) -> list[CleanerRecord]:
    if not path.exists():
        raise ContractError(f"missing records sidecar {path}")
    records = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            rec = CleanerRecord(
                kind=str(obj["kind"]), start=int(obj["start"]), end=int(obj["end"]),
                payload=freeze({k: v for k, v in obj.items() if k not in ("kind", "start", "end")}),
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ContractError(f"{path}:{lineno}: malformed record ({exc})") from exc
        records.append(rec)
    return records


def load_cleaner_folder(folder: Path, *, strict: bool = False) -> list[Document]:
    """Adapter for the §29 cleaner output folder. Fails closed on any violation.

    `strict` turns the REC-1 missing-receipt warning into an error.
    """
    text_dir = folder / "cleaned_devanagari"
    manifest = _read_json(text_dir / "manifest.json")
    warnings = _manifest_warnings(manifest) + _receipt_check(manifest, strict)
    tier = manifest.get("source_tier", "unspecified")
    if tier not in ("T", "P", "R", "unspecified"):
        raise ContractError(f"unknown source_tier {tier!r}")
    report_path = folder / "cleaned_report.json"
    noise = {}
    if report_path.exists():
        noise = {f["rel_path"]: f.get("noise_per_1000") for f in _read_json(report_path).get("files", [])}
    docs = []
    for path in sorted(p for p in text_dir.rglob("*") if p.is_file() and p.name != "manifest.json"):
        rel = path.relative_to(text_dir).as_posix()
        records = _read_records(folder / "cleaned_records" / f"{rel}.jsonl")
        docs.append(document_from_text(
            _read_text(path), doc_id=rel, path=str(path), tier=tier, records=records,
            cleaner_version=str(manifest.get("cleaner_version", "unknown")),
            noise_per_1000=noise.get(rel), warnings=warnings,
            synthetic=bool(manifest.get("synthetic")),
        ))
    if not docs:
        raise ContractError(f"no documents under {text_dir}")
    return docs
