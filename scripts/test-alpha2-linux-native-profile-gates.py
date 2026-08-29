#!/usr/bin/env python3
"""Offline hostile checks for the exact Linux native-profile gate matrix."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "scripts/alpha2-linux-native-profile-gates.py"
SPEC = importlib.util.spec_from_file_location("alpha2_native_profile_gates", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def main() -> int:
    report = MODULE.build_report()
    assert report["targetCount"] == 9
    assert report["readyCount"] + report["qualificationRequiredCount"] == 9
    assert {item["operatingSystemId"] for item in report["profiles"]} == {
        "ubuntu-26.04", "ubuntu-24.04", "debian-13", "linux-mint-22.3",
        "pop-os-24.04", "fedora-44", "bazzite-44", "cachyos-rolling",
        "arch-rolling",
    }
    assert all(item["caTrustPathAllowlisted"] for item in report["profiles"])
    assert all(item["backendMode"] == "cuda" for item in report["profiles"])
    assert all(item["glibcMinimum"] == "2.39" for item in report["profiles"])
    assert all(
        item["nativeManagedSetupReady"]
        == (item["modelEvidenceGate"] == "ready" and item["selectedModelId"] is not None)
        for item in report["profiles"]
    )
    assert report["effects"] == {
        "networkContacted": False,
        "processStarted": False,
        "fileWritten": False,
        "selectionPolicyChanged": False,
    }

    missing_ca = set(MODULE.SETUP.SYSTEM_CA_BUNDLE_CANDIDATES) - {
        MODULE.CA_PATH_BY_FAMILY["fedora"]
    }
    with mock.patch.object(
        MODULE.SETUP, "SYSTEM_CA_BUNDLE_CANDIDATES", tuple(missing_ca),
    ):
        try:
            MODULE.build_report()
        except MODULE.GateError as error:
            assert str(error) == "missing-ca-path-for-fedora-44-gnome"
        else:
            raise AssertionError("Missing Fedora-family CA path was admitted.")

    original = MODULE.LINUX.evaluate_hardware
    with mock.patch.object(
        MODULE.LINUX, "evaluate_hardware",
        side_effect=lambda snapshot: {
            **original(snapshot), "operatingSystemId": "wrong-os",
        },
    ):
        try:
            MODULE.build_report()
        except MODULE.GateError as error:
            assert str(error).startswith("os-identity-drift-for-")
        else:
            raise AssertionError("OS identity drift was admitted.")

    print("Alpha 2 Linux native profile matrix passed 18 fail-closed checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
