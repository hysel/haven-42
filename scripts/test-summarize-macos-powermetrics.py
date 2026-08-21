#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mac_power", ROOT / "scripts/summarize-macos-powermetrics.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


SAMPLE = """
*** Sampled system activity (fixture) ***
CPU Power: 1000 mW
GPU Power: 2000 mW
ANE Power: 0 mW
Combined Power (CPU + GPU + ANE): 3000 mW
Current pressure level: Nominal
GPU HW active residency:  50.00% (338 MHz: 50%)
GPU Power: 2000 mW
*** Sampled system activity (fixture) ***
CPU Power: 2000 mW
GPU Power: 4000 mW
ANE Power: 0 mW
Combined Power (CPU + GPU + ANE): 6000 mW
Current pressure level: Nominal
GPU HW active residency:  75.00% (338 MHz: 75%)
GPU Power: 4000 mW
"""


class MacPowerSummaryTests(unittest.TestCase):
    def test_summary_is_compact_and_sanitized(self) -> None:
        result = MODULE.summarize(SAMPLE)
        self.assertEqual(result["powerMilliwatts"]["combined"]["average"], 4500.0)
        self.assertEqual(result["gpuActiveResidencyPercent"]["maximum"], 75.0)
        self.assertEqual(result["thermalPressureLevels"], ["nominal"])
        self.assertFalse(result["rawTelemetryRetained"])

    def test_incomplete_samples_fail_closed(self) -> None:
        with self.assertRaisesRegex(MODULE.PowerSummaryError, "incomplete-power-samples"):
            MODULE.summarize("")
        with self.assertRaisesRegex(MODULE.PowerSummaryError, "incomplete-sample-block"):
            MODULE.summarize(SAMPLE.replace("Current pressure level: Nominal\n", "", 1))


if __name__ == "__main__":
    unittest.main()
