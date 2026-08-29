#!/usr/bin/env python3
"""Validate the fail-closed Alpha 2 macOS expansion boundary."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "config" / "alpha-2-macos-extension-plan.json"


def main() -> int:
    value = json.loads(PLAN.read_text(encoding="utf-8"))
    assert value["schemaVersion"] == 1
    assert value["kind"] == "haven42-alpha2-macos-extension-plan"
    assert value["release"] == "0.4.0-alpha.2"
    assert value["status"] == "owner-approved-implementation-and-native-validation-required"

    target = value["target"]
    assert target == {
        "platformId": "macos-arm64",
        "operatingSystem": "macOS 26.6.2",
        "architecture": "arm64",
        "hardwareProfileId": "apple-m4-16gib-macos26-metal",
        "accelerator": "Apple M4 Metal",
        "systemMemoryGiB": 16.0,
        "plannedArchive": "haven42-0.4.0-alpha.2-macos-arm64-unsigned.zip",
    }

    evidence = value["existingExactProfileEvidence"]
    assert evidence["modelCandidatesChecked"] == 19
    assert evidence["modelCandidatesPassed"] == 10
    assert evidence["thirtyMinuteSoaksPassed"] == 10
    assert evidence["ollamaVersion"] == "0.32.15"
    assert evidence["codingCandidatesRecommended"] == 0
    assert evidence["crossSnapshotInheritanceAllowed"] is False

    gates = value["currentCandidateGates"]
    assert len(gates) == 11
    assert len({gate["id"] for gate in gates}) == len(gates)
    assert {gate["status"] for gate in gates} <= {
        "passed", "required", "attended-required",
    }
    assert sum(gate["status"] == "passed" for gate in gates) == 2
    assert any(gate["id"] == "current-source-full-suite" for gate in gates)
    assert any(gate["id"] == "source-package-parity-and-lifecycle" for gate in gates)
    assert any(gate["id"] == "manual-keyboard-voiceover-zoom-and-reduced-motion" for gate in gates)

    behavior = value["platformBehavior"]
    assert behavior == {
        "managedInitialOllamaInstallation": False,
        "userInstallsOllamaBeforeConnecting": True,
        "guidedModelDownloadsAfterConnection": True,
        "terminalRequiredForOrdinaryModelDownload": False,
    }
    assert value["authority"] == {
        "changesAutomaticModelDefaults": False,
        "changesSupportLabels": False,
        "changesManagedRuntimeAdmission": False,
        "publicationAuthorized": False,
        "productionReady": False,
        "signedOrNotarized": False,
    }
    print("Alpha 2 macOS extension plan passed 28 fail-closed checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
