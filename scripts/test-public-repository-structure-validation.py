#!/usr/bin/env python3
"""Static and mocked tests for read-only public repository structure validation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "scripts/run-public-repository-structure-validation.py"
SPEC = importlib.util.spec_from_file_location("public_structure", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def main() -> int:
    cases = {
        "python-cli-click-8.2.1": ["pyproject.toml", "src/click/core.py", "tests/test_basic.py"],
        "node-web-express-5.1.0": ["package.json", "lib/application.js", "test/app.js"],
        "rust-library-serde-json-1.0.140": ["Cargo.toml", "Cargo.lock", "src/lib.rs"],
    }
    for candidate, paths in cases.items():
        expected = MODULE.CONTRACT["expected"][candidate]
        detected = MODULE.detect(paths)
        assert detected[0]["ecosystem"] == expected
        assert detected[0]["confidence"] in {"medium", "high"}
        assert detected[0]["rulePackId"]
    with patch.object(MODULE.VALIDATOR, "inspect", return_value={"commit": "a" * 40}), patch.object(MODULE, "paths_for", return_value=cases["python-cli-click-8.2.1"]):
        result = MODULE.validate("python-cli-click-8.2.1", Path("unused"))
    assert result["runtimeContextPlan"]["contentIncluded"] is False
    assert result["runtimeContextPlan"]["localPathIncluded"] is False
    assert result["workflowSelection"] == ["repository-discovery", "implementation-plan", "code-review"]
    assert result["remediationTemplates"] == []
    assert not any(result["effects"].values())
    assert not any(result["authority"].values())
    assert "scoped-write" not in result["workflowSelection"]
    runtime = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "web").rglob("*") if path.is_file() and path.suffix in {".py", ".js", ".html", ".css"})
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    assert "run-public-repository-structure-validation" not in runtime + package
    print("Public repository structure validation passed 19 read-only boundary checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
