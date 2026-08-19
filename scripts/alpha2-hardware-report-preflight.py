#!/usr/bin/env python3
"""Report whether two hardware cells are ready for final comparison publication."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("preflight_compare", ROOT / "scripts/alpha2-hardware-cross-os-report.py")
assert SPEC and SPEC.loader
COMPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPARE)


def preflight(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    comparison = COMPARE.build_comparison(first, second)
    blockers: list[str] = []
    for label, value in (("first", first), ("second", second)):
        if value.get("status") != COMPARE.COMPLETE:
            blockers.append(f"{label}-cell-incomplete")
        freshness = value.get("sourceBindings", {}).get("inputFreshness")
        if not isinstance(freshness, dict) or freshness.get("status") != "fresh":
            blockers.append(f"{label}-cell-input-bindings-not-fresh")
    if comparison["pendingCells"]:
        blockers.append("comparison-has-not-run-cells")
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-hardware-report-preflight",
        "status": "ready" if not blockers else "blocked",
        "blockers": blockers,
        "comparisonStatus": comparison["status"],
        "commonPassCount": len(comparison["commonPasses"]),
        "divergenceCount": len(comparison["divergences"]),
        "pendingCellCount": len(comparison["pendingCells"]),
        "publicationAllowed": not blockers,
        "automaticPromotionAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = preflight(COMPARE.read_result(args.first), COMPARE.read_result(args.second))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
