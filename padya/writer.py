"""Stage 10: atomic output writer (§13, §24.1, §26.6, §26.8).

Outputs are written to temporary files, fsynced and renamed only after every
file has been produced; any failure leaves no partial final outputs.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Iterable

from padya.pipeline import Detection

_SAFE = str.maketrans({c: "_" for c in '/\\:*?"<>|'})


def _dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_temp(directory: Path, lines: Iterable[str]) -> Path:
    fd, name = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".part")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        for line in lines:
            fh.write(line)
            fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    return Path(name)


def output_dir_for(base: Path, doc_id: str) -> Path:
    """§26.9: sanitise document ids; never allow path traversal."""
    safe = doc_id.translate(_SAFE).strip(".") or "doc"
    out = (base / safe).resolve()
    if base.resolve() not in out.parents:
        raise ValueError(f"unsafe output path for {doc_id!r}")
    return out


def write_detection(det: Detection, base: Path, *, emit_candidates: bool = False) -> Path:
    out = output_dir_for(base, det.doc.doc_id)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "verses.jsonl": [_dumps(v) for v in det.verses],
        "regions.jsonl": [_dumps(r) for r in (*det.syllable_regions, *det.char_regions)],
        "report.json": [json.dumps(det.report, ensure_ascii=False, sort_keys=True, indent=2)],
    }
    if det.suspects:
        files["suspects.jsonl"] = [_dumps(s) for s in det.suspects]
    if emit_candidates:
        files["candidates.jsonl"] = [_dumps(c) for c in det.candidates]
    temps: dict[str, Path] = {}
    try:
        for name, lines in files.items():
            temps[name] = _write_temp(out, lines)
        for name, tmp in temps.items():
            os.replace(tmp, out / name)
    finally:
        for tmp in temps.values():
            if tmp.exists():
                tmp.unlink()
    return out
