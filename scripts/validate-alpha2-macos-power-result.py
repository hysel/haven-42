#!/usr/bin/env python3
"""Independently validate sanitized Apple SoC idle or model power evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json"
RUNNER_PATH = ROOT / "scripts/alpha2-macos-model-qualification.py"

class PowerResultError(ValueError):
    pass

def load_runner():
    spec = importlib.util.spec_from_file_location("mac_qualification_runner", RUNNER_PATH)
    if not spec or not spec.loader:
        raise PowerResultError("runner-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def require(condition: bool, code: str) -> None:
    if not condition:
        raise PowerResultError(code)

def validate_metric(value: Any, samples: int) -> None:
    require(isinstance(value, dict) and set(value) == {"samples", "minimum", "average", "maximum"}, "invalid-power-metric")
    require(value["samples"] == samples and samples >= 2, "invalid-power-sample-count")
    numbers = [value[key] for key in ("minimum", "average", "maximum")]
    require(all(isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(item) and item >= 0 for item in numbers), "invalid-power-values")
    require(numbers[0] <= numbers[1] <= numbers[2], "invalid-power-order")

def validate_summary(value: Any) -> None:
    require(isinstance(value, dict), "invalid-power-summary")
    require(value.get("schemaVersion") == 1 and value.get("kind") == "haven42-sanitized-macos-power-summary", "invalid-power-summary")
    power = value.get("powerMilliwatts")
    require(isinstance(power, dict) and set(power) == {"cpu", "gpu", "ane", "combined"}, "invalid-power-channels")
    samples = power["combined"].get("samples") if isinstance(power["combined"], dict) else None
    require(isinstance(samples, int) and not isinstance(samples, bool), "invalid-power-sample-count")
    for item in power.values():
        validate_metric(item, samples)
    validate_metric(value.get("gpuActiveResidencyPercent"), samples)
    levels = value.get("thermalPressureLevels")
    require(isinstance(levels, list) and levels and all(isinstance(item, str) and item for item in levels), "invalid-thermal-levels")
    require(value.get("rawTelemetryRetained") is False and value.get("privateIdentityRetained") is False, "unsafe-summary-retention")

def validate_result(value: Any, plan: dict[str, Any], runner: Any) -> None:
    require(isinstance(value, dict), "result-not-object")
    kind = value.get("kind")
    require(kind in {"haven42-sanitized-macos-idle-power-result", "haven42-sanitized-macos-model-power-result"}, "unexpected-result-kind")
    require(value.get("schemaVersion") == 1 and value.get("release") == plan["release"] and value.get("status") == "passed", "invalid-result-header")
    require(value.get("planCanonicalSha256") == runner.canonical_sha256(plan), "plan-binding-mismatch")
    require(value.get("runtime") == {key: plan["runtime"][key] for key in ("provider", "version", "artifactSha256", "transport")}, "runtime-binding-mismatch")
    profile = value.get("hardwareProfile")
    require(isinstance(profile, dict) and profile.get("profileId") == plan["hardwareProfile"]["id"], "hardware-profile-mismatch")
    require(profile.get("platformFamily") == "macos" and profile.get("architecture") == "arm64" and profile.get("backend") == "metal", "hardware-boundary-mismatch")
    validate_summary(value.get("appleSocPower"))
    require(value.get("measurementBoundary") == "Apple powermetrics CPU/GPU/ANE estimates; not wall-outlet or whole-system energy", "measurement-boundary-mismatch")
    require(value.get("rawTelemetryRetained") is False and value.get("privateIdentityRetained") is False, "unsafe-result-retention")
    for key in ("automaticDefaultChangeAllowed", "automaticSelectionEvidenceAllowed", "automaticSupportChangeAllowed"):
        require(value.get(key) is False, "promotion-authority-present")
    if kind == "haven42-sanitized-macos-idle-power-result":
        require("model" not in value and "workload" not in value, "idle-result-contains-workload")
        precondition = value.get("precondition")
        require(isinstance(precondition, dict) and precondition.get("loadedModels") == 0 and precondition.get("generationWorkloadActive") is False, "invalid-idle-precondition")
        return
    candidates = runner.validate_plan(plan, ROOT)
    model = value.get("model")
    require(isinstance(model, dict) and model.get("modelId") in candidates, "unknown-model")
    candidate = candidates[model["modelId"]]
    require(model == {key: candidate[key] for key in ("modelId", "model", "manifestDigest", "modelBytes")}, "model-binding-mismatch")
    workload = value.get("workload")
    require(isinstance(workload, dict) and workload.get("kind") == "bounded-repeat-generation", "invalid-workload")
    require(isinstance(workload.get("requests"), int) and workload["requests"] > 0, "invalid-request-count")
    require(isinstance(workload.get("outputTokens"), int) and workload["outputTokens"] > 0, "invalid-output-token-count")
    require(isinstance(workload.get("durationSeconds"), (int, float)) and workload["durationSeconds"] >= 8, "power-window-too-short")
    require(workload.get("responseRetained") is False and workload.get("fullMetalResidencyObserved") is True, "invalid-workload-boundary")
    cleanup = value.get("cleanup")
    require(isinstance(cleanup, dict) and cleanup.get("unloadPassed") is True and cleanup.get("temporaryModelRemoved") is not False, "cleanup-failed")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    args = parser.parse_args()
    runner = load_runner()
    try:
        plan = runner.load_json(args.plan)
        runner.validate_plan(plan, ROOT)
        validate_result(runner.load_json(args.result), plan, runner)
    except (PowerResultError, runner.QualificationError, OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps({"result": str(args.result), "status": "valid"}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
