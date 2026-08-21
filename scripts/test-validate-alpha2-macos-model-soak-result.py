#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mac_soak_validator", ROOT / "scripts/validate-alpha2-macos-model-soak-result.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Runner:
    @staticmethod
    def canonical_sha256(value):
        return value["digest"]


class MacSoakResultValidatorTests(unittest.TestCase):
    def fixture(self):
        plan = {
            "digest": "a" * 64,
            "release": "test",
            "runtime": {"provider": "ollama", "version": "1", "artifactSha256": "b" * 64, "transport": "ipv4-loopback-only"},
            "hardwareProfile": {"id": "apple", "minimumSystemMemoryGiB": 15},
            "candidates": [{"modelId": "one", "model": "model:one", "manifestDigest": "c" * 64}],
        }
        qualification = {"digest": "d" * 64, "results": [{"modelId": "one", "status": "passed"}]}
        result = {
            "schemaVersion": 1, "kind": "haven42-apple-silicon-model-soak-result", "release": "test", "status": "completed",
            "planCanonicalSha256": "a" * 64, "qualificationCanonicalSha256": "d" * 64,
            "runtime": {"provider": "ollama", "version": "1", "artifactSha256": "b" * 64, "transport": "ipv4-loopback-only"},
            "hardwareProfile": {"architecture": "arm64", "backend": "metal", "platformFamily": "macos", "profileId": "apple", "systemMemoryGiB": 16.0},
            "requestedMinutesPerModel": 30, "intervalSeconds": 30, "modelIdsExpected": ["one"],
            "results": [{"modelId": "one", "model": "model:one", "manifestDigest": "c" * 64, "status": "passed", "durationSeconds": 1800.0, "cycles": 10, "samples": 50, "outputTokens": 100, "averageTokensPerSecond": 10.0, "unloadProofs": 50, "temporaryModelPulled": True, "temporaryModelRemoved": True, "responseRetained": False}],
            "observedAtUtc": "2026-01-01T00:00:00Z", "rawPromptsOrResponsesRetained": False, "privateIdentityRetained": False,
            "automaticDefaultChangeAllowed": False, "automaticSelectionEvidenceAllowed": False, "automaticSupportChangeAllowed": False,
        }
        return plan, qualification, result

    def test_complete_result_passes(self):
        plan, qualification, result = self.fixture()
        MODULE.validate_result(result, plan, qualification, Runner)

    def test_short_pass_is_rejected(self):
        plan, qualification, result = self.fixture()
        result["results"][0]["durationSeconds"] = 1799.9
        with self.assertRaisesRegex(MODULE.SoakResultError, "passed-duration-invalid"):
            MODULE.validate_result(result, plan, qualification, Runner)

    def test_missing_candidate_is_rejected(self):
        plan, qualification, result = self.fixture()
        result["results"] = []
        with self.assertRaisesRegex(MODULE.SoakResultError, "result-coverage-invalid"):
            MODULE.validate_result(result, plan, qualification, Runner)

    def test_privacy_and_cleanup_fail_closed(self):
        plan, qualification, result = self.fixture()
        result["privateIdentityRetained"] = True
        with self.assertRaisesRegex(MODULE.SoakResultError, "privacy-boundary-invalid"):
            MODULE.validate_result(result, plan, qualification, Runner)
        _, _, result = self.fixture()
        result["results"][0]["temporaryModelRemoved"] = False
        with self.assertRaisesRegex(MODULE.SoakResultError, "temporary-model-cleanup-invalid"):
            MODULE.validate_result(result, plan, qualification, Runner)


if __name__ == "__main__":
    unittest.main()
