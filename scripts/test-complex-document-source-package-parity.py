#!/usr/bin/env python3
"""Verify complex-document source evidence cannot imply package admission."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    contract = json.loads(
        (
            ROOT / "config/complex-document-source-package-parity-contract.json"
        ).read_text(encoding="utf-8")
    )
    native = json.loads(
        (ROOT / "config/complex-document-native-validation-contract.json").read_text(
            encoding="utf-8"
        )
    )
    checks = 0
    matrix = contract["matrix"]
    assert matrix["windowsSource"] and matrix["linuxSource"]
    assert not matrix["macosSource"]
    assert not any(
        matrix[value]
        for value in ("windowsPackage", "linuxPackage", "macosPackage")
    )
    checks += 3
    requirements = contract["futurePackageRequirements"]
    assert requirements["exactComponentInventoryRequired"]
    assert requirements["sourcePackageFixtureDigestParityRequired"]
    assert requirements["hostileContainerParityRequired"]
    assert requirements["semanticProvenanceParityRequired"]
    assert requirements["formulaAndTrackedChangeRejectionParityRequired"]
    assert requirements["nativePackageSmokeRequired"]
    assert requirements["residueFreeCleanupRequired"]
    assert requirements["thirdPartyDependencyExpected"] is False
    checks += 8
    assert not any(contract["authority"].values())
    assert native["platformEvidence"]["windowsSource"] is True
    assert native["platformEvidence"]["linuxSource"] is True
    assert native["platformEvidence"]["macosSource"] is False
    checks += 4
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    resources = json.loads(
        (ROOT / "package/resource-integrity.json").read_text(encoding="utf-8")
    )
    runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*")
        if path.is_file() and path.suffix in {".py", ".js", ".html", ".css", ".json"}
    )
    resource_text = json.dumps(resources, sort_keys=True)
    for relative in contract["currentExclusions"]:
        name = Path(relative).name
        assert name not in package
        assert name not in resource_text
        assert name not in runtime
        checks += 3
    print(f"Complex-document source/package parity passed: {checks} exclusion checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
