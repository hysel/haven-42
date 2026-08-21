#!/usr/bin/env python3
"""Repository tests for the Apple M4 llama.cpp lifecycle cell."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "alpha2-macos-llamacpp-lifecycle.py"
VALIDATOR = ROOT / "scripts" / "validate-alpha2-macos-llamacpp-lifecycle-result.py"
SPEC = importlib.util.spec_from_file_location("llamacpp_lifecycle", RUNNER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-macos-llamacpp-lifecycle-result",
        "outcome": "passed",
        "profile": {"hardware": "Apple M4", "memoryGiB": 16, "os": "macOS", "architecture": "arm64"},
        "runtime": {"name": "llama.cpp", "commit": "cd644c395", "serverSha256": "a" * 64},
        "model": {"id": "Qwen3.5-0.8B-Q4_0-GGUF", "sha256": "b" * 64},
        "checks": {
            "loopbackOnly": True, "webUiDisabled": True, "authenticationRequired": True,
            "metalDetected": True, "allLayersOffloaded": True, "boundedInference": True,
            "forcedTimeoutObserved": True, "postTimeoutRecovery": True, "restart": True,
            "listenerClosed": True,
        },
        "metrics": {"firstCompletionTokens": 3, "recoveryCompletionTokens": 4, "durationSeconds": 12.5},
        "authority": {"changesDefaults": False, "changesSupport": False, "changesPackaging": False},
        "privacy": {"containsPrompt": False, "containsResponse": False, "containsPrivatePath": False, "containsCredential": False},
    }


def validate(data: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "result.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return subprocess.run([sys.executable, str(VALIDATOR), str(path)], text=True, capture_output=True)


def main() -> int:
    checks = 0
    source = RUNNER.read_text(encoding="utf-8")
    for required in ("127.0.0.1", "--no-webui", '"--reasoning", "off"', "--verbose", "--api-key", "forcedTimeoutObserved", "containsPrivatePath"):
        assert required in source
        checks += 1
    assert MODULE.full_offload_observed("load_tensors: offloaded 29/29 layers to GPU")
    assert MODULE.full_offload_observed("offloaded all layers")
    assert not MODULE.full_offload_observed("load_tensors: offloaded 28/29 layers to GPU")
    checks += 3
    assert validate(fixture()).returncode == 0
    checks += 1
    for mutation in (
        lambda value: value["checks"].__setitem__("metalDetected", False),
        lambda value: value["runtime"].__setitem__("serverSha256", "latest"),
        lambda value: value["authority"].__setitem__("changesDefaults", True),
        lambda value: value["profile"].__setitem__("memoryGiB", 32),
    ):
        candidate = fixture()
        mutation(candidate)
        assert validate(candidate).returncode != 0
        checks += 1
    candidate = fixture()
    candidate["model"]["id"] = "/" + "Users/private/model.gguf"
    assert validate(candidate).returncode != 0
    checks += 1
    print(f"Apple M4 llama.cpp lifecycle tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
