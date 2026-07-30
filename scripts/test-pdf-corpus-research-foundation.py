#!/usr/bin/env python3
"""Validate metadata-only PDF corpus research remains non-operational."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.update(item.name.split(".", 1)[0] for item in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            values.add(node.module.split(".", 1)[0])
    return values


def main() -> int:
    catalog = json.loads(
        (ROOT / "config/pdf-corpus-candidate-catalog.json").read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "config/pdf-hostile-corpus-intake-policy.json").read_text(encoding="utf-8")
    )
    verifier = ROOT / "scripts/verify-pdf-corpus-intake.py"
    checks = 0
    assert catalog["status"] == "metadata-research-only-no-artifacts-selected"
    assert len(catalog["sources"]) == 3
    assert catalog["selectedArtifacts"] == []
    assert not any(catalog["effects"].values())
    checks += 4
    for source in catalog["sources"]:
        assert source["sourcePage"].startswith("https://github.com/")
        assert source["artifactLicenseScopeConfirmed"] is False
        assert source["selectionDecision"].startswith("blocked-")
        checks += 3
    assert policy["acceptedArtifacts"] == []
    assert policy["requirements"]["automaticDownloadAllowed"] is False
    assert policy["requirements"]["knownLiveMalwareAllowed"] is False
    assert not any(policy["authority"].values())
    checks += 4
    imports = imported_roots(verifier)
    assert imports.isdisjoint({"requests", "socket", "http", "ftplib", "subprocess"})
    assert "urlopen" not in verifier.read_text(encoding="utf-8")
    checks += 2
    print(f"PDF corpus research foundation passed {checks} non-acquisition checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
