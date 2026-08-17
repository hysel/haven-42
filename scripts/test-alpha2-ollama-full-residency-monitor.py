#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("alpha2-ollama-full-residency-monitor.py")
SPEC = importlib.util.spec_from_file_location("residency_monitor", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ResidencyMonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = {
            "qualificationProvider": {"exactVersion": "0.32.13"},
            "families": [{"versions": [{"candidates": [{
                "id": "model-one", "model": "publisher:model", "manifestDigest": "a" * 64,
            }]}]}],
        }

    def test_full_residency_passes_without_private_content(self) -> None:
        candidates = MODULE._inventory_candidates(self.inventory)
        record = MODULE._record(
            "model-one", candidates["model-one"], {"size": 100, "size_vram": 100}, "b" * 64,
            operating_system_id="ubuntu-test", backend="vulkan", hardware_profile_id="amd-test",
        )
        self.assertEqual(record["outcome"], "passed")
        self.assertTrue(record["evidence"]["fullGpuResidencyObserved"])
        self.assertFalse(record["containsPrivateMachineIdentity"])
        self.assertEqual(record["evidence"]["backendMode"], "vulkan")
        self.assertNotIn("name", json.dumps(record))

    def test_partial_residency_fails_closed(self) -> None:
        candidates = MODULE._inventory_candidates(self.inventory)
        record = MODULE._record(
            "model-one", candidates["model-one"], {"size": 100, "size_vram": 99}, "b" * 64,
            operating_system_id="ubuntu-test", backend="vulkan", hardware_profile_id="amd-test",
        )
        self.assertEqual(record["outcome"], "failed")
        self.assertEqual(record["errorCode"], "partial-gpu-residency")

    def test_invalid_counters_are_refused(self) -> None:
        candidates = MODULE._inventory_candidates(self.inventory)
        with self.assertRaises(MODULE.ResidencyError):
            MODULE._record(
                "model-one", candidates["model-one"], {"size": 100, "size_vram": 101}, "b" * 64,
                operating_system_id="ubuntu-test", backend="vulkan", hardware_profile_id="amd-test",
            )

    def test_origin_is_loopback_only_and_canonical(self) -> None:
        self.assertEqual(
            MODULE._validate_origin("http://127.0.0.1:11434/"),
            "http://127.0.0.1:11434",
        )
        for origin in (
            "https://127.0.0.1:11434",
            "http://localhost:11434",
            "http://192.0.2.1:11434",
            "http://127.0.0.1:11434/api/ps",
            "http://user@127.0.0.1:11434",
            "http://127.0.0.1",
        ):
            with self.subTest(origin=origin), self.assertRaises(MODULE.ResidencyError):
                MODULE._validate_origin(origin)

    def test_output_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "record.json"
            MODULE._write_once(output, {"outcome": "passed"})
            with self.assertRaises(MODULE.ResidencyError):
                MODULE._write_once(output, {"outcome": "failed"})


if __name__ == "__main__":
    unittest.main()
