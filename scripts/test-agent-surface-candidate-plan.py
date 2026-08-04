#!/usr/bin/env python3
"""Hostile tests for candidate-only agent-surface planning."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "scripts/evaluate-agent-surface-candidate-plan.py"
SPEC = importlib.util.spec_from_file_location("candidate_surface_plan", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def request(surface="aider", **changes):
    profile = MODULE.CONTRACT["surfaces"][surface]
    value = {
        "surface": surface,
        "platform": "windows",
        "model": "qwen3.5:9b",
        "endpoint": "http://127.0.0.1:11434",
        "discovery": {"executableName": profile["expectedExecutable"], "version": profile["expectedVersion"], "regularFile": True, "linkOrReparse": False},
    }
    value.update(changes)
    return value


def rejected(value, reason):
    try:
        MODULE.evaluate(value)
    except MODULE.CandidatePlanRejected as error:
        assert str(error) == reason, (str(error), reason)
        return
    raise AssertionError(reason)


def main() -> int:
    for surface in ("aider", "opencode"):
        value = MODULE.evaluate(request(surface))
        assert value["dryRun"] is True
        assert not any(value["effects"].values())
        assert not any(value["authority"].values())
        assert value["configTarget"]["scope"] == "repository-direct-child"
        assert value["configTarget"]["preexistingBehavior"] == "reject"
    rejected(request(model="qwen;calc.exe"), "model-shape")
    rejected(request(endpoint="https://example.com:11434"), "endpoint-address")
    rejected(request(endpoint="http://127.0.0.1:8080"), "endpoint-port")
    rejected(request(endpoint="http://user@127.0.0.1:11434"), "endpoint-shape")
    rejected(request(endpoint="http://127.0.0.1:bad"), "endpoint-shape")
    rejected(request(discovery={"executableName": "aider", "version": "latest", "regularFile": True, "linkOrReparse": False}), "discovery-mismatch")
    rejected(request(discovery={"executableName": "aider", "version": "0.86.2", "regularFile": False, "linkOrReparse": False}), "discovery-mismatch")
    rejected(request(discovery={"executableName": "aider", "version": "0.86.2", "regularFile": True, "linkOrReparse": True}), "discovery-mismatch")
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    runtime = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "web").rglob("*") if path.is_file() and path.suffix in {".py", ".js", ".html", ".css"})
    assert "evaluate-agent-surface-candidate-plan" not in package + runtime
    print("Agent-surface candidate planning passed 20 dry-run and injection checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
