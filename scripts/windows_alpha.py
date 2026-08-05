#!/usr/bin/env python3
"""Fail-closed Windows alpha readiness, model selection, and local metrics."""

from __future__ import annotations

import ctypes
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable


SOURCE_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
CONTRACT_PATH = ROOT / "config" / "windows-alpha-contract.json"
MODEL_CATALOG_PATH = ROOT / "config" / "windows-alpha-model-catalog.json"
COMPONENT_REGISTRY_PATH = ROOT / "config" / "windows-alpha-component-registry.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_MODEL = re.compile(r"^[a-z0-9][a-z0-9._:+/-]{0,127}$")
SAFE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SAFE_TEXT = re.compile(r"^[\x20-\x7e]{1,160}$")
AUTOMATIC_EVIDENCE = {"validated-exact-windows-cell"}
SUPPORTED_ARCHITECTURES = {"amd64", "x86_64", "x64"}
MAX_METRIC = 2**63 - 1
GIB = 1024**3
_CPU_SAMPLE_LOCK = threading.Lock()
_CPU_SAMPLE_PREVIOUS: tuple[int, int] | None = None
_GPU_PDH_LOCK = threading.Lock()
_GPU_PDH_QUERY: object | None = None
_GPU_PDH_UTILIZATION: object | None = None
_GPU_PDH_MEMORY: object | None = None
_GPU_PDH_PRIMED = False


class WindowsAlphaError(ValueError):
    """Raised for invalid or authority-broadening alpha input."""


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise WindowsAlphaError("invalid-json-root")
    return value


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    value = _load(path)
    if (
        value.get("schemaVersion") != 1
        or value.get("contractId") != "haven42.windows-alpha"
        or value.get("version") != "0.4.0-alpha.1"
        or value.get("implementationStatus") != "implementation-complete-native-validation-required"
    ):
        raise WindowsAlphaError("invalid-alpha-contract")
    platform_policy = value.get("platform")
    if platform_policy != {
        "operatingSystem": "windows",
        "minimumProduct": "Windows 11",
        "architecture": "x64",
        "administratorRequired": False,
    }:
        raise WindowsAlphaError("invalid-alpha-platform-policy")
    capability = value.get("capabilityPolicy", {})
    if (
        capability.get("admitted") != ["general.chat", "content.write", "content.summarize"]
        or capability.get("rendererMayBroaden") is not False
        or capability.get("serverEnforcementRequired") is not True
        or "media.image.create" not in capability.get("denied", [])
        or "software.workflow.execute" not in capability.get("denied", [])
    ):
        raise WindowsAlphaError("invalid-alpha-capability-policy")
    driver = value.get("driverPolicy", {})
    if driver.get("automationAllowed") is not False or driver.get("enterpriseDriverRequired") is not False:
        raise WindowsAlphaError("invalid-alpha-driver-policy")
    if any(
        forbidden not in value.get("forbiddenEffects", [])
        for forbidden in ("driver-install", "firewall-change", "system-service-change", "automatic-elevation")
    ):
        raise WindowsAlphaError("invalid-alpha-effect-policy")
    storage = value.get("managedSetup", {}).get("storagePreflight")
    if storage != {
        "freeReserveGiB": 2,
        "maximumExpandedGiBPerComponent": 4,
        "includeComponentArchives": True,
        "includeModelArtifact": True,
        "recheckBeforeEffects": True,
    }:
        raise WindowsAlphaError("invalid-alpha-storage-policy")
    managed = value.get("managedSetup", {})
    if (
        managed.get("managedStorageScope") != "inside-extracted-folder/Haven42-Data"
        or managed.get("removalPolicy") != {
            "explicitConfirmationRequired": True,
            "ownedDataOnly": True,
            "applicationSelfDeletionAllowed": False,
            "driversOrExternalInstallationsRemoved": False,
        }
        or managed.get("managedProcessPolicy") != {
            "windowsJobObjectRequired": True,
            "assignBeforeProcessResume": True,
            "killProcessTreeWhenHavenExits": True,
            "externalProviderProcessesIncluded": False,
            "processNameAloneGrantsTermination": False,
        }
    ):
        raise WindowsAlphaError("invalid-alpha-managed-storage-policy")
    return value


def load_model_catalog(path: Path = MODEL_CATALOG_PATH) -> dict[str, Any]:
    value = _load(path)
    if (
        set(value) != {"schemaVersion", "catalogId", "catalogStatus", "source", "selectionPolicy", "models"}
        or value.get("schemaVersion") != 1
        or value.get("catalogId") != "haven42.windows-alpha.chat-models"
        or value.get("catalogStatus") != "candidate-ladder-requires-exact-windows-evidence"
    ):
        raise WindowsAlphaError("invalid-alpha-model-catalog")
    source = value.get("source", {})
    if (
        set(source) != {"registry", "library", "retrievedAtUtc"}
        or source.get("registry") != "https://registry.ollama.ai"
        or source.get("library") != "qwen3.5"
        or not isinstance(source.get("retrievedAtUtc"), str)
    ):
        raise WindowsAlphaError("invalid-alpha-model-catalog")
    policy = value.get("selectionPolicy", {})
    if (
        set(policy) != {
            "capabilityId", "trustedPrequantizedFirst", "largestValidatedComfortableFit",
            "minimumMemoryReservePercent", "minimumMemoryReserveGiB",
            "runtimeVerificationRequired", "unvalidatedCandidateMayAutoSelect",
            "cloudModelsAllowed",
        }
        or policy.get("capabilityId") != "general.chat"
        or policy.get("trustedPrequantizedFirst") is not True
        or policy.get("largestValidatedComfortableFit") is not True
        or policy.get("minimumMemoryReservePercent") != 25
        or policy.get("minimumMemoryReserveGiB") != 2
        or policy.get("runtimeVerificationRequired") is not True
        or policy.get("unvalidatedCandidateMayAutoSelect") is not False
        or policy.get("cloudModelsAllowed") is not False
    ):
        raise WindowsAlphaError("invalid-alpha-model-catalog")
    models = value.get("models")
    if not isinstance(models, list) or len(models) != 6:
        raise WindowsAlphaError("invalid-alpha-model-catalog")
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    seen_digests: set[str] = set()
    previous_priority = 0
    for model in models:
        required = {
            "id", "name", "manifestDigest", "modelLayerDigest", "modelBytes",
            "parameterClass", "quantization", "minimumSystemMemoryGiB",
            "minimumUsableGpuMemoryGiB", "candidatePriority", "windowsEvidenceStatus",
        }
        if not isinstance(model, dict) or set(model) != required:
            raise WindowsAlphaError("invalid-alpha-model-entry")
        if (
            not SAFE_MODEL.fullmatch(model["name"])
            or not SAFE_ID.fullmatch(model["id"])
            or not HEX64.fullmatch(model["manifestDigest"])
            or not HEX64.fullmatch(model["modelLayerDigest"])
            or not re.fullmatch(r"(?:0\.8|2|4|9|27|35)b", model["parameterClass"])
            or model["quantization"] not in {"Q8_0", "Q4_K_M"}
            or model["id"] in seen_ids
            or model["name"] in seen_names
            or model["manifestDigest"] in seen_digests
            or not isinstance(model["modelBytes"], int)
            or not 0 < model["modelBytes"] <= 128 * GIB
            or isinstance(model["candidatePriority"], bool)
            or not isinstance(model["candidatePriority"], int)
            or model["candidatePriority"] <= previous_priority
            or isinstance(model["minimumSystemMemoryGiB"], bool)
            or not isinstance(model["minimumSystemMemoryGiB"], (int, float))
            or not 8 <= model["minimumSystemMemoryGiB"] <= 512
            or isinstance(model["minimumUsableGpuMemoryGiB"], bool)
            or not isinstance(model["minimumUsableGpuMemoryGiB"], (int, float))
            or not 0 <= model["minimumUsableGpuMemoryGiB"] <= 256
            or model["windowsEvidenceStatus"] not in {
                "required", "validated-exact-windows-cell"
            }
        ):
            raise WindowsAlphaError("invalid-alpha-model-entry")
        seen_ids.add(model["id"])
        seen_names.add(model["name"])
        seen_digests.add(model["manifestDigest"])
        previous_priority = model["candidatePriority"]
    return value


def setup_backend(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Choose one measured accelerator and its matching managed backend."""
    accelerators = snapshot.get("accelerators", [])
    if not isinstance(accelerators, list):
        raise WindowsAlphaError("invalid-hardware-snapshot")
    candidates: list[tuple[float, int, str, str]] = []
    priorities = {"cuda": 3, "rocm": 2, "vulkan": 1}
    for item in accelerators:
        if not isinstance(item, dict):
            continue
        vendor = str(item.get("vendor", "")).casefold()
        if "nvidia" in vendor:
            backend, component = "cuda", "ollama-windows-core"
        elif "amd" in vendor or "radeon" in vendor:
            backend, component = "rocm", "ollama-windows-amd-rocm"
        elif "intel" in vendor:
            backend, component = "vulkan", "ollama-windows-core"
        else:
            continue
        memory = _number(item.get("memoryGiB")) or 0
        candidates.append((memory, priorities[backend], backend, component))
    if not candidates:
        return {
            "backendMode": "cpu", "usableGpuMemoryGiB": 0,
            "components": ["ollama-windows-core"],
        }
    memory, _priority, backend, component = max(candidates)
    components = ["ollama-windows-core"]
    if component != "ollama-windows-core":
        components.append(component)
    return {
        "backendMode": backend, "usableGpuMemoryGiB": memory,
        "components": components,
    }


def required_setup_storage_bytes(
    model: dict[str, Any],
    component_ids: list[str],
    *,
    contract: dict[str, Any] | None = None,
    catalog: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
) -> int:
    """Return conservative peak bytes for archives, extraction, model, and reserve."""
    contract = contract or load_contract()
    catalog = catalog or load_model_catalog()
    registry = registry or load_component_registry()
    if model not in catalog["models"] or not isinstance(component_ids, list) or not component_ids:
        raise WindowsAlphaError("invalid-alpha-storage-request")
    components = {item["id"]: item for item in registry["components"]}
    if len(set(component_ids)) != len(component_ids) or any(item not in components for item in component_ids):
        raise WindowsAlphaError("invalid-alpha-storage-request")
    policy = contract["managedSetup"]["storagePreflight"]
    return int(
        sum(components[item]["byteLength"] for item in component_ids)
        + len(component_ids) * policy["maximumExpandedGiBPerComponent"] * GIB
        + model["modelBytes"]
        + policy["freeReserveGiB"] * GIB
    )


def load_component_registry(path: Path = COMPONENT_REGISTRY_PATH) -> dict[str, Any]:
    value = _load(path)
    if (
        value.get("schemaVersion") != 1
        or value.get("registryId") != "haven42.windows-alpha.components"
        or value.get("defaultDecision") != "deny"
        or value.get("runtimeAdmission") != "alpha-consent-only-native-evidence-required"
    ):
        raise WindowsAlphaError("invalid-alpha-component-registry")
    components = value.get("components")
    if not isinstance(components, list) or len(components) != 2:
        raise WindowsAlphaError("invalid-alpha-component-registry")
    expected_ids = {"ollama-windows-core", "ollama-windows-amd-rocm"}
    if {component.get("id") for component in components} != expected_ids:
        raise WindowsAlphaError("invalid-alpha-component-entry")
    for component in components:
        if (
            component.get("installationScope") != "current-user"
            or not SAFE_TEXT.fullmatch(str(component.get("displayName", "")))
            or not SAFE_TEXT.fullmatch(str(component.get("purpose", "")))
            or component.get("archiveFormat") != "zip"
            or component.get("extractedExecutableSignatureRequired") is not True
            or component.get("managedInstallationAllowed") is not True
            or not isinstance(component.get("byteLength"), int)
            or component["byteLength"] <= 0
            or not HEX64.fullmatch(str(component.get("sha256", "")))
            or not str(component.get("sourceUrl", "")).startswith(
                "https://github.com/ollama/ollama/releases/download/v0.32.5/"
            )
            or not str(component.get("artifactName", "")).endswith(".zip")
        ):
            raise WindowsAlphaError("invalid-alpha-component-entry")
    rocm = next(component for component in components if component["id"] == "ollama-windows-amd-rocm")
    if (
        rocm.get("version") != "0.32.5"
        or rocm.get("technologyName") != "ROCm"
        or rocm.get("technologyVersion") != "7.1"
        or rocm.get("technologyVersionSourceUrl")
        != "https://raw.githubusercontent.com/ollama/ollama/v0.32.5/.github/workflows/release.yaml"
    ):
        raise WindowsAlphaError("invalid-alpha-component-entry")
    for guidance in value.get("driverGuidance", []):
        if guidance.get("automationAllowed") is not False or not str(guidance.get("officialUrl", "")).startswith("https://"):
            raise WindowsAlphaError("invalid-driver-guidance")
    return value


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and 0 <= value <= 1_000_000:
        return float(value)
    return None


def _normalized_architecture(value: object) -> str:
    text = str(value or "").casefold()
    return "x64" if text in SUPPORTED_ARCHITECTURES else text


def evaluate_hardware(snapshot: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load_contract()
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("platform"), dict):
        raise WindowsAlphaError("invalid-hardware-snapshot")
    platform_info = snapshot["platform"]
    operating_system = str(platform_info.get("operatingSystem", "")).casefold()
    architecture = _normalized_architecture(platform_info.get("architecture"))
    logical_processors = _number(platform_info.get("logicalProcessors"))
    memory = _number(platform_info.get("systemMemoryGiB"))
    storage = _number(platform_info.get("availableStorageGiB"))
    policy = contract["minimumCandidateHardware"]
    blockers: list[str] = []
    if operating_system != "windows":
        blockers.append("windows-11-required")
    if architecture != "x64":
        blockers.append("windows-x64-required")
    product = str(platform_info.get("productName", ""))
    if product and "windows 11" not in product.casefold():
        blockers.append("windows-11-required")
    if logical_processors is None or logical_processors < policy["logicalProcessors"]:
        blockers.append("logical-processor-threshold")
    if memory is None or memory < policy["systemMemoryGiB"]:
        blockers.append("system-memory-threshold")
    if storage is None or storage < policy["availableStorageGiB"]:
        blockers.append("storage-threshold")
    accelerators = snapshot.get("accelerators", [])
    if not isinstance(accelerators, list):
        raise WindowsAlphaError("invalid-hardware-snapshot")
    backend = setup_backend(snapshot)
    vendors = sorted({
        str(item.get("vendor", "unknown")).casefold()
        for item in accelerators
        if isinstance(item, dict)
    })
    return {
        "decision": "candidate" if not blockers else "unsupported",
        "blockers": blockers,
        "operatingSystem": operating_system or "unknown",
        "architecture": architecture or "unknown",
        "logicalProcessors": int(logical_processors) if logical_processors is not None else None,
        "systemMemoryGiB": memory,
        "availableStorageGiB": storage,
        "maximumUsableGpuMemoryGiB": backend["usableGpuMemoryGiB"],
        "managedBackendCandidate": backend["backendMode"],
        "acceleratorVendors": vendors,
        "uiMayOpen": True,
        "localChatSetupAllowed": not blockers,
    }


def select_model(
    snapshot: dict[str, Any],
    contract: dict[str, Any] | None = None,
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = contract or load_contract()
    catalog = catalog or load_model_catalog()
    hardware = evaluate_hardware(snapshot, contract)
    if hardware["decision"] != "candidate":
        return {
            "decision": "no-safe-recommendation",
            "hardware": hardware,
            "selected": None,
            "eligible": [],
            "automaticExecutionAllowed": False,
            "reason": "The computer is below the Windows alpha minimum threshold.",
        }
    memory = hardware["systemMemoryGiB"] or 0
    gpu_memory = hardware["maximumUsableGpuMemoryGiB"] or 0
    storage = hardware["availableStorageGiB"] or 0
    backend = setup_backend(snapshot)
    registry = load_component_registry()
    eligible: list[dict[str, Any]] = []
    storage_requirements: dict[str, float] = {}
    for model in catalog["models"]:
        if memory < model["minimumSystemMemoryGiB"]:
            continue
        # A missing GPU measurement is zero capacity, not unlimited capacity.
        # This keeps CPU-only and unmeasured systems on the explicitly admitted
        # CPU model instead of silently selecting a larger GPU-oriented model.
        if gpu_memory < model["minimumUsableGpuMemoryGiB"]:
            continue
        required_bytes = required_setup_storage_bytes(
            model,
            backend["components"],
            contract=contract,
            catalog=catalog,
            registry=registry,
        )
        required_gib = math.ceil((required_bytes / GIB) * 10) / 10
        storage_requirements[model["id"]] = required_gib
        if storage < required_gib:
            continue
        eligible.append(model)
    if not eligible:
        return {
            "decision": "no-safe-recommendation",
            "hardware": hardware,
            "selected": None,
            "eligible": [],
            "automaticExecutionAllowed": False,
            "reason": (
                "No catalog model has enough verified memory, accelerator, and storage headroom."
                if storage_requirements
                else "No catalog model fits the bounded hardware profile."
            ),
        }
    selected = max(eligible, key=lambda item: item["candidatePriority"])
    automatic = selected["windowsEvidenceStatus"] in AUTOMATIC_EVIDENCE
    return {
        "decision": "validated-selection" if automatic else "candidate-selection",
        "hardware": hardware,
        "selected": {
            "id": selected["id"],
            "name": selected["name"],
            "manifestDigest": selected["manifestDigest"],
            "parameterClass": selected["parameterClass"],
            "quantization": selected["quantization"],
            "modelBytes": selected["modelBytes"],
            "requiredStorageGiB": storage_requirements[selected["id"]],
            "evidenceStatus": selected["windowsEvidenceStatus"],
        },
        "eligible": [item["id"] for item in eligible],
        "automaticExecutionAllowed": automatic,
        "reason": (
            "The strongest exact Windows-validated model with bounded headroom was selected."
            if automatic
            else "The strongest fitting catalog candidate still requires exact Windows evidence."
        ),
    }


def driver_guidance(snapshot: dict[str, Any], registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return official manual guidance; never infer an install command."""
    registry = registry or load_component_registry()
    guidance_by_vendor = {item["vendor"]: item for item in registry["driverGuidance"]}
    result: list[dict[str, Any]] = []
    accelerators = snapshot.get("accelerators", [])
    if not isinstance(accelerators, list):
        raise WindowsAlphaError("invalid-hardware-snapshot")
    for item in accelerators:
        if not isinstance(item, dict):
            raise WindowsAlphaError("invalid-hardware-snapshot")
        vendor_text = str(item.get("vendor", "")).casefold()
        vendor = next((name for name in ("nvidia", "amd", "intel") if name in vendor_text), None)
        if vendor is None or vendor not in guidance_by_vendor:
            continue
        source = guidance_by_vendor[vendor]
        driver_version = item.get("driverVersion")
        detected = isinstance(driver_version, str) and bool(driver_version.strip())
        result.append({
            "vendor": vendor,
            "model": str(item.get("model", "Unknown"))[:120],
            "driverDetected": detected,
            "driverVersion": driver_version.strip()[:80] if detected else None,
            "decision": "present-review-compatibility" if detected else "manual-driver-guidance-required",
            "officialUrl": source["officialUrl"],
            "consumerChannels": list(source["consumerChannels"]),
            "automaticInstallAllowed": False,
            "administratorActionStarted": False,
        })
    return result


def validate_provider_metrics(value: object) -> dict[str, float | int | None]:
    expected = {
        "inputTokens", "outputTokens", "totalTokens", "tokensPerSecond",
        "totalDurationMs", "loadDurationMs", "promptDurationMs", "providerReported",
    }
    if not isinstance(value, dict) or set(value) != expected or value.get("providerReported") is not True:
        raise WindowsAlphaError("invalid-provider-metrics")
    result: dict[str, float | int | None] = {}
    for key in expected - {"providerReported"}:
        item = value[key]
        if item is None:
            result[key] = None
        elif isinstance(item, bool) or not isinstance(item, (int, float)) or item < 0 or item > MAX_METRIC:
            raise WindowsAlphaError("invalid-provider-metrics")
        else:
            result[key] = item
    if (
        result["inputTokens"] is not None
        and result["outputTokens"] is not None
        and result["totalTokens"] != result["inputTokens"] + result["outputTokens"]
    ):
        raise WindowsAlphaError("invalid-provider-metrics")
    result["providerReported"] = True
    return result


class SessionTokenTotals:
    """Memory-only aggregation of strictly validated provider metrics."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.requests = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.speed_sum = 0.0
        self.speed_samples = 0

    def add(self, metrics: object) -> dict[str, int | float]:
        value = validate_provider_metrics(metrics)
        self.requests += 1
        self.input_tokens += int(value["inputTokens"] or 0)
        self.output_tokens += int(value["outputTokens"] or 0)
        if value["tokensPerSecond"] is not None:
            self.speed_sum += float(value["tokensPerSecond"])
            self.speed_samples += 1
        return self.summary()

    def summary(self) -> dict[str, int | float]:
        return {
            "requestCount": self.requests,
            "inputTokens": self.input_tokens,
            "outputTokens": self.output_tokens,
            "totalTokens": self.input_tokens + self.output_tokens,
            "averageTokensPerSecond": round(self.speed_sum / self.speed_samples, 2) if self.speed_samples else 0.0,
            "persisted": False,
        }


def _windows_memory_sample() -> dict[str, int | None]:
    if os.name != "nt":
        return {"systemMemoryUsedBytes": None, "systemMemoryTotalBytes": None, "havenProcessMemoryBytes": None}

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
            ("total_physical", ctypes.c_ulonglong), ("available_physical", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong), ("available_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
            ("available_extended_virtual", ctypes.c_ulonglong),
        ]

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong), ("page_fault_count", ctypes.c_ulong),
            ("peak_working_set_size", ctypes.c_size_t), ("working_set_size", ctypes.c_size_t),
            ("quota_peak_paged_pool_usage", ctypes.c_size_t), ("quota_paged_pool_usage", ctypes.c_size_t),
            ("quota_peak_non_paged_pool_usage", ctypes.c_size_t), ("quota_non_paged_pool_usage", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t), ("peak_pagefile_usage", ctypes.c_size_t),
        ]

    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    total = used = process_memory = None
    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        total = int(status.total_physical)
        used = int(status.total_physical - status.available_physical)
    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    if ctypes.windll.psapi.GetProcessMemoryInfo(
        ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    ):
        process_memory = int(counters.working_set_size)
    return {
        "systemMemoryUsedBytes": used,
        "systemMemoryTotalBytes": total,
        "havenProcessMemoryBytes": process_memory,
    }


def _windows_cpu_sample() -> float | None:
    global _CPU_SAMPLE_PREVIOUS
    if os.name != "nt":
        return None

    class FileTime(ctypes.Structure):
        _fields_ = [("low", ctypes.c_ulong), ("high", ctypes.c_ulong)]

    idle = FileTime(); kernel = FileTime(); user = FileTime()
    if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
        return None
    number = lambda value: (int(value.high) << 32) | int(value.low)
    idle_value = number(idle)
    total_value = number(kernel) + number(user)
    with _CPU_SAMPLE_LOCK:
        previous = _CPU_SAMPLE_PREVIOUS
        _CPU_SAMPLE_PREVIOUS = (idle_value, total_value)
    if previous is None:
        return None
    idle_delta = idle_value - previous[0]
    total_delta = total_value - previous[1]
    if total_delta <= 0 or idle_delta < 0 or idle_delta > total_delta:
        return None
    return round(100.0 * (1.0 - idle_delta / total_delta), 1)


def _nvidia_sample() -> dict[str, int | float | None]:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return {
            "gpuUtilizationPercent": None,
            "gpuMemoryUsedBytes": None,
            "gpuMemoryTotalBytes": None,
        }
    try:
        process = subprocess.run(
            [executable, "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=False,
            timeout=2,
            check=False,
            env={"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")},
        )
    except (OSError, subprocess.TimeoutExpired):
        process = None
    if process is None or process.returncode != 0 or len(process.stdout) > 4096:
        return {"gpuUtilizationPercent": None, "gpuMemoryUsedBytes": None, "gpuMemoryTotalBytes": None}
    rows = []
    for line in process.stdout.decode("utf-8", errors="replace").splitlines()[:16]:
        match = re.fullmatch(r"\s*(\d{1,3})\s*,\s*(\d{1,8})\s*,\s*(\d{1,8})\s*", line)
        if match:
            rows.append(tuple(int(value) for value in match.groups()))
    if not rows:
        return {"gpuUtilizationPercent": None, "gpuMemoryUsedBytes": None, "gpuMemoryTotalBytes": None}
    return {
        "gpuUtilizationPercent": max(min(row[0], 100) for row in rows),
        "gpuMemoryUsedBytes": sum(row[1] for row in rows) * 1024 * 1024,
        "gpuMemoryTotalBytes": sum(row[2] for row in rows) * 1024 * 1024,
    }


def _aggregate_windows_gpu_counters(
    utilization_rows: list[tuple[str, float]],
    memory_rows: list[tuple[str, float]],
) -> dict[str, int | float | None]:
    """Aggregate vendor-neutral Windows GPU counters without over-counting engines."""
    engines: dict[str, float] = {}
    for name, raw_value in utilization_rows[:8192]:
        if not isinstance(name, str) or not isinstance(raw_value, (int, float)) or not math.isfinite(raw_value):
            continue
        match = re.fullmatch(
            r"pid_\d+_(luid_0x[0-9a-f]+_0x[0-9a-f]+_phys_\d+_eng_\d+)_engtype_.+",
            name.casefold(),
        )
        if match and 0 <= raw_value <= 100:
            engines[match.group(1)] = engines.get(match.group(1), 0.0) + float(raw_value)
    memory_values = [
        float(value)
        for name, value in memory_rows[:256]
        if isinstance(name, str)
        and re.fullmatch(r"luid_0x[0-9a-f]+_0x[0-9a-f]+_phys_\d+", name.casefold())
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and 0 <= value <= MAX_METRIC
    ]
    return {
        "gpuUtilizationPercent": round(min(max(engines.values()), 100.0), 1) if engines else None,
        "gpuMemoryUsedBytes": int(sum(memory_values)) if memory_values else None,
        "gpuMemoryTotalBytes": None,
    }


def _windows_pdh_gpu_sample() -> dict[str, int | float | None]:
    """Read Windows' vendor-neutral GPU Engine counters through the trusted PDH API."""
    global _GPU_PDH_QUERY, _GPU_PDH_UTILIZATION, _GPU_PDH_MEMORY, _GPU_PDH_PRIMED
    unavailable = {
        "gpuUtilizationPercent": None,
        "gpuMemoryUsedBytes": None,
        "gpuMemoryTotalBytes": None,
    }
    if os.name != "nt":
        return unavailable

    class CounterValueUnion(ctypes.Union):
        _fields_ = [
            ("long_value", ctypes.c_long), ("double_value", ctypes.c_double),
            ("large_value", ctypes.c_longlong), ("ansi_value", ctypes.c_char_p),
            ("wide_value", ctypes.c_wchar_p),
        ]

    class CounterValue(ctypes.Structure):
        _anonymous_ = ("value",)
        _fields_ = [("status", ctypes.c_ulong), ("value", CounterValueUnion)]

    class CounterItem(ctypes.Structure):
        _fields_ = [("name", ctypes.c_wchar_p), ("value", CounterValue)]

    def status_code(value: int) -> int:
        return int(value) & 0xFFFFFFFF

    def formatted_rows(pdh: object, counter: object) -> list[tuple[str, float]]:
        size = ctypes.c_ulong(0)
        count = ctypes.c_ulong(0)
        result = pdh.PdhGetFormattedCounterArrayW(counter, 0x00000200, ctypes.byref(size), ctypes.byref(count), None)
        if status_code(result) != 0x800007D2 or size.value == 0 or size.value > 8 * 1024 * 1024 or count.value > 8192:
            return []
        buffer = ctypes.create_string_buffer(size.value)
        result = pdh.PdhGetFormattedCounterArrayW(
            counter, 0x00000200, ctypes.byref(size), ctypes.byref(count), ctypes.byref(buffer)
        )
        if status_code(result) != 0 or count.value > 8192:
            return []
        items = ctypes.cast(buffer, ctypes.POINTER(CounterItem))
        return [
            (str(items[index].name or "")[:240], float(items[index].value.double_value))
            for index in range(count.value)
            if items[index].value.status in (0, 1)
        ]

    with _GPU_PDH_LOCK:
        try:
            if _GPU_PDH_QUERY is None:
                system_directory = ctypes.create_unicode_buffer(32768)
                length = ctypes.windll.kernel32.GetSystemDirectoryW(system_directory, len(system_directory))
                if not 0 < length < len(system_directory):
                    return unavailable
                pdh = ctypes.WinDLL(str(Path(system_directory.value) / "pdh.dll"), use_last_error=True)
                pdh.PdhOpenQueryW.argtypes = [ctypes.c_wchar_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
                pdh.PdhAddEnglishCounterW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
                pdh.PdhCollectQueryData.argtypes = [ctypes.c_void_p]
                pdh.PdhGetFormattedCounterArrayW.argtypes = [
                    ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong),
                    ctypes.POINTER(ctypes.c_ulong), ctypes.c_void_p,
                ]
                query = ctypes.c_void_p()
                utilization = ctypes.c_void_p()
                memory = ctypes.c_void_p()
                if status_code(pdh.PdhOpenQueryW(None, 0, ctypes.byref(query))) != 0:
                    return unavailable
                if status_code(pdh.PdhAddEnglishCounterW(
                    query, r"\GPU Engine(*)\Utilization Percentage", 0, ctypes.byref(utilization)
                )) != 0 or status_code(pdh.PdhAddEnglishCounterW(
                    query, r"\GPU Adapter Memory(*)\Dedicated Usage", 0, ctypes.byref(memory)
                )) != 0:
                    pdh.PdhCloseQuery(query)
                    return unavailable
                _GPU_PDH_QUERY = (pdh, query)
                _GPU_PDH_UTILIZATION = utilization
                _GPU_PDH_MEMORY = memory
            pdh, query = _GPU_PDH_QUERY
            if status_code(pdh.PdhCollectQueryData(query)) != 0:
                return unavailable
            if not _GPU_PDH_PRIMED:
                _GPU_PDH_PRIMED = True
                return unavailable
            return _aggregate_windows_gpu_counters(
                formatted_rows(pdh, _GPU_PDH_UTILIZATION),
                formatted_rows(pdh, _GPU_PDH_MEMORY),
            )
        except (AttributeError, OSError, TypeError, ValueError):
            return unavailable


def _gpu_sample() -> dict[str, int | float | None]:
    nvidia = _nvidia_sample()
    if nvidia["gpuUtilizationPercent"] is not None:
        return nvidia
    return _windows_pdh_gpu_sample()


def sample_resources() -> dict[str, Any]:
    sample = {
        "schemaVersion": 1,
        "kind": "local-resource-sample",
        "sampledAtMonotonicMs": int(time.monotonic() * 1000),
        "systemCpuPercent": _windows_cpu_sample(),
        **_windows_memory_sample(),
        **_gpu_sample(),
        "ollamaLoadedModelBytes": None,
        "ollamaLoadedVramBytes": None,
        "externalTelemetryUsed": False,
        "persisted": False,
    }
    return sample


class ResourceHistory:
    """Bounded in-memory resource samples with no background thread authority."""

    def __init__(self, maximum_samples: int = 30, sampler: Callable[[], dict[str, Any]] = sample_resources) -> None:
        if maximum_samples < 1 or maximum_samples > 120:
            raise WindowsAlphaError("invalid-resource-history-limit")
        self._samples: deque[dict[str, Any]] = deque(maxlen=maximum_samples)
        self._sampler = sampler
        self._lock = threading.Lock()

    def take(self) -> dict[str, Any]:
        value = self._sampler()
        if not isinstance(value, dict) or value.get("kind") != "local-resource-sample":
            raise WindowsAlphaError("invalid-resource-sample")
        with self._lock:
            self._samples.append(dict(value))
        return value

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            samples = list(self._samples)
        return {"samples": samples, "sampleCount": len(samples), "persisted": False, "externalTelemetryUsed": False}


def main() -> int:
    contract = load_contract()
    catalog = load_model_catalog()
    registry = load_component_registry()
    print(json.dumps({
        "version": contract["version"],
        "modelCount": len(catalog["models"]),
        "componentCount": len(registry["components"]),
        "runtimeAdmitted": False,
        "managedSetupCandidateAvailable": True,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
