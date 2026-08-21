#!/usr/bin/env python3
"""Tests for the macOS Keychain lifecycle evidence validator."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("keychain_result", ROOT / "scripts/validate-alpha2-macos-keychain-lifecycle-result.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def common(status: str) -> dict:
    return {"schemaVersion": 1, "kind": "haven42-sanitized-physical-macos-keychain-lifecycle-result", "release": "0.4.0-alpha.2", "status": status, "platform": "macos", "scope": "current-user-synthetic-item-only", "secretRetained": False, "rawOutputRetained": False, "keychainNameOrPathRetained": False, "privateIdentityRetained": False, "encryptedHistoryAdmissionGranted": False, "packageAdmissionGranted": False, "productionAdmissionGranted": False}


class KeychainResultTests(unittest.TestCase):
    def test_accepts_blocked_denial(self) -> None:
        value = common("blocked")
        value["errorCode"] = "synthetic-item-create-denied"
        MODULE.validate_result(value)

    def test_accepts_complete_pass(self) -> None:
        value = common("passed")
        value["checks"] = {key: True for key in ("collisionRefused", "created", "readBackMatched", "updated", "updatedReadBackMatched", "deleted", "absenceConfirmed")}
        MODULE.validate_result(value)

    def test_rejects_admission_claim(self) -> None:
        value = common("blocked")
        value["errorCode"] = "synthetic-item-create-denied"
        value["productionAdmissionGranted"] = True
        with self.assertRaisesRegex(MODULE.KeychainResultError, "unsafe-retention-or-admission"):
            MODULE.validate_result(value)


if __name__ == "__main__":
    unittest.main()
