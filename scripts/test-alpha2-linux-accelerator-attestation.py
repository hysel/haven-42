#!/usr/bin/env python3
"""Offline checks for the sanitized Linux accelerator attestor."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/alpha2-linux-accelerator-attestation.py"
SPEC = importlib.util.spec_from_file_location("alpha2_accelerator_attestation", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AcceleratorAttestationTests(unittest.TestCase):
    def fixture(self, root: Path, *, driver: str = "amdgpu") -> tuple[Path, Path, Path, Path]:
        plan = root / "plan.json"
        plan.write_text(json.dumps({
            "planId": "fixture-plan",
            "hardwareClass": {
                "vendor": "AMD", "model": "Radeon RX 5700 XT",
                "architecture": "RDNA 1", "gfxTarget": "gfx1010",
                "pciVendorId": "0x1002", "pciDeviceId": "0x731f",
                "kernelDriver": "amdgpu", "vulkanDriver": "radv", "memoryGiB": 8,
            },
        }), encoding="utf-8")
        drm = root / "drm"
        device = drm / "card1" / "device"
        device.mkdir(parents=True)
        (device / "vendor").write_text("0x1002\n", encoding="ascii")
        (device / "device").write_text("0x731f\n", encoding="ascii")
        (device / "mem_info_vram_total").write_text("8573157376\n", encoding="ascii")
        (device / "driver").write_text(driver, encoding="ascii")
        os_release = root / "os-release"
        os_release.write_text('ID=ubuntu\nVERSION_ID="26.04"\n', encoding="ascii")
        uptime = root / "uptime"
        uptime.write_text("5400.25 100.0\n", encoding="ascii")
        return plan, drm, os_release, uptime

    def test_passes_without_retaining_private_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, drm, os_release, uptime = self.fixture(root)
            completed = MODULE.subprocess.CompletedProcess(
                ["vulkaninfo", "--summary"], 0,
                "GPU0:\n vendorID = 0x1002\n deviceID = 0x731f\n"
                " deviceName = AMD Radeon RX 5700 XT (RADV NAVI10)\n"
                " driverName = radv\n driverInfo = Mesa 26.0.3\n",
                "warning ignored",
            )
            vulkaninfo = root / "vulkaninfo"
            vulkaninfo.write_text("fixture", encoding="ascii")
            with patch.object(MODULE.subprocess, "run", return_value=completed), patch.object(
                MODULE.platform, "release", return_value="7.0.0-29-generic"
            ), patch.object(MODULE, "_driver_name", return_value="amdgpu"):
                result = MODULE.build_attestation(
                    plan, drm, os_release, uptime, str(vulkaninfo.resolve())
                )
            self.assertEqual(result["outcome"], "passed")
            self.assertEqual(result["device"]["kernelDriver"], "amdgpu")
            self.assertEqual(result["vulkan"]["driverName"], "radv")
            self.assertEqual(result["uptimeSeconds"], 5400)
            rendered = json.dumps(result)
            for forbidden in ("hostname", "ipaddress", "hardwareuuid", "card1"):
                self.assertNotIn(forbidden, rendered.lower())

    def test_driver_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, drm, _, _ = self.fixture(root, driver="vfio-pci")
            with patch.object(MODULE, "_driver_name", return_value="vfio-pci"):
                with self.assertRaisesRegex(MODULE.AttestationError, "kernel-driver-mismatch"):
                    MODULE._devices(drm, MODULE._expected(MODULE._load_json(plan)))

    def test_multiple_matching_devices_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, drm, _, _ = self.fixture(root)
            source = drm / "card1" / "device"
            duplicate = drm / "card2" / "device"
            duplicate.mkdir(parents=True)
            for name in ("vendor", "device", "mem_info_vram_total"):
                (duplicate / name).write_text((source / name).read_text(encoding="ascii"), encoding="ascii")
            (duplicate / "driver").write_text("amdgpu", encoding="ascii")
            with patch.object(MODULE, "_driver_name", return_value="amdgpu"):
                with self.assertRaisesRegex(MODULE.AttestationError, "expected-accelerator-not-unique"):
                    MODULE._devices(drm, MODULE._expected(MODULE._load_json(plan)))


if __name__ == "__main__":
    unittest.main()
