#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("power_cell", ROOT / "scripts/alpha2-macos-model-power-cell.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MacModelPowerCellTests(unittest.TestCase):
    def test_warmup_accepts_completed_nonempty_generation_on_metal(self) -> None:
        MODULE.validate_warmup(
            {"done": True},
            "READY.",
            {"fullMetalResidency": True},
        )

    def test_warmup_rejects_empty_incomplete_or_non_metal_generation(self) -> None:
        cases = (
            ({"done": False}, "READY", {"fullMetalResidency": True}, "warmup-generation-failed"),
            ({"done": True}, "  ", {"fullMetalResidency": True}, "warmup-generation-failed"),
            ({"done": True}, "READY", {"fullMetalResidency": False}, "warmup-metal-residency-failed"),
        )
        for response, text, residency, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(MODULE.PowerCellError, message):
                MODULE.validate_warmup(response, text, residency)

    def test_non_root_or_writable_helper_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            helper = Path(directory) / "helper"
            helper.write_text("#!/bin/sh\n", encoding="utf-8")
            helper.chmod(0o777)
            with self.assertRaisesRegex(MODULE.PowerCellError, "unsafe-power-helper"):
                MODULE.validate_helper(helper)

    def test_report_is_explicit_about_power_boundary_and_authority(self) -> None:
        plan = {"release": "test", "runtime": {"provider": "ollama", "version": "1", "artifactSha256": "a" * 64, "transport": "ipv4-loopback-only"}, "hardwareProfile": {"id": "apple-test"}}
        candidate = {"modelId": "model-test", "model": "model:test", "manifestDigest": "b" * 64, "modelBytes": 1}
        summary = {"kind": "haven42-sanitized-macos-power-summary", "rawTelemetryRetained": False, "privateIdentityRetained": False}
        report = MODULE.build_report(plan, candidate, {"planCanonicalSha256": "c" * 64}, {"platformFamily": "macos"}, summary, {"responseRetained": False}, {"unloadPassed": True, "temporaryModelRemoved": True})
        self.assertEqual(report["status"], "passed")
        self.assertIn("not wall-outlet", report["measurementBoundary"])
        self.assertFalse(report["automaticSupportChangeAllowed"])
        self.assertFalse(report["rawPromptsOrResponsesRetained"])


if __name__ == "__main__":
    unittest.main()
