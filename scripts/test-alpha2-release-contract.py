#!/usr/bin/env python3
"""Validate the fail-closed Alpha 2 release and Alpha 1 isolation contract."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "alpha-2-release-contract.json"


def main() -> int:
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert set(value) == {
        "schemaVersion", "contractId", "version", "status", "audience",
        "capabilities", "platforms", "alpha1", "releaseControls",
        "requiredPerArchiveEvidence", "stopConditions",
    }
    assert value["schemaVersion"] == 1
    assert value["contractId"] == "haven42.alpha2.release"
    assert value["version"] == "0.4.0-alpha.2"
    assert value["status"] == "candidate-preparation-native-validation-required"
    assert value["capabilities"] == [
        "general.chat", "content.write", "content.summarize",
    ]
    assert value["platforms"] == [
        {
            "id": "windows-x64",
            "archive": "haven42-0.4.0-alpha.2-windows-x64-unsigned.zip",
            "nativeValidationRequired": True,
        },
        {
            "id": "linux-x64",
            "archive": "haven42-0.4.0-alpha.2-linux-x64-unsigned.tar.gz",
            "nativeValidationRequired": True,
        },
    ]
    assert value["alpha1"] == {
        "version": "0.4.0-alpha.1",
        "tag": "v0.4.0-alpha.1",
        "asset": "haven42-0.4.0-alpha.1-windows-x64-unsigned.zip",
        "immutable": True,
        "replacementAllowed": False,
        "republicationAllowed": False,
    }
    controls = value["releaseControls"]
    assert controls == {
        "unsigned": True,
        "prereleaseRequired": True,
        "automaticPublicationAllowed": False,
        "ownerApprovalRequiredForPublication": True,
        "ownerApprovalRequiredForDefaultModelChange": True,
        "onePlatformMayInheritAnotherPlatformResult": False,
        "productionReady": False,
    }
    assert set(value["requiredPerArchiveEvidence"]) == {
        "sha256", "package-file-inventory", "runtime-component-inventory",
        "dependency-inventory", "third-party-notices", "cyclonedx-sbom",
        "build-provenance", "known-limitations",
    }
    assert "alpha1-asset-mutation" in value["stopConditions"]
    builder = (ROOT / "scripts/build-windows-alpha-candidate.py").read_text(
        encoding="utf-8"
    )
    alpha2_builder = (
        ROOT / "scripts/build-windows-alpha2-candidate.py"
    ).read_text(encoding="utf-8")
    assert 'VERSION = "0.4.0-alpha.1"' in builder
    assert 'VERSION = "0.4.0-alpha.2"' in alpha2_builder
    assert "alpha1AssetsMayBeModified" in alpha2_builder
    print("Alpha 2 release contract passed 12 fail-closed checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
