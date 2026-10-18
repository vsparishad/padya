#!/usr/bin/env python3
"""Compile the metre registry and cross-check the verification ledger (§25, §5.2, T25).

Exit 0 only when the registry compiles and the ledger agrees with metres.yaml.
Mechanical agreement is not philological verification (REL6-5).
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from padya.config import load_config  # noqa: E402
from padya.errors import RegistryError  # noqa: E402
from padya.metres.registry import compile_registry  # noqa: E402

LEDGER = ROOT / "data" / "metres" / "verification.tsv"


def ledger_problems(registry, ledger_path: Path) -> list[str]:
    with ledger_path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    variants = next(m for m in registry["metres"] if m["id"] == "anustubh")["variants"]
    problems = []
    for row in rows:
        want = variants.get(row["variant"], {}).get("status")
        if row["status"] != want:
            problems.append(f"ledger {row['metre']}/{row['variant']}: {row['status']} != metres.yaml {want}")
        if row["status"] == "verified" and not (row["primary_reference"] and row["second_reference"]):
            problems.append(f"ledger {row['variant']}: verified without two references")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    args = parser.parse_args(argv)
    registry = load_config().metres
    try:
        compiled = compile_registry(registry)
    except RegistryError as exc:
        print(exc)
        return 1
    problems = ledger_problems(registry, args.ledger)
    for p in problems:
        print("FAIL:", p)
    statuses = {}
    for c in compiled:
        statuses[c.status] = statuses.get(c.status, 0) + 1
    print(f"{len(compiled)} entries compiled; statuses {statuses}; ledger problems {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
