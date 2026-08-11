#!/usr/bin/env python3
"""Test the Alpha 2 driver compatibility catalog and advisory evaluator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "config" / "alpha-2-driver-compatibility-catalog.json"
FIXTURE_PATH = ROOT / "examples" / "fixtures" / "alpha-2-driver-compatibility-cases.json"
MODULE_PATH = ROOT / "scripts" / "driver_compatibility.py"

spec = importlib.util.spec_from_file_location("driver_compatibility", MODULE_PATH)
assert spec and spec.loader
driver_compatibility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver_compatibility)


class DriverCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_catalog_has_no_install_or_product_policy_authority(self) -> None:
        authority = self.catalog["authority"]
        self.assertFalse(authority["changesAutomaticModelSelection"])
        self.assertFalse(authority["installsOrUpdatesDrivers"])
        self.assertFalse(authority["authorizesAutomaticDriverInstallation"])
        self.assertTrue(authority["unknownHardwareFallsBackToCpu"])
        self.assertTrue(authority["olderSupportedRequiresRiskAcknowledgement"])
        self.assertTrue(authority["knownIncompatibleBlocksAutomaticGpuUse"])

    def test_sources_are_reviewed_https_primary_sources(self) -> None:
        allowed_hosts = {
            "download.nvidia.com",
            "www.nvidia.com",
            "documentation.ubuntu.com",
            "wiki.debian.org",
        }
        source_ids = set()
        for source in self.catalog["sources"]:
            parsed = urlparse(source["url"])
            self.assertEqual(parsed.scheme, "https")
            self.assertIn(parsed.hostname, allowed_hosts)
            self.assertNotIn(source["id"], source_ids)
            source_ids.add(source["id"])
        for device in self.catalog["devices"]:
            self.assertTrue(set(device["supportEvidence"]).issubset(source_ids))

    def test_exact_rtx_and_non_rtx_quadro_are_not_conflated(self) -> None:
        devices = {item["deviceId"]: item for item in self.catalog["devices"]}
        self.assertEqual(devices["1eb0"]["name"], "NVIDIA Quadro RTX 5000")
        self.assertEqual(devices["1eb0"]["supportClass"], "current-unified")
        self.assertEqual(devices["06d9"]["name"], "NVIDIA Quadro 5000")
        self.assertEqual(devices["06d9"]["supportClass"], "legacy-390")

    def test_all_advisory_cases(self) -> None:
        for case in self.fixtures["cases"]:
            with self.subTest(case=case["id"]):
                values = case["input"]
                result = driver_compatibility.evaluate(
                    platform=values[0],
                    distribution=values[1],
                    os_version=values[2],
                    vendor_id=values[3],
                    device_id=values[4],
                    driver_version=values[5],
                )
                self.assertEqual(result["status"], case["expected"])
                self.assertTrue(result["advisoryOnly"])
                self.assertFalse(result["driverMutationAllowed"])
                self.assertFalse(result["modelDefaultChangeAllowed"])

    def test_older_supported_version_requires_explicit_acknowledgement(self) -> None:
        result = driver_compatibility.evaluate(
            platform="linux",
            distribution="ubuntu",
            os_version="24.04",
            vendor_id="10de",
            device_id="1eb0",
            driver_version="550.163.01",
        )
        self.assertEqual(result["status"], "supported-update-available")
        self.assertTrue(result["continueAllowed"])
        self.assertTrue(result["acknowledgementRequired"])
        self.assertIn("at your own risk", result["warning"])
        self.assertFalse(result["automaticGpuUseAllowed"])

    def test_malformed_inputs_are_rejected(self) -> None:
        invalid = ["latest", "595.x", "595.84; reboot", "9" * 100]
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(driver_compatibility.DriverAdvisoryError):
                    driver_compatibility.evaluate(
                        platform="linux",
                        distribution="ubuntu",
                        os_version="24.04",
                        vendor_id="10de",
                        device_id="1eb0",
                        driver_version=value,
                    )


if __name__ == "__main__":
    unittest.main()
