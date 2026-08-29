#!/usr/bin/env python3
"""Offline policy tests for Linux Alpha 2 hardware and model admission."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("linux_alpha", ROOT / "scripts/linux_alpha.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def snapshot(vendor: str | None = "NVIDIA") -> dict:
    accelerators = [] if vendor is None else [{
        "vendor": vendor,
        "model": "Test accelerator",
        "memoryGiB": 16,
        "source": "nvidia-smi" if vendor == "NVIDIA" else "lspci",
        "driverVersion": "595.84",
    }]
    return {
        "platform": {
            "operatingSystem": "linux", "architecture": "x86_64",
            "logicalProcessors": 8, "systemMemoryGiB": 32,
            "availableStorageGiB": 64, "distributionId": "ubuntu",
            "distributionVersion": "26.04", "libcFamily": "glibc",
            "libcVersion": "2.42",
        },
        "accelerators": accelerators,
    }


def evidence(model_id: str, os_id: str = "ubuntu-26.04", backend: str = "cuda") -> dict:
    catalog = MODULE.load_catalog()
    policy, _ = MODULE.SELECTOR.load_policy()
    model = next(item for item in catalog["models"] if item["id"] == model_id)
    return {
        "evidenceId": f"alpha2-{model_id}-{os_id}-{backend}",
        "modelId": model_id,
        "manifestDigest": model["manifestDigest"],
        "platformFamily": "linux",
        "operatingSystemId": os_id,
        "architecture": "x64",
        "backendMode": backend,
        "provider": "ollama",
        "providerVersion": "0.32.5",
        "selectorPolicyCanonicalSha256": MODULE.SELECTOR.canonical_sha256(policy),
        "minimumTestedSystemMemoryGiB": 16,
        "minimumTestedUsableGpuMemoryGiB": 0 if backend == "cpu" else 16,
        "capabilities": ["general.chat", "content.write", "content.summarize"],
        "status": "passed",
    }


def main() -> None:
    checks = 0
    MODULE.load_contract()
    MODULE.load_catalog()
    MODULE.load_registry()
    reviewed = MODULE.load_evidence()
    assert len(reviewed) == 22
    checks += 4

    cuda = snapshot()
    hardware = MODULE.evaluate_hardware(cuda)
    assert hardware["decision"] == "candidate"
    assert hardware["managedBackendCandidate"] == "cuda"
    assert hardware["operatingSystemId"] == "ubuntu-26.04"
    assert hardware["runtimeCompatibility"] == {
        "libraryFamily": "glibc",
        "detectedVersion": "2.42",
        "minimumPlatformVersion": "2.39",
        "minimumRuntimeVersion": "2.28",
        "effectiveMinimumVersion": "2.39",
        "decision": "compatible",
    }
    empty = MODULE.select_model(cuda, [])
    assert empty["automaticExecutionAllowed"] is False
    assert empty["selected"] is None
    admitted = MODULE.select_model(cuda, [evidence("qwen35-4b-q4")])
    assert admitted["automaticExecutionAllowed"] is True
    assert admitted["selected"]["id"] == "qwen35-4b-q4"
    committed_cuda = MODULE.select_model(cuda)
    assert committed_cuda["automaticExecutionAllowed"] is True
    assert committed_cuda["selected"]["id"] == "qwen35-4b-q4"
    installed_model = next(
        item for item in MODULE.load_catalog()["models"]
        if item["id"] == committed_cuda["selected"]["id"]
    )
    low_storage = copy.deepcopy(cuda)
    low_storage["platform"]["availableStorageGiB"] = 1
    assert "storage-threshold" in MODULE.evaluate_hardware(low_storage)["blockers"]
    assert MODULE.select_model(low_storage)["automaticExecutionAllowed"] is False
    assert MODULE.resume_setup_admitted(installed_model, low_storage) is True
    resume_plan = MODULE.build_resume_plan(low_storage, installed_model)
    assert resume_plan["modelId"] == installed_model["id"]
    assert resume_plan["backendMode"] == "cuda"
    low_storage["platform"]["systemMemoryGiB"] = 4
    assert MODULE.resume_setup_admitted(installed_model, low_storage) is False
    checks += 15

    cpu = snapshot(None)
    cpu_evidence = evidence("qwen35-08b-q8", backend="cpu")
    cpu_decision = MODULE.select_model(cpu, [cpu_evidence])
    assert cpu_decision["selected"]["id"] == "qwen35-08b-q8"
    assert cpu_decision["hardware"]["maximumUsableGpuMemoryGiB"] == 0
    committed_cpu = MODULE.select_model(cpu)
    assert committed_cpu["selected"]["id"] == "qwen35-08b-q8"
    checks += 3

    exact_profiles = {
        "ubuntu": ("26.04", "ubuntu-26.04"),
        "debian": ("13", "debian-13"),
        "linuxmint": ("22.3", "linux-mint-22.3"),
        "pop": ("24.04", "pop-os-24.04"),
        "fedora": ("44", "fedora-44"),
        "bazzite": ("44", "bazzite-44"),
        "cachyos": ("rolling", "cachyos-rolling"),
        "arch": ("rolling", "arch-rolling"),
    }
    for distribution_id, (version, expected_id) in exact_profiles.items():
        profile = snapshot(None)
        profile["platform"].update(
            distributionId=distribution_id, distributionVersion=version,
        )
        assert MODULE.operating_system_id(profile) == expected_id
        assert MODULE.evaluate_hardware(profile)["decision"] == "candidate"
        checks += 2

    rolling = snapshot(None)
    rolling["platform"].update(
        distributionId="arch", distributionVersion="rolling",
    )
    assert MODULE.evaluate_hardware(rolling)["operatingSystemId"] == "arch-rolling"
    mint = snapshot(None)
    mint["platform"].update(distributionId="linuxmint", distributionVersion="22.3")
    assert MODULE.evaluate_hardware(mint)["operatingSystemId"] == "linux-mint-22.3"
    pop = snapshot(None)
    pop["platform"].update(distributionId="pop", distributionVersion="24.04")
    assert MODULE.evaluate_hardware(pop)["operatingSystemId"] == "pop-os-24.04"
    checks += 3

    for field, value, blocker in (
        ("architecture", "arm64", "linux-x64-required"),
        ("logicalProcessors", 2, "logical-processor-threshold"),
        ("systemMemoryGiB", 4, "system-memory-threshold"),
        ("availableStorageGiB", 4, "storage-threshold"),
        ("distributionId", "unknown", "linux-distribution-not-in-alpha2-matrix"),
        ("distributionVersion", None, "linux-distribution-version-unavailable"),
        ("libcVersion", "2.27", "glibc-version-threshold"),
    ):
        hostile = copy.deepcopy(cuda)
        hostile["platform"][field] = value
        result = MODULE.evaluate_hardware(hostile)
        assert result["decision"] == "unsupported" and blocker in result["blockers"]
        checks += 1
    non_glibc = copy.deepcopy(cuda)
    non_glibc["platform"].update(libcFamily="musl", libcVersion="1.2.5")
    result = MODULE.evaluate_hardware(non_glibc)
    assert result["runtimeCompatibility"]["decision"] == "incompatible-or-unavailable"
    assert "glibc-required" in result["blockers"]
    checks += 1
    multi = copy.deepcopy(cuda)
    multi["accelerators"].append({"vendor": "AMD", "memoryGiB": 16, "source": "lspci"})
    assert "multiple-accelerators-require-manual-review" in MODULE.evaluate_hardware(multi)["blockers"]
    amd = snapshot("AMD")
    assert "linux-amd-native-evidence-required" in MODULE.evaluate_hardware(amd)["blockers"]
    assert MODULE.driver_guidance(amd)["decision"] == "evidence-pending"
    intel = snapshot("Intel")
    assert "linux-intel-native-evidence-required" in MODULE.evaluate_hardware(intel)["blockers"]
    assert MODULE.driver_guidance(intel)["decision"] == "evidence-pending"
    assert MODULE.driver_guidance(cpu)["decision"] == "not-required"
    assert MODULE.driver_guidance(cuda)["decision"] == "ready"
    misleading = snapshot("Not Intel")
    assert MODULE.setup_backend(misleading)["backendMode"] == "cpu"
    checks += 8

    wrong = evidence("qwen35-4b-q4", os_id="ubuntu-24.04")
    assert MODULE.select_model(cuda, [wrong])["automaticExecutionAllowed"] is False
    wrong = evidence("qwen35-4b-q4", backend="cpu")
    assert MODULE.select_model(cuda, [wrong])["automaticExecutionAllowed"] is False
    wrong = evidence("qwen35-4b-q4")
    wrong["manifestDigest"] = "0" * 64
    try:
        MODULE.select_model(cuda, [wrong])
    except MODULE.LinuxAlphaError:
        pass
    else:
        raise AssertionError("altered digest accepted")
    checks += 3

    print(f"Linux Alpha admission passed {checks} policy and hostile checks.")


if __name__ == "__main__":
    main()
