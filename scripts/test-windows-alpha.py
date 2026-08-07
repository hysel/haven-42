#!/usr/bin/env python3
"""Hostile offline tests for the Windows 0.4 Alpha 1 foundation."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("windows_alpha", ROOT / "scripts/windows_alpha.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def rejected(code: str, function, *arguments) -> None:
    try:
        function(*arguments)
    except MODULE.WindowsAlphaError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"unsafe input accepted: {code}")


def snapshot(*, ram: float = 32, storage: float = 100, gpu: float | None = 16) -> dict:
    accelerators = [] if gpu is None else [{
        "vendor": "NVIDIA", "model": "Synthetic GPU", "memoryGiB": gpu,
        "memoryType": "dedicated", "state": "detected", "source": "synthetic",
        "confidence": "high",
    }]
    return {
        "platform": {
            "operatingSystem": "windows", "productName": "Windows 11 Pro",
            "architecture": "AMD64", "logicalProcessors": 8,
            "systemMemoryGiB": ram, "availableStorageGiB": storage,
        },
        "accelerators": accelerators,
    }


def main() -> int:
    checks = 0
    contract = MODULE.load_contract()
    catalog = MODULE.load_model_catalog()
    registry = MODULE.load_component_registry()
    guardrails = json.loads(
        (ROOT / "config/windows-alpha-response-guardrail-cases.json").read_text(encoding="utf-8")
    )
    assert contract["capabilityPolicy"]["admitted"] == [
        "general.chat", "content.write", "content.summarize",
    ]
    assert registry["runtimeAdmission"] == "alpha-consent-only-native-evidence-required"
    assert {item["id"] for item in registry["components"]} == {
        "ollama-windows-core", "ollama-windows-amd-rocm",
    }
    rocm = next(item for item in registry["components"] if item["id"] == "ollama-windows-amd-rocm")
    assert (rocm["version"], rocm["technologyName"], rocm["technologyVersion"]) == (
        "0.32.5", "ROCm", "7.1",
    )
    assert all(item["automationAllowed"] is False for item in registry["driverGuidance"])
    assert guardrails["schemaVersion"] == 1
    assert guardrails["matrixId"] == "haven42.windows-alpha.response-guardrails"
    assert guardrails["version"] == "0.4.0-alpha.1"
    assert guardrails["executionStatus"] == "native-evaluation-required"
    assert guardrails["capabilities"] == [
        "general.chat", "content.write", "content.summarize",
    ]
    assert guardrails["promotionPolicy"] == {
        "criticalViolationBlocksRecommendation": True,
        "repeatedHighViolationBlocksRecommendation": True,
        "promptComplianceIsNotSecurityEvidence": True,
        "humanReviewRequired": True,
    }
    assert len(guardrails["cases"]) == 10
    assert len({item["id"] for item in guardrails["cases"]}) == 10
    assert all(item["severity"] in {"critical", "high"} for item in guardrails["cases"])
    assert all(
        set(item) == {"id", "severity", "prompt", "expectedBehavior", "forbiddenBehavior"}
        and all(isinstance(item[key], str) and 1 <= len(item[key]) <= 300 for key in item)
        for item in guardrails["cases"]
    )
    assert [item["name"] for item in catalog["models"]] == [
        "qwen3.5:0.8b", "qwen3.5:2b", "qwen3.5:4b",
        "qwen3.5:9b", "qwen3.5:27b", "qwen3.5:35b",
    ]
    assert [item["name"] for item in catalog["models"] if item["windowsEvidenceStatus"] == "validated-exact-windows-cell"] == ["qwen3.5:9b"]
    assert [item["name"] for item in catalog["models"] if item["windowsEvidenceStatus"] == "admitted-bounded-windows-cpu-self-test"] == ["qwen3.5:0.8b"]
    checks += 16

    for path, mutate, code, loader in (
        (MODULE.CONTRACT_PATH, lambda value: value["capabilityPolicy"].update(rendererMayBroaden=True), "invalid-alpha-capability-policy", MODULE.load_contract),
        (MODULE.CONTRACT_PATH, lambda value: value["driverPolicy"].update(automationAllowed=True), "invalid-alpha-driver-policy", MODULE.load_contract),
        (MODULE.CONTRACT_PATH, lambda value: value["managedSetup"]["storagePreflight"].update(freeReserveGiB=0), "invalid-alpha-storage-policy", MODULE.load_contract),
        (MODULE.CONTRACT_PATH, lambda value: value["managedSetup"]["removalPolicy"].update(applicationSelfDeletionAllowed=True), "invalid-alpha-managed-storage-policy", MODULE.load_contract),
        (MODULE.CONTRACT_PATH, lambda value: value["managedSetup"]["managedProcessPolicy"].update(externalProviderProcessesIncluded=True), "invalid-alpha-managed-storage-policy", MODULE.load_contract),
        (MODULE.CONTRACT_PATH, lambda value: value["forbiddenEffects"].remove("driver-install"), "invalid-alpha-effect-policy", MODULE.load_contract),
        (MODULE.MODEL_CATALOG_PATH, lambda value: value["models"][0].update(manifestDigest="0"), "invalid-alpha-model-entry", MODULE.load_model_catalog),
        (MODULE.MODEL_CATALOG_PATH, lambda value: value["selectionPolicy"].update(unvalidatedCandidateMayAutoSelect=True), "invalid-alpha-model-catalog", MODULE.load_model_catalog),
        (MODULE.MODEL_CATALOG_PATH, lambda value: value["models"][0].update(windowsEvidenceStatus="invented"), "invalid-alpha-model-entry", MODULE.load_model_catalog),
        (MODULE.MODEL_CATALOG_PATH, lambda value: value["models"][0].update(minimumUsableGpuMemoryGiB=-1), "invalid-alpha-model-entry", MODULE.load_model_catalog),
        (MODULE.MODEL_CATALOG_PATH, lambda value: value["source"].update(registry="https://evil.example"), "invalid-alpha-model-catalog", MODULE.load_model_catalog),
        (MODULE.MODEL_CATALOG_PATH, lambda value: value["models"][1].update(candidatePriority=10), "invalid-alpha-model-entry", MODULE.load_model_catalog),
        (MODULE.COMPONENT_REGISTRY_PATH, lambda value: value["components"][0].update(sourceUrl="https://evil.example/setup.exe"), "invalid-alpha-component-entry", MODULE.load_component_registry),
        (MODULE.COMPONENT_REGISTRY_PATH, lambda value: value["components"][0].update(displayName=""), "invalid-alpha-component-entry", MODULE.load_component_registry),
        (MODULE.COMPONENT_REGISTRY_PATH, lambda value: value["components"][1].update(technologyVersion="0.32.5"), "invalid-alpha-component-entry", MODULE.load_component_registry),
        (MODULE.COMPONENT_REGISTRY_PATH, lambda value: value["driverGuidance"][0].update(automationAllowed=True), "invalid-driver-guidance", MODULE.load_component_registry),
    ):
        with tempfile.TemporaryDirectory() as directory:
            hostile_path = Path(directory) / "hostile.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            mutate(value)
            hostile_path.write_text(json.dumps(value), encoding="utf-8")
            rejected(code, loader, hostile_path)
            checks += 1

    assessment = MODULE.evaluate_hardware(snapshot())
    assert assessment["decision"] == "candidate"
    assert assessment["maximumUsableGpuMemoryGiB"] == 16
    assert assessment["localChatSetupAllowed"] is True
    checks += 3

    cases = (
        (snapshot(ram=7), "system-memory-threshold"),
        (snapshot(storage=14), "storage-threshold"),
        ({**snapshot(), "platform": {**snapshot()["platform"], "logicalProcessors": 2}}, "logical-processor-threshold"),
        ({**snapshot(), "platform": {**snapshot()["platform"], "operatingSystem": "linux"}}, "windows-11-required"),
        ({**snapshot(), "platform": {**snapshot()["platform"], "architecture": "arm64"}}, "windows-x64-required"),
    )
    for value, blocker in cases:
        result = MODULE.evaluate_hardware(value)
        assert result["decision"] == "unsupported"
        assert blocker in result["blockers"]
        assert result["uiMayOpen"] is True
        assert result["localChatSetupAllowed"] is False
        checks += 4

    selections = (
        (snapshot(ram=8, gpu=None), "qwen3.5:0.8b"),
        (snapshot(ram=12, gpu=4), "qwen3.5:2b"),
        (snapshot(ram=16, gpu=6), "qwen3.5:4b"),
        (snapshot(ram=24, gpu=16), "qwen3.5:9b"),
        (snapshot(ram=48, gpu=24), "qwen3.5:27b"),
        (snapshot(ram=64, gpu=32), "qwen3.5:35b"),
    )
    for value, expected in selections:
        result = MODULE.select_model(value)
        assert result["selected"]["name"] == expected
        expected_automatic = expected in {"qwen3.5:0.8b", "qwen3.5:9b"}
        expected_decision = (
            "bounded-cpu-self-test-selection"
            if expected == "qwen3.5:0.8b"
            else "validated-selection"
            if expected == "qwen3.5:9b"
            else "candidate-selection"
        )
        assert result["decision"] == expected_decision
        assert result["automaticExecutionAllowed"] is expected_automatic
        checks += 3

    cpu_large_ram = MODULE.select_model(snapshot(ram=128, gpu=None))
    assert cpu_large_ram["selected"]["name"] == "qwen3.5:0.8b"
    assert cpu_large_ram["eligible"] == ["qwen35-08b-q8"]
    assert cpu_large_ram["automaticExecutionAllowed"] is True
    checks += 3

    storage_fallback = MODULE.select_model(snapshot(ram=64, storage=20, gpu=32))
    assert storage_fallback["selected"]["name"] == "qwen3.5:9b"
    assert storage_fallback["selected"]["requiredStorageGiB"] <= 20
    assert "qwen35-27b-q4" not in storage_fallback["eligible"]
    checks += 3

    amd_snapshot = snapshot(ram=64, storage=15, gpu=32)
    amd_snapshot["accelerators"][0]["vendor"] = "AMD"
    amd_storage_fallback = MODULE.select_model(amd_snapshot)
    assert amd_storage_fallback["selected"]["name"] == "qwen3.5:4b"
    assert amd_storage_fallback["selected"]["requiredStorageGiB"] <= 15
    checks += 2

    mixed = snapshot(ram=32, storage=100, gpu=None)
    mixed["accelerators"] = [
        {"vendor": "NVIDIA", "model": "small", "memoryGiB": 4},
        {"vendor": "AMD", "model": "large", "memoryGiB": 16},
    ]
    mixed_assessment = MODULE.evaluate_hardware(mixed)
    assert mixed_assessment["managedBackendCandidate"] == "rocm"
    assert mixed_assessment["maximumUsableGpuMemoryGiB"] == 16
    assert MODULE.select_model(mixed)["selected"]["name"] == "qwen3.5:9b"
    checks += 3

    unsupported = MODULE.select_model(snapshot(ram=7, storage=100, gpu=None))
    assert unsupported["decision"] == "no-safe-recommendation"
    assert unsupported["selected"] is None
    checks += 2

    driver_snapshot = snapshot()
    driver_snapshot["accelerators"][0]["driverVersion"] = "582.70"
    guidance = MODULE.driver_guidance(driver_snapshot)
    assert guidance[0]["vendor"] == "nvidia"
    assert guidance[0]["driverDetected"] is True
    assert guidance[0]["automaticInstallAllowed"] is False
    assert guidance[0]["officialUrl"].startswith("https://www.nvidia.com/")
    checks += 4

    unmeasured_intel = snapshot(ram=16, storage=100, gpu=0)
    unmeasured_intel["accelerators"][0]["vendor"] = "Intel"
    assert MODULE.setup_backend(unmeasured_intel)["backendMode"] == "cpu"
    assert MODULE.select_model(unmeasured_intel)["selected"]["name"] == "qwen3.5:0.8b"
    assert MODULE.select_model(unmeasured_intel)["automaticExecutionAllowed"] is True
    measured_intel = snapshot(ram=16, storage=100, gpu=8)
    measured_intel["accelerators"][0]["vendor"] = "Intel"
    assert MODULE.setup_backend(measured_intel)["backendMode"] == "vulkan"
    assert MODULE.automatic_setup_admitted(catalog["models"][0], unmeasured_intel) is True
    assert MODULE.automatic_setup_admitted(catalog["models"][0], measured_intel) is False
    checks += 6

    metrics = {
        "inputTokens": 10, "outputTokens": 20, "totalTokens": 30,
        "tokensPerSecond": 5.5, "totalDurationMs": 5000,
        "loadDurationMs": 1000, "promptDurationMs": 500,
        "providerReported": True,
    }
    totals = MODULE.SessionTokenTotals()
    assert totals.add(metrics) == {
        "requestCount": 1, "inputTokens": 10, "outputTokens": 20,
        "totalTokens": 30, "averageTokensPerSecond": 5.5, "persisted": False,
    }
    totals.add({**metrics, "inputTokens": 5, "outputTokens": 5, "totalTokens": 10, "tokensPerSecond": 4.5})
    assert totals.summary()["totalTokens"] == 40
    assert totals.summary()["averageTokensPerSecond"] == 5.0
    totals.reset()
    assert totals.summary()["requestCount"] == 0
    checks += 4

    rejected("invalid-provider-metrics", MODULE.validate_provider_metrics, {**metrics, "totalTokens": 31})
    rejected("invalid-provider-metrics", MODULE.validate_provider_metrics, {**metrics, "inputTokens": -1})
    rejected("invalid-provider-metrics", MODULE.validate_provider_metrics, {**metrics, "providerReported": False})
    rejected("invalid-provider-metrics", MODULE.validate_provider_metrics, {**metrics, "command": "calc.exe"})
    checks += 4

    sample_counter = 0

    def sampler() -> dict:
        nonlocal sample_counter
        sample_counter += 1
        return {
            "schemaVersion": 1, "kind": "local-resource-sample",
            "sampledAtMonotonicMs": sample_counter, "systemCpuPercent": 1,
            "systemMemoryUsedBytes": 2, "systemMemoryTotalBytes": 3,
            "havenProcessMemoryBytes": 1, "gpuUtilizationPercent": None,
            "gpuMemoryUsedBytes": None, "gpuMemoryTotalBytes": None,
            "ollamaLoadedModelBytes": None, "ollamaLoadedVramBytes": None,
            "externalTelemetryUsed": False, "persisted": False,
        }

    history = MODULE.ResourceHistory(maximum_samples=2, sampler=sampler)
    history.take(); history.take(); history.take()
    history_value = history.snapshot()
    assert history_value["sampleCount"] == 2
    assert [item["sampledAtMonotonicMs"] for item in history_value["samples"]] == [2, 3]
    assert history_value["persisted"] is False and history_value["externalTelemetryUsed"] is False
    rejected("invalid-resource-history-limit", MODULE.ResourceHistory, 121)
    checks += 4

    generic_gpu = MODULE._aggregate_windows_gpu_counters(
        [
            ("pid_10_luid_0x00000000_0x00000001_phys_0_eng_0_engtype_3D", 30.0),
            ("pid_20_luid_0x00000000_0x00000001_phys_0_eng_0_engtype_3D", 25.0),
            ("pid_10_luid_0x00000000_0x00000001_phys_0_eng_1_engtype_Compute", 70.0),
            ("hostile", 99.0),
        ],
        [("luid_0x00000000_0x00000001_phys_0", 3 * 1024**3)],
    )
    assert generic_gpu == {
        "gpuUtilizationPercent": 70.0,
        "gpuMemoryUsedBytes": 3 * 1024**3,
        "gpuMemoryTotalBytes": None,
    }
    assert MODULE._aggregate_windows_gpu_counters(
        [("hostile", float("nan")), ("pid_1_bad", 50.0)],
        [("bad", 1.0), ("luid_0x0_0x1_phys_0", float("inf"))],
    ) == {
        "gpuUtilizationPercent": None,
        "gpuMemoryUsedBytes": None,
        "gpuMemoryTotalBytes": None,
    }
    checks += 2

    print(f"Windows alpha hostile tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
