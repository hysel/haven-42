#!/usr/bin/env python3
"""Tests for the attended macOS qualification result validator."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("attended_validator", ROOT / "scripts/validate-alpha2-macos-attended-qualification-result.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
PLAN_PATH = ROOT / "config/alpha-2-macos-attended-qualification-plan.json"
PLAN_BYTES = PLAN_PATH.read_bytes()
PLAN = json.loads(PLAN_BYTES.decode("utf-8"))


def result(status: str = "passed") -> dict:
    gate_status = "passed" if status == "passed" else "not-run"
    reason = "verified-as-instructed" if gate_status == "passed" else "operator-deferred"
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-physical-macos-attended-qualification-result",
        "release": PLAN["release"],
        "profileId": PLAN["profileId"],
        "observedAtUtc": "2026-08-21T00:00:00Z",
        "status": status,
        "bindings": {
            "planSha256": hashlib.sha256(PLAN_BYTES).hexdigest(),
            "artifactSha256": "a" * 64,
            "sourceCommit": "b" * 40,
        },
        "gates": {gate["id"]: {"status": gate_status, "reasonCode": reason} for gate in PLAN["gates"]},
        "privacy": {
            "freeformNotesRetained": False,
            "privateIdentityRetained": False,
            "privatePathsRetained": False,
            "rawUserContentRetained": False,
            "rawClipboardContentRetained": False,
        },
        "authority": {
            "releaseAdmissionGranted": False,
            "supportClaimGranted": False,
            "productionAdmissionGranted": False,
        },
    }


class AttendedQualificationValidatorTests(unittest.TestCase):
    def test_accepts_passed_and_incomplete(self) -> None:
        MODULE.validate(result("passed"), PLAN, PLAN_BYTES)
        MODULE.validate(result("incomplete"), PLAN, PLAN_BYTES)

    def test_rejects_implicit_pass_and_private_data(self) -> None:
        value = result("passed")
        first = next(iter(value["gates"]))
        value["gates"][first] = {"status": "not-run", "reasonCode": "operator-deferred"}
        with self.assertRaisesRegex(MODULE.ResultError, "overall-status-invalid"):
            MODULE.validate(value, PLAN, PLAN_BYTES)
        value = result("passed")
        value["observedAtUtc"] = "/" + "Users/exampleZ"
        with self.assertRaisesRegex(MODULE.ResultError, "private-data-detected"):
            MODULE.validate(value, PLAN, PLAN_BYTES)

    def test_rejects_plan_drift_and_authority(self) -> None:
        value = result("passed")
        value["bindings"]["planSha256"] = "c" * 64
        with self.assertRaisesRegex(MODULE.ResultError, "plan-binding-mismatch"):
            MODULE.validate(value, PLAN, PLAN_BYTES)
        value = result("passed")
        value["authority"]["releaseAdmissionGranted"] = True
        with self.assertRaisesRegex(MODULE.ResultError, "authority-invalid"):
            MODULE.validate(value, PLAN, PLAN_BYTES)


if __name__ == "__main__":
    unittest.main()
