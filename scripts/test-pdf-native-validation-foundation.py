#!/usr/bin/env python3
"""Validate native PDF review planning without claiming unrun platform evidence."""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts/run-native-pdf-worker-validation.py"
SPEC = importlib.util.spec_from_file_location("native_pdf_validation", RUNNER)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            values.add(node.module.split(".", 1)[0])
    return values


def main() -> int:
    contract = MODULE.load()
    checks = 0
    assert contract["status"] == "review-only-native-validation-no-runtime-admission"
    assert contract["platformEvidence"] == {
        "windowsSource": True,
        "linuxSource": True,
        "macosSource": False,
        "windowsPackaged": False,
        "linuxPackaged": False,
        "macosPackaged": False,
    }
    assert not any(contract["parity"].values())
    checks += 3
    assert contract["exactArtifactSizeBytes"] == 349514
    assert contract["validationLimits"] == {
        "maximumCheckSeconds": 45,
        "maximumStdoutBytes": 1048576,
        "maximumStderrBytes": 65536,
    }
    runner_source = RUNNER.read_text(encoding="utf-8")
    assert all(
        marker in runner_source
        for marker in ("subprocess.Popen(", "drain_bounded", "native-check-output-limit-exceeded")
    )
    checks += 3
    for platform_id in ("windows", "linux", "macos"):
        plan = MODULE.describe(platform_id)
        assert plan["platform"] == platform_id
        assert plan["networkUsed"] is False
        assert plan["dependencyInstalled"] is False
        assert plan["packageTested"] is False
        assert plan["runtimeAdmissionGranted"] is False
        checks += 5
    assert imports(RUNNER).isdisjoint({"requests", "socket", "urllib", "http"})
    assert MODULE.TESTS and all("-" not in identifier for identifier, _, _ in MODULE.TESTS)
    checks += 2
    shell = (ROOT / "scripts/validate-restricted-pdf-worker.linux.sh").read_text(encoding="utf-8")
    assert "uname -s" in shell and "--platform linux" in shell and "exec python3" in shell
    checks += 3
    intake = json.loads((ROOT / "config/pdf-hostile-corpus-intake-policy.json").read_text())
    assert intake["acceptedArtifacts"] == []
    assert not any(intake["authority"].values())
    assert intake["requirements"]["automaticDownloadAllowed"] is False
    assert intake["requirements"]["explicitRedistributionPermissionRequired"] is True
    assert intake["requirements"]["knownLiveMalwareAllowed"] is False
    checks += 5
    runtime = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "web").rglob("*.py"))
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    assert "run-native-pdf-worker-validation" not in runtime + package
    assert "restricted-pdf-worker" not in package
    checks += 2
    print(f"PDF native validation foundation passed {checks} offline security and parity checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
