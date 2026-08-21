#!/usr/bin/env python3
"""Unit tests for the physical macOS synthetic Keychain lifecycle runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mac_keychain_lifecycle", ROOT / "scripts/alpha2-macos-keychain-lifecycle.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeRunner:
    def __init__(self) -> None:
        self.value: bytes | None = None

    def __call__(self, command, **kwargs):
        operation = command[1]
        if operation == "find-generic-password":
            if self.value is None:
                return subprocess.CompletedProcess(command, 44, b"", b"missing")
            if "-w" in command:
                return subprocess.CompletedProcess(command, 0, self.value + b"\n", b"")
            return subprocess.CompletedProcess(command, 0, b"item", b"")
        if operation == "add-generic-password":
            self.value = command[command.index("-w") + 1].encode("utf-8")
            return subprocess.CompletedProcess(command, 0, b"", b"")
        if operation == "delete-generic-password":
            self.value = None
            return subprocess.CompletedProcess(command, 0, b"", b"")
        raise AssertionError(command)


class KeychainLifecycleTests(unittest.TestCase):
    def test_blocked_result_is_sanitized_and_non_admitting(self) -> None:
        result = MODULE.blocked_result("synthetic-item-create-denied")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["errorCode"], "synthetic-item-create-denied")
        self.assertFalse(result["secretRetained"])
        self.assertFalse(result["productionAdmissionGranted"])

    @mock.patch.object(MODULE.sys, "platform", "darwin")
    @mock.patch.object(MODULE.Path, "is_file", return_value=True)
    def test_lifecycle_passes_and_retains_no_secret(self, _is_file) -> None:
        result = MODULE.run_lifecycle(runner=FakeRunner())
        self.assertEqual(result["status"], "passed")
        self.assertTrue(all(result["checks"].values()))
        self.assertFalse(result["secretRetained"])
        self.assertFalse(result["productionAdmissionGranted"])

    @mock.patch.object(MODULE.sys, "platform", "darwin")
    @mock.patch.object(MODULE.Path, "is_file", return_value=True)
    def test_existing_synthetic_item_is_never_deleted(self, _is_file) -> None:
        fake = FakeRunner()
        fake.value = b"existing"
        with self.assertRaisesRegex(MODULE.KeychainLifecycleError, "synthetic-item-collision"):
            MODULE.run_lifecycle(runner=fake)
        self.assertEqual(fake.value, b"existing")


if __name__ == "__main__":
    unittest.main()
