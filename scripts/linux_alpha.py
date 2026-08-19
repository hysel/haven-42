#!/usr/bin/env python3
"""Effect-free Linux Alpha 2 hardware admission and setup planning."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import secrets
import sys
from typing import Any

import alpha2_model_selector as SELECTOR


SOURCE_ROOT = Path(__file__).resolve().parent.parent
ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
CONTRACT_PATH = ROOT / "config/linux-alpha-contract.json"
CATALOG_PATH = ROOT / "config/alpha-2-model-catalog.json"
REGISTRY_PATH = ROOT / "config/linux-alpha-component-registry.json"
EVIDENCE_PATH = ROOT / "config/alpha-2-model-selection-evidence.json"
GIB = 1024**3
SAFE_OS_ID = re.compile(r"^[a-z0-9][a-z0-9.-]{0,79}$")
SUPPORTED_DISTRIBUTIONS = {
    "ubuntu", "debian", "linuxmint", "pop", "fedora", "bazzite", "cachyos", "arch",
}


class LinuxAlphaError(ValueError):
    """Linux admission or plan input is invalid or lacks evidence."""


def _load(path: Path, label: str) -> Any:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise LinuxAlphaError(f"unsafe-{label}")
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LinuxAlphaError(f"invalid-{label}") from error


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    value = _load(path, "linux-alpha-contract")
    if (
        not isinstance(value, dict)
        or value.get("schemaVersion") != 1
        or value.get("contractId") != "haven42.linux-alpha"
        or value.get("version") != "0.4.0-alpha.2"
        or value.get("platform") != {
            "operatingSystem": "linux",
            "architecture": "x64",
            "minimumGlibcVersion": "2.39",
            "administratorRequired": False,
        }
        or value.get("managedSetup", {}).get("rootOrSudoAllowed") is not False
        or value.get("managedSetup", {}).get("shellOrPackageManagerAllowed") is not False
        or value.get("managedSetup", {}).get("serviceInstallationAllowed") is not False
        or value.get("managedSetup", {}).get("driverAutomationAllowed") is not False
        or value.get("managedSetup", {}).get("loopbackHost") != "127.0.0.1"
        or value.get("modelPolicy", {}).get("ownerApprovalRequiredForDefaultChange") is not True
    ):
        raise LinuxAlphaError("invalid-linux-alpha-contract")
    return value


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    value = _load(path, "alpha2-model-catalog")
    if (
        not isinstance(value, dict)
        or value.get("schemaVersion") != 1
        or value.get("catalogId") != "haven42.alpha2.text-models"
        or not isinstance(value.get("models"), list)
        or [item.get("id") for item in value["models"]] != [
            "qwen35-08b-q8", "qwen35-2b-q8", "qwen35-4b-q4",
            "qwen35-9b-q4", "qwen35-27b-q4", "qwen35-35b-q4",
        ]
    ):
        raise LinuxAlphaError("invalid-alpha2-model-catalog")
    return value


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    value = _load(path, "linux-component-registry")
    components = value.get("components") if isinstance(value, dict) else None
    if (
        value.get("registryId") != "haven42.linux-alpha.components"
        or not isinstance(components, list)
        or len(components) != 2
        or components[0].get("id") != "ollama-linux-core"
        or components[0].get("managedInstallationAllowed") is not True
        or components[0].get("minimumGlibcVersion") != "2.28"
        or components[1].get("id") != "ollama-linux-amd-rocm"
        or components[1].get("managedInstallationAllowed") is not False
    ):
        raise LinuxAlphaError("invalid-linux-component-registry")
    return value


def load_evidence(path: Path = EVIDENCE_PATH) -> list[dict[str, Any]]:
    value = _load(path, "alpha2-model-evidence")
    if (
        not isinstance(value, dict)
        or set(value) != {
            "schemaVersion", "kind", "release", "records", "promotionAuthority",
            "containsPrivateMachineIdentity", "containsRawPromptsOrResponses",
        }
        or value.get("schemaVersion") != 1
        or value.get("kind") != "alpha2-reviewed-automatic-selection-evidence"
        or value.get("release") != "0.4.0-alpha.2"
        or value.get("promotionAuthority") != "owner-review-required"
        or value.get("containsPrivateMachineIdentity") is not False
        or value.get("containsRawPromptsOrResponses") is not False
        or not isinstance(value.get("records"), list)
    ):
        raise LinuxAlphaError("invalid-alpha2-model-evidence")
    return value["records"]


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _version_tuple(value: Any) -> tuple[int, ...] | None:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", value):
        return None
    return tuple(int(item) for item in value.split("."))


def operating_system_id(snapshot: dict[str, Any]) -> str | None:
    platform_info = snapshot.get("platform") if isinstance(snapshot, dict) else None
    if not isinstance(platform_info, dict):
        return None
    distro = str(platform_info.get("distributionId") or "").casefold()
    distro = {"linuxmint": "linux-mint", "pop": "pop-os"}.get(distro, distro)
    version = str(platform_info.get("distributionVersion") or "").casefold()
    candidate = f"{distro}-{version}" if distro and version else ""
    return candidate if SAFE_OS_ID.fullmatch(candidate) else None


def setup_backend(snapshot: dict[str, Any]) -> dict[str, Any]:
    accelerators = snapshot.get("accelerators") if isinstance(snapshot, dict) else None
    if not isinstance(accelerators, list):
        raise LinuxAlphaError("invalid-hardware-snapshot")
    supported: list[tuple[str, dict[str, Any]]] = []
    for item in accelerators:
        if not isinstance(item, dict):
            raise LinuxAlphaError("invalid-hardware-snapshot")
        vendor_text = str(item.get("vendor", "")).strip().casefold()
        vendor = vendor_text if vendor_text in {"nvidia", "amd", "intel"} else None
        if vendor:
            supported.append((vendor, item))
    vendors = {vendor for vendor, _ in supported}
    if len(vendors) > 1:
        return {
            "backendMode": None, "components": [], "usableGpuMemoryGiB": 0,
            "blocker": "multiple-accelerators-require-manual-review",
        }
    if not supported:
        return {
            "backendMode": "cpu", "components": ["ollama-linux-core"],
            "usableGpuMemoryGiB": 0, "blocker": None,
        }
    vendor, accelerator = supported[0]
    memory = _number(accelerator.get("memoryGiB"))
    if vendor == "nvidia":
        if memory is None or memory <= 0 or accelerator.get("source") != "nvidia-smi":
            return {
                "backendMode": None, "components": [], "usableGpuMemoryGiB": 0,
                "blocker": "nvidia-capacity-or-driver-unverified",
            }
        return {
            "backendMode": "cuda", "components": ["ollama-linux-core"],
            "usableGpuMemoryGiB": memory, "blocker": None,
        }
    if vendor == "intel":
        return {
            "backendMode": None, "components": [], "usableGpuMemoryGiB": memory or 0,
            "blocker": "linux-intel-native-evidence-required",
        }
    return {
        "backendMode": None, "components": [], "usableGpuMemoryGiB": memory or 0,
        "blocker": "linux-amd-native-evidence-required",
    }


def evaluate_hardware(snapshot: dict[str, Any]) -> dict[str, Any]:
    contract = load_contract()
    platform_info = snapshot.get("platform") if isinstance(snapshot, dict) else None
    if not isinstance(platform_info, dict):
        raise LinuxAlphaError("invalid-hardware-snapshot")
    blockers: list[str] = []
    architecture = str(platform_info.get("architecture", "")).casefold()
    normalized_architecture = "x64" if architecture in {"x86_64", "amd64", "x64"} else architecture
    distro = str(platform_info.get("distributionId") or "").casefold()
    logical = _number(platform_info.get("logicalProcessors"))
    memory = _number(platform_info.get("systemMemoryGiB"))
    storage = _number(platform_info.get("availableStorageGiB"))
    libc_family = str(platform_info.get("libcFamily") or "").casefold()
    glibc = _version_tuple(platform_info.get("libcVersion"))
    minimum_glibc = _version_tuple(contract["platform"]["minimumGlibcVersion"])
    runtime_minimum_text = load_registry()["components"][0]["minimumGlibcVersion"]
    runtime_minimum_glibc = _version_tuple(runtime_minimum_text)
    effective_minimum_glibc = max(
        value for value in (minimum_glibc, runtime_minimum_glibc) if value is not None
    )
    if str(platform_info.get("operatingSystem", "")).casefold() != "linux":
        blockers.append("linux-required")
    if normalized_architecture != "x64":
        blockers.append("linux-x64-required")
    if distro not in SUPPORTED_DISTRIBUTIONS:
        blockers.append("linux-distribution-not-in-alpha2-matrix")
    if operating_system_id(snapshot) is None:
        blockers.append("linux-distribution-version-unavailable")
    if libc_family != "glibc":
        blockers.append("glibc-required")
    elif glibc is None or glibc < effective_minimum_glibc:
        blockers.append("glibc-version-threshold")
    policy = contract["minimumCandidateHardware"]
    if logical is None or logical < policy["logicalProcessors"]:
        blockers.append("logical-processor-threshold")
    if memory is None or memory < policy["systemMemoryGiB"]:
        blockers.append("system-memory-threshold")
    if storage is None or storage < policy["availableStorageGiB"]:
        blockers.append("storage-threshold")
    backend = setup_backend(snapshot)
    if backend["blocker"]:
        blockers.append(backend["blocker"])
    return {
        "decision": "candidate" if not blockers else "unsupported",
        "blockers": blockers,
        "operatingSystemId": operating_system_id(snapshot),
        "architecture": normalized_architecture,
        "logicalProcessors": int(logical) if logical is not None else None,
        "systemMemoryGiB": memory,
        "availableStorageGiB": storage,
        "runtimeCompatibility": {
            "libraryFamily": libc_family or None,
            "detectedVersion": platform_info.get("libcVersion"),
            "minimumPlatformVersion": contract["platform"]["minimumGlibcVersion"],
            "minimumRuntimeVersion": runtime_minimum_text,
            "effectiveMinimumVersion": ".".join(str(item) for item in effective_minimum_glibc),
            "decision": "compatible" if (
                libc_family == "glibc"
                and glibc is not None
                and glibc >= effective_minimum_glibc
            ) else "incompatible-or-unavailable",
        },
        "glibcVersion": platform_info.get("libcVersion"),
        "managedBackendCandidate": backend["backendMode"],
        "maximumUsableGpuMemoryGiB": backend["usableGpuMemoryGiB"],
        "localSetupAllowed": not blockers,
    }


def driver_guidance(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Explain detected Linux graphics readiness without changing system drivers."""
    hardware = evaluate_hardware(snapshot)
    backend = hardware.get("managedBackendCandidate")
    blockers = set(hardware.get("blockers", []))
    if backend == "cuda":
        decision = "ready"
        message = "The installed NVIDIA driver exposed a usable graphics accelerator. Haven 42 will not change it."
    elif "nvidia-capacity-or-driver-unverified" in blockers:
        decision = "action-required"
        message = "The NVIDIA driver or graphics memory could not be verified. Use your Linux distribution's driver tools, then check again; Haven 42 does not install drivers."
    elif "linux-amd-native-evidence-required" in blockers:
        decision = "evidence-pending"
        message = "AMD graphics hardware was detected, but this Linux acceleration route is not yet approved for managed setup. Haven 42 will not change the driver or silently use the CPU."
    elif "linux-intel-native-evidence-required" in blockers:
        decision = "evidence-pending"
        message = "Intel graphics hardware was detected, but this Linux acceleration route is not yet approved for managed setup. Haven 42 will not change the driver or silently use the CPU."
    else:
        decision = "not-required"
        message = "The reviewed CPU setup does not require a graphics-driver change."
    return {
        "decision": decision,
        "message": message,
        "automaticInstallationAllowed": False,
        "systemDriverChangesAllowed": False,
    }


def _required_storage_bytes(model: dict[str, Any], component: dict[str, Any]) -> int:
    return (
        component["byteLength"]
        + component["expandedByteLength"]
        + model["modelBytes"]
        + 2 * GIB
    )


def select_model(
    snapshot: dict[str, Any], evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    hardware = evaluate_hardware(snapshot)
    if hardware["decision"] != "candidate":
        return {
            "decision": "no-safe-recommendation", "hardware": hardware,
            "selected": None, "eligible": [], "automaticExecutionAllowed": False,
            "reason": "This computer does not meet the reviewed Linux Alpha 2 setup boundary.",
        }
    catalog = load_catalog()
    core = load_registry()["components"][0]
    storage_bytes = int((hardware["availableStorageGiB"] or 0) * GIB)
    admitted = [
        model["id"] for model in catalog["models"]
        if _required_storage_bytes(model, core) <= storage_bytes
    ]
    profile = {
        "platformFamily": "linux",
        "operatingSystemId": hardware["operatingSystemId"],
        "architecture": "x64",
        "backendMode": hardware["managedBackendCandidate"],
        "systemMemoryGiB": hardware["systemMemoryGiB"],
        "usableGpuMemoryGiB": hardware["maximumUsableGpuMemoryGiB"],
        "storageAdmittedModelIds": admitted,
        "requestedCapabilities": ["general.chat", "content.write", "content.summarize"],
        "provider": "ollama",
        # Selection evidence remains tied to the exact runtime used by the
        # recorded model cells. Managed setup performs a fresh bounded
        # inference check on the newer portable runtime before completing.
        "providerVersion": "0.32.5",
    }
    try:
        decision = SELECTOR.select_model(profile, load_evidence() if evidence is None else evidence)
    except SELECTOR.SelectionError as error:
        raise LinuxAlphaError(str(error)) from error
    model_by_id = {item["id"]: item for item in catalog["models"]}
    selected = model_by_id.get(decision["selectedModelId"])
    return {
        "decision": decision["decision"],
        "hardware": hardware,
        "selected": None if selected is None else {
            "id": selected["id"], "name": selected["name"],
            "manifestDigest": selected["manifestDigest"],
            "parameterClass": selected["parameterClass"],
            "quantization": selected["quantization"],
            "modelBytes": selected["modelBytes"],
            "requiredStorageGiB": math.ceil(
                _required_storage_bytes(selected, core) / GIB * 10
            ) / 10,
            "evidenceId": decision["evidenceId"],
        },
        "eligible": decision["fitModelIds"],
        "evidencePending": decision["evidencePendingModelIds"],
        "automaticExecutionAllowed": decision["automaticExecutionAllowed"],
        "reason": decision["reason"],
    }


def build_plan(snapshot: dict[str, Any], selected_model: dict[str, Any]) -> dict[str, Any]:
    decision = select_model(snapshot)
    catalog = load_catalog()
    registered = next((item for item in catalog["models"] if item == selected_model), None)
    if (
        registered is None
        or decision["automaticExecutionAllowed"] is not True
        or decision["selected"] is None
        or decision["selected"]["id"] != registered["id"]
    ):
        raise LinuxAlphaError("linux-model-not-automatically-admitted")
    backend = setup_backend(snapshot)
    core = load_registry()["components"][0]
    return {
        "schemaVersion": 1,
        "kind": "linux-alpha-setup-plan",
        "planId": secrets.token_urlsafe(24),
        "version": "0.4.0-alpha.2",
        "components": backend["components"],
        "modelId": registered["id"],
        "backendMode": backend["backendMode"],
        "gpuAccelerationRequired": backend["backendMode"] != "cpu",
        "requiredStorageBytes": _required_storage_bytes(registered, core),
        "effects": [
            "network-download", "portable-folder-files", "owned-process",
            "local-model-validation",
        ],
        "forbiddenEffects": load_contract()["forbiddenEffects"],
        "approvalRequired": True,
        "rememberApprovalAllowed": False,
        "driverAutomationAllowed": False,
    }
