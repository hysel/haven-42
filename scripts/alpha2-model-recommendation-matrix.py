#!/usr/bin/env python3
"""Exercise recommendation explanations across deterministic synthetic profiles."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("recommendation_report_matrix", ROOT / "scripts/alpha2-model-recommendation-report.py")
assert SPEC and SPEC.loader
REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT)


def _evidence(model: dict[str, Any], profile: dict[str, Any], policy_digest: str, index: int) -> dict[str, Any]:
    return {
        "evidenceId": f"synthetic-{index}-{model['id']}",
        "modelId": model["id"],
        "manifestDigest": model["manifestDigest"],
        "platformFamily": profile["platformFamily"],
        "operatingSystemId": profile["operatingSystemId"],
        "architecture": profile["architecture"],
        "backendMode": profile["backendMode"],
        "provider": profile["provider"],
        "providerVersion": profile["providerVersion"],
        "minimumTestedSystemMemoryGiB": max(0.1, min(profile["systemMemoryGiB"], model["minimumSystemMemoryGiB"])),
        "minimumTestedUsableGpuMemoryGiB": 0 if profile["backendMode"] == "cpu" else max(0.1, min(profile["usableGpuMemoryGiB"], model["minimumUsableGpuMemoryGiB"])),
        "capabilities": list(profile["requestedCapabilities"]),
        "status": "passed",
        "selectorPolicyCanonicalSha256": policy_digest,
    }


def build_matrix(fixtures: dict[str, Any]) -> dict[str, Any]:
    if fixtures.get("kind") != "alpha2-model-selection-synthetic-fixtures" or fixtures.get("productAdmission") is not False:
        raise ValueError("only non-product synthetic selector fixtures are accepted")
    policy, catalog = REPORT.SELECTOR.load_policy()
    digest = REPORT.SELECTOR.canonical_sha256(policy)
    by_id = {model["id"]: model for model in catalog["models"]}
    rows = []
    for index, case in enumerate(fixtures.get("cases", []), start=1):
        profile = case["profile"]
        evidence = [_evidence(by_id[model_id], profile, digest, index) for model_id in case["evidencedModelIds"]]
        explanation = REPORT.explain(profile, evidence)
        actual = explanation["selectorDecision"]["selectedModelId"]
        if actual != case["expectedModelId"]:
            raise ValueError(f"fixture decision drift: {case['id']}")
        rows.append({
            "caseId": case["id"], "expectedModelId": case["expectedModelId"],
            "selectedModelId": actual, "runtimeRoute": explanation["runtimeRoute"],
            "candidateDecisions": explanation["candidates"],
        })
    return {
        "schemaVersion": 1,
        "kind": "alpha2-model-recommendation-synthetic-matrix",
        "productAdmission": False,
        "caseCount": len(rows),
        "cases": rows,
        "downloadsPerformed": False,
        "policyChanged": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/fixtures/alpha-2-model-selection-cases.json")
    args = parser.parse_args()
    try:
        result = build_matrix(json.loads(args.fixtures.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, ValueError, REPORT.SELECTOR.SelectionError) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
