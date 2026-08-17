#!/usr/bin/env python3
"""Offline unit checks for AMD GPU power-profile aggregation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/alpha2-linux-amd-power-profile.py"
SPEC = importlib.util.spec_from_file_location("alpha2_amd_power", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AmdPowerProfileTests(unittest.TestCase):
    def test_sensor_value_read_is_content_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sensor = Path(temporary) / "power1_average"
            sensor.write_text("7000000\n", encoding="ascii")
            self.assertEqual(MODULE._read_integer(sensor), 7_000_000)
            sensor.write_text("7" * 129, encoding="ascii")
            with self.assertRaisesRegex(MODULE.PowerProfileError, "unsafe-power-sensor"):
                MODULE._read_integer(sensor)

    def test_trapezoid_summary_is_bounded(self) -> None:
        result = MODULE.summarize_samples([
            (10.0, 10_000_000), (11.0, 20_000_000), (12.0, 30_000_000)
        ])
        self.assertEqual(result["samples"], 3)
        self.assertEqual(result["averageWatts"], 20.0)
        self.assertEqual(result["medianWatts"], 20.0)
        self.assertEqual(result["peakWatts"], 30.0)
        self.assertAlmostEqual(result["energyWattHours"], 40 / 3600, places=6)

    def test_invalid_sample_order_fails_closed(self) -> None:
        with self.assertRaisesRegex(MODULE.PowerProfileError, "invalid-power-sample-order"):
            MODULE.summarize_samples([(2.0, 10), (1.0, 20)])

    def test_sensor_selection_requires_exact_unique_device(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sensor = root / "card1/device/hwmon/hwmon0/power1_average"
            sensor.parent.mkdir(parents=True)
            (root / "card1/device/vendor").write_text("0x1002\n", encoding="ascii")
            (root / "card1/device/device").write_text("0x731f\n", encoding="ascii")
            sensor.write_text("8000000\n", encoding="ascii")
            self.assertEqual(MODULE.find_power_sensor(root), sensor)

    def test_duplicate_sensors_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for number in (1, 2):
                device = root / f"card{number}/device"
                sensor = device / "hwmon/hwmon0/power1_average"
                sensor.parent.mkdir(parents=True)
                (device / "vendor").write_text("0x1002\n", encoding="ascii")
                (device / "device").write_text("0x731f\n", encoding="ascii")
                sensor.write_text("8000000\n", encoding="ascii")
            with self.assertRaisesRegex(MODULE.PowerProfileError, "power-sensor-not-unique"):
                MODULE.find_power_sensor(root)


if __name__ == "__main__":
    unittest.main()
