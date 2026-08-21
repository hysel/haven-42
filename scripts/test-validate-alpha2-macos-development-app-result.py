#!/usr/bin/env python3
"""Tests for fail-closed physical-Mac development-app result validation."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "validate-alpha2-macos-development-app-result.py"
SPEC = importlib.util.spec_from_file_location("development_app_result", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-physical-macos-development-app-result",
        "release": "0.4.0-alpha.2",
        "observedAtUtc": "2026-08-21T00:00:00Z",
        "status": "partial-pass",
        "hardwareProfile": {
            "profileId": "apple-m4-16gib-macos26-metal",
            "platformFamily": "macos", "architecture": "arm64",
            "backend": "metal", "systemMemoryGiB": 16,
        },
        "source": {"repository": "https://github.com/hysel/haven-42", "commit": "a" * 40, "treeState": "modified-uncommitted", "commitIsExactSource": False, "snapshotSha256": "1" * 64},
        "app": {
            "bundleIdentifier": "org.haven42.desktop", "bundleShortVersion": "0.4.0",
            "bundleVersion": "0.4.2", "minimumSystemVersion": "13.0",
            "archiveSha256": "2" * 64, "portablePackageArchiveSha256": "3" * 64,
            "portableBuildProvenanceSha256": "4" * 64, "inventoryCanonicalSha256": "5" * 64,
            "fileCount": 42, "nativeArchitecture": "arm64", "globalPythonRequired": False,
        },
        "tests": {key: True for key in MODULE.REQUIRED_TESTS - {"packagedBrowserChecks"}} | {"packagedBrowserChecks": 61},
        "platformTrust": {"codeSignatureStructureValid": True, "developerIdSigned": False, "notarized": False, "gatekeeperAdmittedOnTestHost": False, "publicDistributionAllowed": False},
        "open": sorted(MODULE.REQUIRED_OPEN),
        "authority": {"releasePublicationAllowed": False, "automaticUpdateAllowed": False, "productionAdmissionGranted": False},
        "privacy": {"privateIdentityRetained": False, "privatePathsRetained": False, "rawUserContentRetained": False, "rawToolOutputRetained": False},
    }


def main() -> int:
    checks = 0
    assert MODULE.validate(fixture())["status"] == "partial-pass"
    checks += 1
    exact = fixture()
    exact["source"].update({
        "treeState": "exact-commit",
        "commitIsExactSource": True,
        "snapshotSha256": "",
    })
    assert MODULE.validate(exact)["status"] == "partial-pass"
    checks += 1
    for change in (
        lambda value: value["tests"].__setitem__("packagedBrowserFlow", False),
        lambda value: value["app"].__setitem__("globalPythonRequired", True),
        lambda value: value["source"].update(
            {"treeState": "exact-commit", "commitIsExactSource": False}
        ),
        lambda value: value["platformTrust"].__setitem__("developerIdSigned", True),
        lambda value: value["authority"].__setitem__("productionAdmissionGranted", True),
        lambda value: value["open"].remove("manual-keyboard"),
    ):
        candidate = fixture()
        change(candidate)
        try:
            MODULE.validate(candidate)
        except MODULE.ResultError:
            checks += 1
        else:
            raise AssertionError("Invalid development-app evidence was accepted.")
    print(f"Apple M4 development-app result validator tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
