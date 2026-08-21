#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mac_soak", ROOT / "scripts/alpha2-macos-model-soak.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MacModelSoakTests(unittest.TestCase):
    def test_cycle_requires_every_pass_residency_and_unload(self) -> None:
        checks = {"a": {"status": "passed", "responseRetained": False}, "b": {"status": "passed", "responseRetained": False}}
        metrics = {"a": {"outputTokens": 10, "tokensPerSecond": 20.0, "fullMetalResidency": True, "unloadPassed": True}, "b": {"outputTokens": 20, "tokensPerSecond": 40.0, "fullMetalResidency": True, "unloadPassed": True}}
        self.assertEqual(MODULE.aggregate_cycle({"corePassed": True, "checks": checks, "metrics": metrics}), (2, 30, 30.0, True))
        metrics["b"]["fullMetalResidency"] = False
        self.assertFalse(MODULE.aggregate_cycle({"corePassed": True, "checks": checks, "metrics": metrics})[3])

    def test_resume_binding_and_records_fail_closed(self) -> None:
        expected = {"schemaVersion": 1, "kind": "kind", "release": "release", "planCanonicalSha256": "a", "qualificationCanonicalSha256": "b", "runtime": {}, "hardwareProfile": {}, "requestedMinutesPerModel": 30, "intervalSeconds": 30, "modelIdsExpected": ["one", "two"]}
        value = expected | {"status": "running", "results": [{"modelId": "one", "status": "passed"}]}
        self.assertEqual(len(MODULE.validate_resume(value, expected)), 1)
        value["planCanonicalSha256"] = "changed"
        with self.assertRaisesRegex(MODULE.SoakError, "stale-or-invalid"):
            MODULE.validate_resume(value, expected)

    def test_checkpoint_has_no_promotion_authority(self) -> None:
        class Runner:
            @staticmethod
            def canonical_sha256(value): return "a" * 64
        plan = {"release": "test", "runtime": {"provider": "ollama", "version": "1", "artifactSha256": "b" * 64, "transport": "ipv4-loopback-only"}, "hardwareProfile": {"id": "apple"}}
        report = MODULE.checkpoint_base(plan, {}, Runner, {"platformFamily": "macos"}, ["one"])
        self.assertFalse(report["automaticDefaultChangeAllowed"])
        self.assertFalse(report["automaticSupportChangeAllowed"])
        self.assertFalse(report["rawPromptsOrResponsesRetained"])


if __name__ == "__main__":
    unittest.main()
