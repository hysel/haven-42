#!/usr/bin/env python3
"""Render a compact validated Apple-Silicon model qualification summary."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts/validate-alpha2-macos-model-qualification-result.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("mac_result_validator", VALIDATOR_PATH)
    if not spec or not spec.loader:
        raise ValueError("validator-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def average_rate(metrics: dict[str, Any]) -> float | None:
    rates = [item.get("tokensPerSecond") for item in metrics.values() if isinstance(item, dict) and isinstance(item.get("tokensPerSecond"), (int, float))]
    return round(sum(rates) / len(rates), 3) if rates else None


def summarize(result: dict[str, Any]) -> dict[str, Any]:
    records = []
    for item in result["results"]:
        records.append({
            "modelId": item["modelId"],
            "model": item["model"],
            "status": item["status"],
            "checks": {name: check["status"] for name, check in item["checks"].items()},
            "averageTokensPerSecond": average_rate(item["metrics"]),
            "codingSurfaceStatus": item["codingSurfaceStatus"],
            "codingRecommendationEligible": item["codingRecommendationEligible"],
            "promotionBlock": item.get("promotionBlock"),
        })
    return {
        "kind": "haven42-apple-silicon-model-qualification-summary",
        "status": result["status"],
        "testContractVersion": result["testContract"]["version"],
        "models": len(records),
        "passed": sum(item["status"] == "passed" for item in records),
        "failed": sum(item["status"] == "failed" for item in records),
        "temporaryModelsRemoved": sum(item["removed"] is True for item in result["cleanup"]),
        "temporaryModelsExpected": result["modelsPulled"],
        "results": records,
        "rawPromptsOrResponsesRetained": False,
        "privateIdentityRetained": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    validator = load_validator()
    runner = validator.load_runner()
    plan_path = args.plan or validator.PLAN_PATH
    result = runner.load_json(args.result)
    plan = runner.load_json(plan_path)
    validator.validate_result(result, plan, runner)
    print(json.dumps(summarize(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
