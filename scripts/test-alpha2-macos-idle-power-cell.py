#!/usr/bin/env python3
"""Unit tests for the sanitized macOS idle-power baseline runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mac_idle_power", ROOT / "scripts/alpha2-macos-idle-power-cell.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IdlePowerTests(unittest.TestCase):
    def test_build_report_omits_identity_and_raw_telemetry(self) -> None:
        plan = {
            "release": "0.4.0-alpha.2",
            "runtime": {
                "provider": "ollama",
                "version": "0.32.15",
                "artifactSha256": "a" * 64,
                "transport": "ipv4-loopback-only",
            },
            "hardwareProfile": {"id": "apple-m4-16gib-macos26-metal"},
        }
        report = MODULE.build_report(
            plan,
            "b" * 64,
            {"platformFamily": "macos", "architecture": "arm64", "backend": "metal", "systemMemoryGiB": 16.0},
            {"kind": "haven42-sanitized-macos-power-summary"},
        )
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["precondition"]["loadedModels"], 0)
        self.assertFalse(report["rawTelemetryRetained"])
        self.assertFalse(report["privateIdentityRetained"])
        self.assertFalse(report["automaticDefaultChangeAllowed"])


if __name__ == "__main__":
    unittest.main()
