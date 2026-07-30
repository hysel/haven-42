#!/usr/bin/env python3
"""Validate future PDF parity requirements without admitting package content."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parity = json.loads(
        (ROOT / "config/pdf-source-package-parity-contract.json").read_text(
            encoding="utf-8"
        )
    )
    native = json.loads(
        (ROOT / "config/pdf-parser-native-validation-contract.json").read_text(
            encoding="utf-8"
        )
    )
    prospective = json.loads(
        (ROOT / "config/pdf-parser-prospective-package-evidence.json").read_text(
            encoding="utf-8"
        )
    )
    checks = 0
    assert parity["status"] == "parity-contract-defined-capability-not-admitted"
    assert parity["requiredCells"] == {
        "windowsSource": True,
        "linuxSource": True,
        "macosSource": False,
        "windowsPackage": False,
        "linuxPackage": False,
        "macosPackage": False,
    }
    assert parity["requiredCells"] == {
        "windowsSource": native["platformEvidence"]["windowsSource"],
        "linuxSource": native["platformEvidence"]["linuxSource"],
        "macosSource": native["platformEvidence"]["macosSource"],
        "windowsPackage": native["platformEvidence"]["windowsPackaged"],
        "linuxPackage": native["platformEvidence"]["linuxPackaged"],
        "macosPackage": native["platformEvidence"]["macosPackaged"],
    }
    checks += 3
    assert len(parity["requiredPackagedComponentsAfterAdmission"]) == 7
    assert len(parity["requiredParityAssertions"]) == 7
    assert all(parity["packageIntegrity"].values())
    assert not any(parity["authority"].values())
    checks += 4
    assert not any(prospective["generation"].values())
    assert not any(prospective["authority"].values())
    checks += 2
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8").casefold()
    resources = (ROOT / "package/resource-integrity.json").read_text(
        encoding="utf-8"
    ).casefold()
    for marker in ("pypdf", "restricted-pdf-worker", "pdf-parser-artifact-lock"):
        assert marker not in package
        assert marker not in resources
        checks += 2
    print(f"PDF source/package parity foundation passed {checks} exclusion checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
