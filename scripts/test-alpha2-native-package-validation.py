#!/usr/bin/env python3
"""Validate sanitized Alpha 2 native package evidence and runner boundaries."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "config" / "alpha-2-native-package-validation-result.json"
LINUX_RUNNER = ROOT / "scripts" / "run-alpha2-linux-native-validation.py"
WINDOWS_RUNNER = ROOT / "scripts" / "run-windows-alpha-native-validation.ps1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def main() -> int:
    value = json.loads(RESULT.read_text(encoding="utf-8"))
    assert set(value) == {
        "schemaVersion", "kind", "release", "candidateSourceCommit",
        "validationDate", "artifacts", "primaryCells", "compatibilityCells",
        "summary", "openGates", "privacy",
    }
    assert value["schemaVersion"] == 1
    assert value["kind"] == "haven42-alpha2-native-package-validation-result"
    assert value["release"] == "0.4.0-alpha.2"
    assert re.fullmatch(r"[0-9a-f]{40}", value["candidateSourceCommit"])
    assert value["validationDate"] == "2026-08-28"

    artifacts = value["artifacts"]
    assert set(artifacts) == {"linuxArchive", "windowsArchive"}
    assert artifacts["linuxArchive"]["name"] == (
        "haven42-0.4.0-alpha.2-linux-x64-unsigned.tar.gz"
    )
    assert artifacts["windowsArchive"]["name"] == (
        "haven42-0.4.0-alpha.2-windows-x64-unsigned.zip"
    )
    assert all(
        HEX64.fullmatch(artifact["sha256"])
        and isinstance(artifact["sizeBytes"], int)
        and artifact["sizeBytes"] > 0
        for artifact in artifacts.values()
    )
    assert HEX64.fullmatch(artifacts["linuxArchive"]["packagedExecutableSha256"])

    primary = value["primaryCells"]
    compatibility = value["compatibilityCells"]
    assert [cell["id"] for cell in primary] == [
        "windows-11-x64-nvidia",
        "ubuntu-26.04-x64-nvidia",
        "bazzite-44-x64-nvidia",
    ]
    assert [cell["id"] for cell in compatibility] == [
        "ubuntu-24.04-x64", "debian-13-x64", "linux-mint-22.3-x64",
        "pop-os-24.04-x64", "fedora-44-x64", "cachyos-rolling-x64",
        "arch-rolling-x64",
    ]
    for cell in primary:
        assert cell["packageLifecycle"] == "passed"
        assert cell["noEffectReadiness"] == "passed"
        assert cell["managedSetupPlan"] == "passed"
        assert cell["backendMode"] == "cuda"
        assert cell["managedSetupExecution"] == "not-run"
        assert cell["capabilityValidation"] == "not-run"
        assert cell["unloadValidation"] == "not-run"
        assert HEX64.fullmatch(cell["sanitizedResultSha256"])
    for cell in compatibility:
        assert cell["packageLifecycle"] == "passed"
        assert cell["noEffectReadiness"] == "passed"
        assert cell["managedSetupPlan"] == "unavailable-for-profile"
        assert HEX64.fullmatch(cell["sanitizedResultSha256"])

    assert value["summary"] == {
        "nativeCellsCollected": 10,
        "packageLifecyclePassed": 10,
        "noEffectReadinessPassed": 10,
        "primaryManagedPlansPassed": 3,
        "managedSetupExecutionsPassed": 0,
        "nativeCapabilityCellsPassed": 0,
        "nativePackageValidationComplete": False,
        "readyForOwnerReview": False,
        "publicationAuthorized": False,
        "productionReady": False,
    }
    assert len(value["openGates"]) == 5
    assert value["privacy"] and not any(value["privacy"].values())

    encoded = RESULT.read_text(encoding="utf-8").lower()
    assert all(token not in encoded for token in (
        "192.168.", "@haven42", "\\users\\", "/home/", "approvaltoken",
        "sessiontoken", "prompt\"", "response\"",
    ))

    linux_source = LINUX_RUNNER.read_text(encoding="utf-8")
    ast.parse(linux_source, filename=str(LINUX_RUNNER))
    assert 'EXPECTED_VERSION = "0.4.0-alpha.2"' in linux_source
    assert 'parser.add_argument("--apply-managed-setup", action="store_true")' in linux_source
    assert 'parser.add_argument("--require-managed-setup", action="store_true")' in linux_source
    assert '"productionReady": False' in linux_source
    assert '"publicationAuthorized": False' in linux_source
    assert '"managedSetupApplied": False' in linux_source
    assert "args.apply_managed_setup" in linux_source
    assert "args.require_managed_setup" in linux_source
    assert "selectors.DefaultSelector()" in linux_source
    assert "selector.select(timeout=min(0.5, remaining))" in linux_source
    assert 'if result["managedSetupApplied"]:' in linux_source
    assert 'request_json(origin, "/api/unload"' in linux_source
    assert 'origin, "/api/shutdown", token=token' in linux_source
    assert all(token not in linux_source for token in (
        "shell=True", "sudo ", "systemctl", "firewall-cmd", "ufw ",
    ))

    windows_source = WINDOWS_RUNNER.read_text(encoding="utf-8")
    assert '[ValidateSet("0.4.0-alpha.1", "0.4.0-alpha.2")]' in windows_source
    assert '[string]$ExpectedVersion = "0.4.0-alpha.1"' in windows_source
    assert '$bootstrap.version -eq $ExpectedVersion' in windows_source
    assert '$bootstrap.version -eq "0.4.0-alpha.1"' not in windows_source
    print("Alpha 2 native package evidence passed 63 fail-closed checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
