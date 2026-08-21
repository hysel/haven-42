#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mac_coding_validator", ROOT / "scripts/validate-alpha2-macos-opencode-coding-result.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Runner:
    SHA256 = re.compile(r"^[0-9a-f]{64}$")

    @staticmethod
    def canonical_sha256(value):
        return value["digest"]


class MacCodingResultValidatorTests(unittest.TestCase):
    def fixture(self):
        checks = {
            "api-structured-code": ["valid-code-contract", "instruction-fidelity", "deterministic-output"],
            "repository-read-plan-review": ["repository-context-use", "exact-filename-fidelity", "implementation-plan", "defect-review"],
            "tool-contract": ["exact-tool-name", "schema-valid-arguments", "unknown-tool-refusal"],
            "scoped-edit": ["explicit-write-approval", "expected-file-only", "external-git-diff", "no-unintended-writes"],
            "reliability": ["bounded-context", "timeout-recovery", "post-failure-recovery", "model-unload"],
        }
        policy = {"digest": "e" * 64, "requiredGates": [{"id": key, "checks": value} for key, value in checks.items()]}
        plan = {"digest": "a" * 64, "release": "test", "runtime": {"provider": "ollama", "version": "1", "artifactSha256": "b" * 64, "transport": "ipv4-loopback-only"}, "hardwareProfile": {"id": "apple"}, "candidates": [{"modelId": "one", "model": "model:one", "manifestDigest": "c" * 64}]}
        qualification = {"digest": "d" * 64}
        gates = {key: {"status": "passed", "checks": {item: "passed" for item in value}} for key, value in checks.items()}
        record = {"modelId": "one", "model": "model:one", "manifestDigest": "c" * 64, "status": "passed", "gates": gates, "surfaceToolObservations": {"read-tool-observed": "passed", "write-tool-observed": "passed"}, "surfaceMetrics": {"readDurationSeconds": 1.0, "editDurationSeconds": 1.0, "readErrorCode": None, "editErrorCode": None, "readUnloadPassed": True, "editUnloadPassed": True, "rawEventsRetained": False, "forcedTimeoutDurationSeconds": 0.1, "recoveryDurationSeconds": 1.0}, "temporaryModelPulled": True, "temporaryModelRemoved": True, "responseRetained": False, "codingRecommendationEligible": True, "promotionBlock": None}
        result = {"schemaVersion": 1, "kind": "haven42-apple-silicon-coding-agent-qualification-result", "release": "test", "status": "completed", "planCanonicalSha256": "a" * 64, "qualificationCanonicalSha256": "d" * 64, "policyCanonicalSha256": "e" * 64, "runtime": plan["runtime"], "hardwareProfile": {"architecture": "arm64", "backend": "metal", "platformFamily": "macos", "profileId": "apple", "systemMemoryGiB": 16.0}, "surface": {"id": "opencode-cli", "version": "1.18.19", "binarySha256": "f" * 64, "archiveSha256": "1" * 64}, "results": [record], "observedAtUtc": "2026-01-01T00:00:00Z", "rawPromptsOrResponsesRetained": False, "privateIdentityRetained": False, "automaticDefaultChangeAllowed": False, "automaticSelectionEvidenceAllowed": False, "automaticSupportChangeAllowed": False}
        return plan, qualification, policy, result

    def test_complete_result_passes(self):
        plan, qualification, policy, result = self.fixture()
        MODULE.validate_result(result, plan, qualification, policy, Runner)

    def test_missing_gate_fails(self):
        plan, qualification, policy, result = self.fixture()
        result["results"][0]["gates"].pop("reliability")
        with self.assertRaisesRegex(MODULE.CodingResultError, "required-gates-incomplete"):
            MODULE.validate_result(result, plan, qualification, policy, Runner)

    def test_gate_summary_and_eligibility_fail_closed(self):
        plan, qualification, policy, result = self.fixture()
        result["results"][0]["gates"]["scoped-edit"]["checks"]["no-unintended-writes"] = "failed"
        with self.assertRaisesRegex(MODULE.CodingResultError, "gate-summary-inconsistent"):
            MODULE.validate_result(result, plan, qualification, policy, Runner)
        _, _, _, result = self.fixture()
        result["results"][0]["codingRecommendationEligible"] = False
        with self.assertRaisesRegex(MODULE.CodingResultError, "coding-eligibility-inconsistent"):
            MODULE.validate_result(result, plan, qualification, policy, Runner)

    def test_privacy_and_cleanup_fail_closed(self):
        plan, qualification, policy, result = self.fixture()
        result["privateIdentityRetained"] = True
        with self.assertRaisesRegex(MODULE.CodingResultError, "privacy-boundary-invalid"):
            MODULE.validate_result(result, plan, qualification, policy, Runner)
        _, _, _, result = self.fixture()
        result["results"][0]["temporaryModelRemoved"] = False
        result["results"][0]["status"] = "failed"
        result["results"][0]["codingRecommendationEligible"] = False
        with self.assertRaisesRegex(MODULE.CodingResultError, "temporary-model-cleanup-invalid"):
            MODULE.validate_result(result, plan, qualification, policy, Runner)


if __name__ == "__main__":
    unittest.main()
