#!/usr/bin/env python3
"""Tests for physical macOS development update lifecycle evidence validation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mac_update_validator", ROOT / "scripts/validate-alpha2-macos-development-update-lifecycle-result.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
PLAN_PATH = ROOT / "config/alpha-2-macos-development-update-lifecycle-plan.json"
PLAN_BYTES = PLAN_PATH.read_bytes()
PLAN = json.loads(PLAN_BYTES.decode("utf-8"))


def result() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-physical-macos-development-update-lifecycle-result",
        "release": PLAN["release"],
        "profileId": PLAN["profileId"],
        "observedAtUtc": "2026-08-21T00:00:00Z",
        "status": "partial-pass",
        "scope": PLAN["scope"],
        "bindings": {
            "planSha256": hashlib.sha256(PLAN_BYTES).hexdigest(),
            "baselineArchiveSha256": "a" * 64,
            "baselineSourceCommit": "b" * 40,
            "candidateArchiveSha256": "c" * 64,
            "candidateSourceCommit": "d" * 40,
        },
        "operations": {operation: True for operation in PLAN["requiredOperations"]},
        "failureInjection": {"kind": "post-selection-health-failure", "rawErrorRetained": False},
        "platformTrust": {"developerIdSigned": False, "notarized": False, "gatekeeperPublicAdmission": False},
        "privacy": {"privateIdentityRetained": False, "privatePathsRetained": False, "rawApplicationOutputRetained": False, "rawUserContentRetained": False, "rawTelemetryRetained": False},
        "authority": {"productionUpdaterAdmissionGranted": False, "automaticUpdateAdmissionGranted": False, "releasePromotionGranted": False},
    }


class MacDevelopmentUpdateLifecycleValidatorTests(unittest.TestCase):
    def test_accepts_exact_partial_pass(self) -> None:
        MODULE.validate(result(), PLAN, PLAN_BYTES)

    def test_rejects_missing_operation_and_overclaim(self) -> None:
        value = result()
        value["operations"][PLAN["requiredOperations"][0]] = False
        with self.assertRaisesRegex(MODULE.ResultError, "operation-failure-visible"):
            MODULE.validate(value, PLAN, PLAN_BYTES)
        value = result()
        value["platformTrust"]["notarized"] = True
        with self.assertRaisesRegex(MODULE.ResultError, "platform-trust-overstated"):
            MODULE.validate(value, PLAN, PLAN_BYTES)

    def test_rejects_drift_private_data_and_authority(self) -> None:
        value = result()
        value["bindings"]["planSha256"] = "e" * 64
        with self.assertRaisesRegex(MODULE.ResultError, "plan-binding-mismatch"):
            MODULE.validate(value, PLAN, PLAN_BYTES)
        value = result()
        value["observedAtUtc"] = "/" + "Users/exampleZ"
        with self.assertRaisesRegex(MODULE.ResultError, "private-data-detected"):
            MODULE.validate(value, PLAN, PLAN_BYTES)
        value = result()
        value["authority"]["releasePromotionGranted"] = True
        with self.assertRaisesRegex(MODULE.ResultError, "authority-invalid"):
            MODULE.validate(value, PLAN, PLAN_BYTES)


if __name__ == "__main__":
    unittest.main()
