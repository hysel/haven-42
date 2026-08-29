#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate-alpha2-macos-model-qualification-result.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
RUNNER = MODULE.load_runner()
PLAN = RUNNER.load_json(MODULE.PLAN_PATH)


def valid_report() -> dict:
    candidates = RUNNER.validate_plan(PLAN, ROOT)
    checks = {name: {"status": "passed", "responseRetained": False, "durationSeconds": 1.0} for name in MODULE.EXPECTED_CHECKS}
    metrics = {name: {"unloadPassed": True} for name in MODULE.EXPECTED_CHECKS}
    results = []
    for model_id, candidate in candidates.items():
        results.append({"modelId": model_id, "model": candidate["model"], "manifestDigest": candidate["manifestDigest"], "status": "passed", "corePassed": True, "codingSurfaceStatus": "not-run", "codingRecommendationEligible": False, "checks": copy.deepcopy(checks), "metrics": copy.deepcopy(metrics)})
    return {"schemaVersion": 1, "kind": "haven42-apple-silicon-model-qualification-result", "release": PLAN["release"], "observedAtUtc": "2026-08-20T12:00:00Z", "status": "completed", "planCanonicalSha256": RUNNER.canonical_sha256(PLAN), "inventoryCanonicalSha256": PLAN["inventoryBinding"]["canonicalSha256"], "testContract": PLAN["testContract"], "runtime": {key: PLAN["runtime"][key] for key in ("provider", "version", "artifactSha256", "transport")}, "hardwareProfile": {"profileId": PLAN["hardwareProfile"]["id"], "platformFamily": "macos", "architecture": "arm64", "backend": "metal", "systemMemoryGiB": 16.0}, "modelsRequested": len(results), "modelsPulled": 0, "results": results, "cleanup": [], "rawPromptsOrResponsesRetained": False, "privateIdentityRetained": False, "automaticDefaultChangeAllowed": False, "automaticSelectionEvidenceAllowed": False, "automaticSupportChangeAllowed": False}


class ResultValidatorTests(unittest.TestCase):
    def test_complete_sanitized_result_passes(self) -> None:
        MODULE.validate_result(valid_report(), PLAN, RUNNER)

    def test_private_identity_and_address_fail_closed(self) -> None:
        private_path = "/" + "Us" + "ers" + "/example/result.json"
        for key, value, code in (("hostname", "private-host", "private-field-present"), ("note", "192.0.2.40", "private-address-present"), ("path", private_path, "private-path-present")):
            report = valid_report()
            report[key] = value
            with self.assertRaisesRegex(MODULE.ResultError, code):
                MODULE.validate_result(report, PLAN, RUNNER)

    def test_cleanup_and_cell_status_must_be_consistent(self) -> None:
        report = valid_report()
        report["modelsPulled"] = 1
        with self.assertRaisesRegex(MODULE.ResultError, "cleanup-count-mismatch"):
            MODULE.validate_result(report, PLAN, RUNNER)
        report = valid_report()
        report["results"][0]["checks"]["generalChat"]["status"] = "failed"
        with self.assertRaisesRegex(MODULE.ResultError, "inconsistent-candidate-status"):
            MODULE.validate_result(report, PLAN, RUNNER)

    def test_plan_and_model_binding_drift_fail_closed(self) -> None:
        report = valid_report()
        report["planCanonicalSha256"] = "0" * 64
        with self.assertRaisesRegex(MODULE.ResultError, "stale-plan-binding"):
            MODULE.validate_result(report, PLAN, RUNNER)
        report = valid_report()
        report["results"][0]["manifestDigest"] = "0" * 64
        with self.assertRaisesRegex(MODULE.ResultError, "candidate-binding-mismatch"):
            MODULE.validate_result(report, PLAN, RUNNER)

    def test_explicit_candidate_subset_passes_and_unknown_selection_fails(self) -> None:
        report = valid_report()
        selected = report["results"][0]
        report["results"] = [selected]
        report["modelsRequested"] = 1
        MODULE.validate_result(report, PLAN, RUNNER, [selected["modelId"]])

        with self.assertRaisesRegex(MODULE.ResultError, "unknown-candidate-selection"):
            MODULE.validate_result(report, PLAN, RUNNER, ["not-in-plan"])

        with self.assertRaisesRegex(MODULE.ResultError, "invalid-candidate-selection"):
            MODULE.validate_result(
                report,
                PLAN,
                RUNNER,
                [selected["modelId"], selected["modelId"]],
            )


if __name__ == "__main__":
    unittest.main()
