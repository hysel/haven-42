#!/usr/bin/env python3
"""Tests for the independent Apple SoC power-result validator."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mac_power_validator", ROOT / "scripts/validate-alpha2-macos-power-result.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
RUNNER = MODULE.load_runner()
PLAN = RUNNER.load_json(ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json")

def summary() -> dict:
    metric = {"samples": 10, "minimum": 1.0, "average": 2.0, "maximum": 3.0}
    return {"schemaVersion": 1, "kind": "haven42-sanitized-macos-power-summary", "powerMilliwatts": {name: dict(metric) for name in ("cpu", "gpu", "ane", "combined")}, "gpuActiveResidencyPercent": dict(metric), "thermalPressureLevels": ["nominal"], "rawTelemetryRetained": False, "privateIdentityRetained": False}

def common(kind: str) -> dict:
    return {"schemaVersion": 1, "kind": kind, "release": PLAN["release"], "status": "passed", "planCanonicalSha256": RUNNER.canonical_sha256(PLAN), "runtime": {key: PLAN["runtime"][key] for key in ("provider", "version", "artifactSha256", "transport")}, "hardwareProfile": {"profileId": PLAN["hardwareProfile"]["id"], "platformFamily": "macos", "architecture": "arm64", "backend": "metal", "systemMemoryGiB": 16.0}, "appleSocPower": summary(), "measurementBoundary": "Apple powermetrics CPU/GPU/ANE estimates; not wall-outlet or whole-system energy", "rawTelemetryRetained": False, "privateIdentityRetained": False, "automaticDefaultChangeAllowed": False, "automaticSelectionEvidenceAllowed": False, "automaticSupportChangeAllowed": False}

class PowerResultValidatorTests(unittest.TestCase):
    def test_accepts_idle_result(self) -> None:
        value = common("haven42-sanitized-macos-idle-power-result")
        value["precondition"] = {"loadedModels": 0, "generationWorkloadActive": False}
        MODULE.validate_result(value, PLAN, RUNNER)

    def test_accepts_model_result(self) -> None:
        value = common("haven42-sanitized-macos-model-power-result")
        candidate = RUNNER.validate_plan(PLAN, ROOT)["qwen35-2b-q8"]
        value["model"] = {key: candidate[key] for key in ("modelId", "model", "manifestDigest", "modelBytes")}
        value["workload"] = {"kind": "bounded-repeat-generation", "requests": 1, "outputTokens": 32, "durationSeconds": 10.0, "responseRetained": False, "fullMetalResidencyObserved": True}
        value["cleanup"] = {"unloadPassed": True, "temporaryModelRemoved": True}
        MODULE.validate_result(value, PLAN, RUNNER)

    def test_rejects_short_power_window(self) -> None:
        value = common("haven42-sanitized-macos-model-power-result")
        candidate = RUNNER.validate_plan(PLAN, ROOT)["qwen35-2b-q8"]
        value["model"] = {key: candidate[key] for key in ("modelId", "model", "manifestDigest", "modelBytes")}
        value["workload"] = {"kind": "bounded-repeat-generation", "requests": 1, "outputTokens": 32, "durationSeconds": 2.0, "responseRetained": False, "fullMetalResidencyObserved": True}
        value["cleanup"] = {"unloadPassed": True, "temporaryModelRemoved": True}
        with self.assertRaisesRegex(MODULE.PowerResultError, "power-window-too-short"):
            MODULE.validate_result(value, PLAN, RUNNER)

if __name__ == "__main__":
    unittest.main()
