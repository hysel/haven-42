#!/usr/bin/env python3
"""Validate native complex-document orchestration remains review-only."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts/run-native-complex-document-validation.py"


def roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split(".", 1)[0])
    return result


def main() -> int:
    contract = json.loads(
        (ROOT / "config/complex-document-native-validation-contract.json").read_text(
            encoding="utf-8"
        )
    )
    checks = 0
    assert contract["status"] == "review-only-native-validation-no-runtime-admission"
    assert contract["requiredChecks"] == {
        "containerSecurity": 41,
        "semanticSecurity": 57,
    }
    assert contract["platformEvidence"] == {
        "windowsSource": True,
        "linuxSource": True,
        "macosSource": False,
        "windowsPackaged": False,
        "linuxPackaged": False,
        "macosPackaged": False,
    }
    assert not any(contract["authority"].values())
    checks += 4
    assert contract["limits"] == {
        "maximumCheckSeconds": 30,
        "maximumStdoutBytes": 1048576,
        "maximumStderrBytes": 65536,
    }
    text = RUNNER.read_text(encoding="utf-8")
    assert all(
        marker in text
        for marker in (
            "subprocess.Popen(",
            "native-check-output-limit-exceeded",
            "platform-mismatch",
            "rawDocumentContentRecorded",
        )
    )
    assert roots(RUNNER).isdisjoint({"requests", "socket", "urllib", "http"})
    checks += 3
    shell = (ROOT / "scripts/validate-complex-document-review.linux.sh").read_text(
        encoding="utf-8"
    )
    assert "uname -s" in shell
    assert "--platform linux" in shell
    assert "exec python3" in shell
    checks += 3
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    assert "run-native-complex-document-validation" not in package
    assert "review-complex-document-semantics" not in package
    checks += 2
    print(f"Complex-document native foundation passed {checks} offline checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
