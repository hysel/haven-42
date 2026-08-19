#!/usr/bin/env python3
"""Audit legacy coding evidence against the current complete-cell policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def audit(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schemaVersion") != 1 or value.get("kind") != "haven42-model-coding-agent-qualification-result":
        raise ValueError("unsupported coding qualification result")
    if value.get("automaticDefaultChangeAllowed") is not False or value.get("automaticSelectionEvidenceAllowed") is not False or value.get("automaticSupportChangeAllowed") is not False:
        raise ValueError("legacy result grants forbidden automatic authority")
    results = value.get("results")
    if not isinstance(results, list):
        raise ValueError("legacy result list is missing")
    rows = []
    passed_ids = []
    for item in results:
        model_id = item.get("modelId") if isinstance(item, dict) else None
        digest = item.get("manifestDigest") if isinstance(item, dict) else None
        if not isinstance(model_id, str) or not SAFE_ID.fullmatch(model_id) or not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ValueError("legacy model identity is invalid")
        legacy_pass = item.get("workflowScreen") == "passed"
        if legacy_pass:
            passed_ids.append(model_id)
        rows.append({
            "modelId": model_id,
            "legacyWorkflowScreen": item.get("workflowScreen", "not-run"),
            "currentCellStatus": "blocked",
            "currentCodingRecommendationEligible": False,
            "missingCurrentEvidence": [
                "exact-runtime-artifact-digest",
                "exact-hardware-profile-id",
                "surface-id-and-version",
                "all-policy-subchecks",
                "continue-cli-prerequisite-cell",
                "bounded-context-and-timeout-recovery-details",
                "unload-and-unintended-write-details",
            ],
        })
    declared = value.get("workflowScreenPassed")
    if not isinstance(declared, list) or len(declared) != len(set(declared)) or set(declared) != set(passed_ids):
        raise ValueError("legacy workflow pass summary does not match result rows")
    surfaces = value.get("editorSurfaceResults", [])
    if not isinstance(surfaces, list):
        raise ValueError("legacy editor surface results are invalid")
    surface_rows = []
    for item in surfaces:
        if not isinstance(item, dict) or not isinstance(item.get("surfaceId"), str):
            raise ValueError("legacy editor surface identity is invalid")
        surface_rows.append({
            "surfaceId": item["surfaceId"],
            "legacyStatus": item.get("status", "not-run"),
            "currentCellStatus": "blocked",
            "reason": "legacy-surface-record-does-not-contain-all-current-gates",
        })
    return {
        "schemaVersion": 1,
        "kind": "haven42-model-coding-agent-history-audit",
        "status": "legacy-evidence-retained-current-admission-blocked",
        "modelCount": len(rows),
        "models": rows,
        "surfaces": surface_rows,
        "codingRecommendationCount": 0,
        "automaticDefaultChangeAllowed": False,
        "rawEvidenceReinterpretationAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(json.loads(args.input.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
