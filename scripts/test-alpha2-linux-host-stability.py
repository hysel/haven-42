#!/usr/bin/env python3
"""Offline checks for the bounded Linux host-stability attestor."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/alpha2-linux-host-stability.py"
SPEC = importlib.util.spec_from_file_location("alpha2_linux_host_stability", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HostStabilityTests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[Path, Path, Path]:
        boot = root / "boot-id"
        boot.write_text("12345678-1234-1234-1234-123456789abc\n", encoding="ascii")
        uptime = root / "uptime"
        uptime.write_text("7200.0 10.0\n", encoding="ascii")
        os_release = root / "os-release"
        os_release.write_text('ID=ubuntu\nVERSION_ID="26.04"\n', encoding="ascii")
        return boot, uptime, os_release

    def test_pass_is_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            boot, uptime, os_release = self.fixture(root)
            journalctl = root / "journalctl"
            journalctl.write_text("fixture", encoding="ascii")
            completed = MODULE.subprocess.CompletedProcess(
                [str(journalctl)], 0, "Linux version fixture\namdgpu initialized\n", ""
            )
            with patch.object(MODULE.subprocess, "run", return_value=completed), patch.object(
                MODULE, "_run_cpu_smoke", return_value=1234
            ), patch.object(MODULE.platform, "release", return_value="7.0.0-test"):
                result = MODULE.build_evidence(
                    30, 2, journalctl=str(journalctl.resolve()),
                    boot_id_path=boot, uptime_path=uptime, os_release_path=os_release,
                )
            self.assertEqual(result["outcome"], "passed")
            rendered = json.dumps(result).lower()
            for forbidden in ("hostname", "ipaddress", "12345678-1234"):
                self.assertNotIn(forbidden, rendered)

    def test_new_gpu_reset_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            boot, uptime, os_release = self.fixture(root)
            journalctl = root / "journalctl"
            journalctl.write_text("fixture", encoding="ascii")
            before = MODULE.subprocess.CompletedProcess([str(journalctl)], 0, "Linux boot\n", "")
            after = MODULE.subprocess.CompletedProcess(
                [str(journalctl)], 0, "Linux boot\namdgpu GPU reset begin\n", ""
            )
            with patch.object(MODULE.subprocess, "run", side_effect=[before, after]), patch.object(
                MODULE, "_run_cpu_smoke", return_value=10
            ), patch.object(MODULE.platform, "release", return_value="7.0.0-test"):
                result = MODULE.build_evidence(
                    30, 1, journalctl=str(journalctl.resolve()),
                    boot_id_path=boot, uptime_path=uptime, os_release_path=os_release,
                )
            self.assertEqual(result["outcome"], "failed")
            self.assertEqual(result["newKernelIncidentCounts"]["gpuReset"], 1)

    def test_rejects_unsafe_envelope(self) -> None:
        with self.assertRaisesRegex(MODULE.StabilityError, "unsafe-smoke-envelope"):
            MODULE.build_evidence(1, 128, journalctl="/usr/bin/journalctl")

    def test_mce_decoder_initialization_is_not_an_incident(self) -> None:
        counts = MODULE._incident_counts("MCE: In-kernel MCE decoding enabled.\n")
        self.assertEqual(counts["machineCheck"], 0)

    def test_preexisting_current_boot_fatal_event_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            boot, uptime, os_release = self.fixture(root)
            journalctl = root / "journalctl"
            journalctl.write_text("fixture", encoding="ascii")
            log = "Linux boot\nAER: Uncorrected (Fatal) error received\n"
            completed = MODULE.subprocess.CompletedProcess([str(journalctl)], 0, log, "")
            with patch.object(MODULE.subprocess, "run", return_value=completed), patch.object(
                MODULE, "_run_cpu_smoke", return_value=10
            ), patch.object(MODULE.platform, "release", return_value="7.0.0-test"):
                result = MODULE.build_evidence(
                    30, 1, journalctl=str(journalctl.resolve()),
                    boot_id_path=boot, uptime_path=uptime, os_release_path=os_release,
                )
            self.assertEqual(result["outcome"], "failed")
            self.assertEqual(result["currentBootKernelIncidentCounts"]["fatalPcie"], 1)


if __name__ == "__main__":
    unittest.main()
