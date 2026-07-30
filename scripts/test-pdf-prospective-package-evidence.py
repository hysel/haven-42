#!/usr/bin/env python3
"""Validate deterministic review-only pypdf compliance evidence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "scripts" / "generate-pdf-prospective-package-evidence.py"
SPEC = importlib.util.spec_from_file_location("pdf_evidence_generator", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def main() -> int:
    checks = 0
    first = MODULE.generate()
    second = MODULE.generate()
    assert first == second and set(first) == {
        "dependency-inventory.json",
        "THIRD-PARTY-NOTICES.txt",
        "sbom.cdx.json",
    }
    checks += 2
    inventory = json.loads((MODULE.OUTPUT / "dependency-inventory.json").read_text())
    component = inventory["components"][0]
    assert inventory["status"] == "review-only-not-package-evidence"
    assert component["mandatoryDependencies"] == [] and component["extrasSelected"] == []
    assert component["packageIncluded"] is False and component["runtimeAdmitted"] is False
    checks += 3
    sbom = json.loads((MODULE.OUTPUT / "sbom.cdx.json").read_text())
    assert sbom["bomFormat"] == "CycloneDX" and sbom["specVersion"] == "1.6"
    assert sbom["components"][0]["scope"] == "excluded"
    assert all("Users" not in json.dumps(value) and "192.168." not in json.dumps(value) for value in (inventory, sbom))
    checks += 3
    notices = (MODULE.OUTPUT / "THIRD-PARTY-NOTICES.txt").read_text()
    assert "pypdf 6.14.2" in notices and "Redistribution and use in source and binary forms" in notices
    assert "review-only" not in notices.lower()
    checks += 2
    print(f"Prospective PDF package evidence passed {checks} deterministic, non-admission checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
