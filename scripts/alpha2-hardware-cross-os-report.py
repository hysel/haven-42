#!/usr/bin/env python3
"""Compare exact hardware qualification cells without generalizing either one."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,99}$")
COMPLETE = "exact-profile-engineering-evidence-complete"
IN_PROGRESS = "in-progress-local-review-only"


def validate_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schemaVersion") != 1 or value.get("kind") != "haven42-alpha2-hardware-qualification-result":
        raise ValueError("invalid hardware qualification result identity")
    if value.get("status") not in {COMPLETE, IN_PROGRESS}:
        raise ValueError("invalid hardware qualification result status")
    for field in ("containsPrivateMachineIdentity", "containsNetworkIdentity", "containsRawPromptsOrResponses"):
        if value.get(field) is not False:
            raise ValueError(f"comparison input is not sanitized: {field}")
    bindings = value.get("sourceBindings")
    if not isinstance(bindings, dict):
        raise ValueError("source bindings are missing")
    for field in ("inventoryCanonicalSha256", "matrixCanonicalSha256"):
        digest = bindings.get(field)
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"invalid source binding: {field}")
    freshness = bindings.get("inputFreshness")
    if value["status"] == COMPLETE:
        if not isinstance(freshness, dict) or freshness.get("status") != "fresh":
            raise ValueError("complete result lacks fresh exact input bindings")
        if not isinstance(freshness.get("sha256"), dict) or not freshness["sha256"]:
            raise ValueError("complete result lacks bound input digests")
    outcomes(value)
    return value


def read_result(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError(f"unsafe result file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    return validate_result(value)


def outcomes(result: dict[str, Any]) -> dict[str, str]:
    gate = result.get("coreTaskGate", {})
    passed = gate.get("passed", [])
    failed = gate.get("failed", {})
    if not isinstance(passed, list) or not isinstance(failed, dict):
        raise ValueError("coreTaskGate has an invalid shape")
    if any(not isinstance(item, str) or not SAFE_ID.fullmatch(item) for item in passed):
        raise ValueError("coreTaskGate has an unsafe passed model id")
    if any(not isinstance(item, str) or not SAFE_ID.fullmatch(item) for item in failed):
        raise ValueError("coreTaskGate has an unsafe failed model id")
    if any(not isinstance(cells, list) or not cells for cells in failed.values()):
        raise ValueError("failed models require exact failure cells")
    if set(passed) & set(failed):
        raise ValueError("a model cannot both pass and fail")
    return {**{item: "passed" for item in passed}, **{item: "failed" for item in failed}}


def build_comparison(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    first, second = validate_result(first), validate_result(second)
    if first.get("environment", {}).get("accelerator") != second.get("environment", {}).get("accelerator"):
        raise ValueError("hardware accelerator cells do not match")
    if first.get("qualificationProfileId") != second.get("qualificationProfileId"):
        raise ValueError("qualification profiles do not match")
    for field in ("inventoryCanonicalSha256", "matrixCanonicalSha256"):
        if first["sourceBindings"][field] != second["sourceBindings"][field]:
            raise ValueError(f"source binding mismatch: {field}")
    first_results, second_results = outcomes(first), outcomes(second)
    models = sorted(set(first_results) | set(second_results))
    cells = []
    for model in models:
        first_outcome = first_results.get(model, "not-run")
        second_outcome = second_results.get(model, "not-run")
        comparable = first_outcome != "not-run" and second_outcome != "not-run"
        cells.append({
            "modelId": model,
            "first": first_outcome,
            "second": second_outcome,
            "comparable": comparable,
            "divergent": comparable and first_outcome != second_outcome,
        })
    complete = all(item.get("status") == COMPLETE for item in (first, second))
    if complete and any(not cell["comparable"] for cell in cells):
        raise ValueError("complete results have different model cell sets")
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-hardware-cross-os-comparison",
        "status": "complete" if complete else "incomplete-local-review-only",
        "accelerator": first["environment"]["accelerator"],
        "qualificationProfileId": first["qualificationProfileId"],
        "sourceBindings": {
            "inventoryCanonicalSha256": first["sourceBindings"]["inventoryCanonicalSha256"],
            "matrixCanonicalSha256": first["sourceBindings"]["matrixCanonicalSha256"],
            "firstInputFreshnessEvidenceId": first["sourceBindings"]["inputFreshness"]["evidenceId"] if first["sourceBindings"]["inputFreshness"] else None,
            "secondInputFreshnessEvidenceId": second["sourceBindings"]["inputFreshness"]["evidenceId"] if second["sourceBindings"]["inputFreshness"] else None,
        },
        "cells": cells,
        "commonPasses": [cell["modelId"] for cell in cells if cell["first"] == cell["second"] == "passed"],
        "divergences": [cell for cell in cells if cell["divergent"]],
        "pendingCells": [cell for cell in cells if not cell["comparable"]],
        "firstEnvironment": first["environment"],
        "secondEnvironment": second["environment"],
        "automaticDefaultChangeAllowed": False,
        "automaticSelectionEvidenceAllowed": False,
        "automaticSupportChangeAllowed": False,
        "crossOperatingSystemInheritanceAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = build_comparison(read_result(args.first), read_result(args.second))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(rendered, encoding="utf-8")
        temporary.replace(args.output)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
