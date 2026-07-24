#!/usr/bin/env python3
"""Read-only, sanitized system readiness and effect-free setup planning."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent.parent
SAFE_VERSION = re.compile(r"^[\x20-\x7e]{1,160}$")
SAFE_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:+-]{0,255}$")
PROBE_TIMEOUT_SECONDS = 3
MAX_PROBE_BYTES = 65536
INTENTS = {"guided-setup", "existing-setup", "explore"}
SNAPSHOT_EFFECTS = {
    "networkUsed": False, "filesWritten": False, "installationPerformed": False,
    "elevationRequested": False, "servicesChanged": False, "driversChanged": False,
}


class ReadinessError(ValueError):
    pass


def _sanitize_text(value: str, maximum: int = 160) -> str | None:
    line = " ".join(value.replace("\x00", "").split())[:maximum]
    if not line or not SAFE_VERSION.fullmatch(line):
        return None
    if re.search(r"(?i)([A-Z]:\\|/home/|/Users/|\\\\|token=|password=|secret=)", line):
        return None
    return line


class ProbeRunner:
    """Executes only caller-registered executable/argument tuples without a shell."""

    def __init__(self, maximum_scan_seconds: int = 15) -> None:
        self.deadline = time.monotonic() + maximum_scan_seconds

    def run(self, executable: str, arguments: tuple[str, ...], timeout: int = PROBE_TIMEOUT_SECONDS) -> dict[str, Any]:
        resolved = shutil.which(executable)
        if not resolved:
            return {"state": "not-detected", "output": "", "code": None}
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            return {"state": "unknown", "output": "", "code": None}
        timeout = min(timeout, max(0.05, remaining))
        try:
            process = subprocess.Popen(
                [resolved, *arguments],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                env={"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")},
            )
        except OSError:
            return {"state": "unknown", "output": "", "code": None}
        chunks: list[bytes] = []

        def read_bounded() -> None:
            assert process.stdout is not None
            chunks.append(process.stdout.read(MAX_PROBE_BYTES + 1))

        reader = threading.Thread(target=read_bounded, daemon=True)
        reader.start()
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            reader.join(timeout=1)
            return {"state": "unknown", "output": "", "code": None}
        reader.join(timeout=1)
        if reader.is_alive():
            process.kill()
            return {"state": "unknown", "output": "", "code": code}
        output = chunks[0] if chunks else b""
        if len(output) > MAX_PROBE_BYTES:
            return {"state": "unknown", "output": "", "code": code}
        return {
            "state": "detected" if code == 0 else "installed-unverified",
            "output": output.decode("utf-8", errors="replace"),
            "code": code,
        }


def _memory_gib() -> float | None:
    try:
        if os.name == "nt":
            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("length", ctypes.c_ulong),
                    ("memory_load", ctypes.c_ulong),
                    ("total_physical", ctypes.c_ulonglong),
                    ("available_physical", ctypes.c_ulonglong),
                    ("total_page_file", ctypes.c_ulonglong),
                    ("available_page_file", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong),
                    ("available_virtual", ctypes.c_ulonglong),
                    ("available_extended_virtual", ctypes.c_ulonglong),
                ]
            status = MemoryStatus()
            status.length = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return round(status.total_physical / (1024 ** 3), 1)
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
        return round((page_size * pages) / (1024 ** 3), 1)
    except (AttributeError, OSError, ValueError):
        return None


def _software_item(
    runner: ProbeRunner,
    component_id: str,
    executable: str,
    arguments: tuple[str, ...],
) -> dict[str, Any]:
    probe = runner.run(executable, arguments)
    version = None
    if probe["output"]:
        version = _sanitize_text(probe["output"].splitlines()[0])
    return {
        "componentId": component_id,
        "state": probe["state"],
        "version": version,
        "source": "registered-command-probe",
        "confidence": "high" if probe["state"] == "detected" and version else "medium",
    }


def _presence_item(component_id: str, executable: str) -> dict[str, Any]:
    detected = shutil.which(executable) is not None
    return {
        "componentId": component_id,
        "state": "detected" if detected else "not-detected",
        "version": None,
        "source": "executable-presence",
        "confidence": "medium",
    }


def _windows_gpu_items() -> list[dict[str, Any]]:
    try:
        import winreg
    except ImportError:
        return []
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    root_path = r"SYSTEM\CurrentControlSet\Control\Video"
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            root_path,
            0,
            winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0),
        ) as root:
            adapter_index = 0
            while adapter_index < 64:
                try:
                    adapter_key = winreg.EnumKey(root, adapter_index)
                except OSError:
                    break
                adapter_index += 1
                for instance in ("0000", "0001"):
                    try:
                        with winreg.OpenKey(root, f"{adapter_key}\\{instance}") as key:
                            raw_name, _ = winreg.QueryValueEx(key, "DriverDesc")
                            name = _sanitize_text(str(raw_name), 120)
                            if not name or name in seen:
                                continue
                            seen.add(name)
                            try:
                                raw_memory, _ = winreg.QueryValueEx(key, "HardwareInformation.qwMemorySize")
                                if isinstance(raw_memory, bytes):
                                    memory_bytes = int.from_bytes(raw_memory[:8], "little")
                                else:
                                    memory_bytes = int(raw_memory)
                            except (OSError, TypeError, ValueError):
                                try:
                                    raw_memory, _ = winreg.QueryValueEx(key, "HardwareInformation.MemorySize")
                                    legacy_memory = int(raw_memory)
                                    memory_bytes = legacy_memory if legacy_memory < (4 * 1024 ** 3) else 0
                                except (OSError, TypeError, ValueError):
                                    memory_bytes = 0
                            vendor = (
                                "NVIDIA" if re.search("nvidia", name, re.I)
                                else "AMD" if re.search("amd|radeon", name, re.I)
                                else "Intel" if re.search("intel", name, re.I)
                                else "Unknown"
                            )
                            items.append({
                                "vendor": vendor, "model": name,
                                "memoryGiB": round(memory_bytes / (1024 ** 3), 1) if memory_bytes else None,
                                "memoryType": "shared-or-unknown" if vendor == "Intel" else "unknown",
                                "state": "detected", "source": "windows-display-registry",
                                "confidence": "medium",
                            })
                    except OSError:
                        continue
    except OSError:
        return []
    return items


def _gpu_items(runner: ProbeRunner, system: str) -> list[dict[str, Any]]:
    probe = runner.run(
        "nvidia-smi",
        ("--query-gpu=name,memory.total", "--format=csv,noheader,nounits"),
    )
    items: list[dict[str, Any]] = []
    if probe["state"] == "detected":
        for line in probe["output"].splitlines()[:16]:
            match = re.fullmatch(r"\s*([^,\r\n]{1,120})\s*,\s*(\d{1,8})\s*", line)
            if not match:
                continue
            name = _sanitize_text(match.group(1), 120)
            if name:
                items.append({
                    "vendor": "NVIDIA",
                    "model": name,
                    "memoryGiB": round(int(match.group(2)) / 1024, 1),
                    "memoryType": "dedicated",
                    "state": "detected",
                    "source": "nvidia-smi",
                    "confidence": "high",
                })
        return items
    if system == "windows":
        items.extend(_windows_gpu_items())
    elif system == "linux":
        pci = runner.run("lspci", ())
        if pci["state"] == "detected":
            for line in pci["output"].splitlines():
                if not re.search(r"VGA|3D controller|Display controller", line, re.I):
                    continue
                name = _sanitize_text(line.split(":", 2)[-1], 120)
                if name:
                    vendor = (
                        "NVIDIA" if re.search("nvidia", name, re.I)
                        else "AMD" if re.search("amd|ati", name, re.I)
                        else "Intel" if re.search("intel", name, re.I)
                        else "Unknown"
                    )
                    items.append({
                        "vendor": vendor, "model": name, "memoryGiB": None,
                        "memoryType": "unknown", "state": "detected",
                        "source": "lspci", "confidence": "medium",
                    })
    elif system == "macos":
        profiler = runner.run("system_profiler", ("SPDisplaysDataType", "-json"))
        if profiler["state"] == "detected":
            try:
                records = json.loads(profiler["output"]).get("SPDisplaysDataType", [])
                for record in records[:16]:
                    name = _sanitize_text(str(record.get("sppci_model", "")), 120)
                    if name:
                        items.append({
                            "vendor": "Apple" if "apple" in name.lower() else "Unknown",
                            "model": name, "memoryGiB": None, "memoryType": "unified",
                            "state": "detected", "source": "system-profiler", "confidence": "medium",
                        })
            except (json.JSONDecodeError, AttributeError):
                pass
    return items


def inspect_system(runner: ProbeRunner | None = None) -> dict[str, Any]:
    runner = runner or ProbeRunner()
    system = platform.system().lower()
    architecture = platform.machine().lower() or "unknown"
    memory = _memory_gib()
    try:
        storage = round(shutil.disk_usage(ROOT).free / (1024 ** 3), 1)
    except OSError:
        storage = None
    software = [
        {
            "componentId": "python", "state": "validated",
            "version": platform.python_version(), "source": "running-interpreter", "confidence": "high",
        },
        _presence_item("ollama", "ollama"),
        _software_item(runner, "continue", "cn", ("--version",)),
        _software_item(runner, "aider", "aider", ("--version",)),
        _software_item(runner, "opencode", "opencode", ("--version",)),
        _software_item(runner, "nvidia-runtime", "nvidia-smi", ("--version",)),
        _software_item(runner, "amd-runtime", "rocm-smi", ("--version",)),
        _software_item(runner, "intel-runtime", "sycl-ls", ("--version",)),
    ]
    if system == "darwin":
        system = "macos"
    if system != "macos":
        software.append({
            "componentId": "apple-mlx", "state": "unsupported", "version": None,
            "source": "platform-policy", "confidence": "high",
        })
    else:
        mlx = runner.run(sys.executable, ("-c", "import mlx; print('mlx-present')"))
        software.append({
            "componentId": "apple-mlx", "state": mlx["state"], "version": None,
            "source": "registered-python-module-probe", "confidence": "high",
        })
    software.append({
        "componentId": "comfyui", "state": "unknown", "version": None,
        "source": "no-path-discovery-authority", "confidence": "low",
    })
    snapshot = {
        "schemaVersion": 1,
        "kind": "system-readiness",
        "snapshotId": secrets.token_urlsafe(18),
        "platform": {
            "operatingSystem": system,
            "architecture": architecture,
            "logicalProcessors": os.cpu_count(),
            "systemMemoryGiB": memory,
            "availableStorageGiB": storage,
        },
        "accelerators": _gpu_items(runner, system),
        "software": software,
        "installedModels": [],
        "warnings": [],
        "effects": dict(SNAPSHOT_EFFECTS),
        "privacy": {
            "persisted": False, "rawProbeOutputReturned": False,
            "hostIdentityIncluded": False, "privatePathsIncluded": False,
        },
    }
    if not snapshot["accelerators"]:
        snapshot["warnings"].append("accelerator-not-detected-or-permission-limited")
    elif any(item["memoryGiB"] is None for item in snapshot["accelerators"]):
        snapshot["warnings"].append("accelerator-memory-unknown")
    snapshot["warnings"].append("installed-model-discovery-requires-explicit-provider-connection")
    return snapshot


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    required = {
        "schemaVersion", "kind", "snapshotId", "platform", "accelerators",
        "software", "installedModels", "warnings", "effects", "privacy",
    }
    if (
        not isinstance(snapshot, dict) or set(snapshot) != required
        or snapshot.get("schemaVersion") != 1
        or snapshot.get("kind") != "system-readiness"
        or not isinstance(snapshot.get("snapshotId"), str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{16,80}", snapshot["snapshotId"])
        or snapshot.get("effects") != SNAPSHOT_EFFECTS
        or not isinstance(snapshot.get("platform"), dict)
        or not isinstance(snapshot.get("accelerators"), list)
        or not isinstance(snapshot.get("software"), list)
        or not isinstance(snapshot.get("installedModels"), list)
        or not isinstance(snapshot.get("warnings"), list)
    ):
        raise ReadinessError("invalid-readiness-snapshot")
    if any(not isinstance(item, str) or not SAFE_MODEL.fullmatch(item) for item in snapshot["installedModels"]):
        raise ReadinessError("invalid-readiness-snapshot")


def load_component_registry(path: Path | None = None) -> dict[str, dict[str, Any]]:
    value = json.loads((path or ROOT / "config/install-component-registry.json").read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or set(value) != {"schemaVersion", "registryId", "defaultDecision", "rendererMayAddComponents", "components"}
        or value["schemaVersion"] != 1
        or value["registryId"] != "haven42.install-components"
        or value["rendererMayAddComponents"] is not False
        or not isinstance(value["components"], list)
    ):
        raise ReadinessError("invalid-component-registry")
    result: dict[str, dict[str, Any]] = {}
    required = {
        "id", "label", "category", "detectionProbeId", "promotionStatus",
        "managedInstallationAllowed", "missingGate",
    }
    for item in value["components"]:
        if (
            not isinstance(item, dict) or set(item) != required
            or not isinstance(item["id"], str) or item["id"] in result
            or item["managedInstallationAllowed"] is not False
        ):
            raise ReadinessError("invalid-component-registry-entry")
        result[item["id"]] = item
    return result


def _hardware_assessment(snapshot: dict[str, Any]) -> dict[str, Any]:
    memory = snapshot["platform"].get("systemMemoryGiB")
    accelerator_memory = [
        item.get("memoryGiB")
        for item in snapshot["accelerators"]
        if isinstance(item, dict) and isinstance(item.get("memoryGiB"), (int, float))
    ]
    maximum_accelerator_memory = max(accelerator_memory, default=None)
    enough_for_baseline = (
        maximum_accelerator_memory is not None and maximum_accelerator_memory >= 8
    ) or (
        isinstance(memory, (int, float)) and memory >= 16
    )
    return {
        "appliesWhenProviderRunsOnScannedDevice": True,
        "fitDecision": "candidate-only" if enough_for_baseline else "no-safe-recommendation",
        "candidateModel": "qwen3.5:9b" if enough_for_baseline else None,
        "confidence": "low",
        "reason": (
            "Coarse capacity supports evaluating the evidence-gated text baseline; exact runtime fit is still required."
            if enough_for_baseline
            else "Known capacity is insufficient or incomplete; do not select a model automatically."
        ),
        "evidencePromoted": False,
        "downloadAllowed": False,
    }


def build_setup_plan(snapshot: dict[str, Any], intent: str, registry: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    if intent not in INTENTS:
        raise ReadinessError("invalid-setup-intent")
    validate_snapshot(snapshot)
    registry = registry or load_component_registry()
    hardware_assessment = _hardware_assessment(snapshot)
    software = {item["componentId"]: item for item in snapshot.get("software", []) if isinstance(item, dict)}
    actions: list[dict[str, Any]] = []

    def add(component_id: str, reason: str, required: bool) -> None:
        component = registry[component_id]
        detected = software.get(component_id, {}).get("state") in {"detected", "validated"}
        actions.append({
            "componentId": component_id,
            "reason": reason,
            "state": "already-available" if detected else "required" if required else "optional",
            "required": required,
            "promotionStatus": component["promotionStatus"],
            "installControl": "disabled",
            "missingGate": component["missingGate"],
        })

    if intent == "guided-setup":
        add("python", "Runs the current local browser service.", True)
        add("ollama", "Provides local chat, writing, and summarization.", True)
        has_recommended = "qwen3.5:9b" in snapshot.get("installedModels", [])
        if not has_recommended and hardware_assessment["candidateModel"] == "qwen3.5:9b":
            component = registry["ollama-model-qwen35-9b"]
            actions.append({
                "componentId": component["id"],
                "reason": "Current evidence-gated baseline for the three admitted text capabilities.",
                "state": "required",
                "required": True,
                "promotionStatus": component["promotionStatus"],
                "installControl": "disabled",
                "missingGate": component["missingGate"],
            })
        summary = "Review the detected system and the disabled installation plan before connecting a provider."
    elif intent == "existing-setup":
        summary = "Connect a user-managed local or trusted-LAN provider without changing its installation."
    else:
        summary = "Explore Haven 42 without configuring a provider or changing this computer."
    return {
        "schemaVersion": 1,
        "kind": "setup-plan",
        "snapshotId": snapshot["snapshotId"],
        "intent": intent,
        "summary": summary,
        "hardwareAssessment": hardware_assessment,
        "actions": actions,
        "effects": {
            "networkUsed": False, "downloadsPerformed": False, "filesWritten": False,
            "installationPerformed": False, "elevationRequested": False,
            "servicesChanged": False, "driversChanged": False,
        },
        "installationAllowed": False,
    }


def simulate_install_request(request: dict[str, Any], registry: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    required = {"schemaVersion", "componentId", "platformProfileId", "approvalToken"}
    if not isinstance(request, dict) or set(request) != required or request.get("schemaVersion") != 1:
        raise ReadinessError("invalid-install-request-shape")
    registry = registry or load_component_registry()
    component_id = request.get("componentId")
    if component_id not in registry:
        raise ReadinessError("unknown-install-component")
    if not isinstance(request.get("platformProfileId"), str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,79}", request["platformProfileId"]):
        raise ReadinessError("invalid-platform-profile")
    if request.get("approvalToken") is not None:
        raise ReadinessError("simulation-does-not-accept-approval")
    return {
        "schemaVersion": 1,
        "kind": "installation-simulation",
        "status": "not-admitted",
        "componentId": component_id,
        "events": [
            {"sequence": 1, "type": "accepted", "code": "SIMULATION_ACCEPTED"},
            {"sequence": 2, "type": "planning", "code": "COMPONENT_POLICY_EVALUATED"},
            {"sequence": 3, "type": "failed", "code": "REAL_INSTALL_NOT_ADMITTED"},
        ],
        "missingGate": registry[component_id]["missingGate"],
        "effects": {
            "networkUsed": False, "filesWritten": False, "installationPerformed": False,
            "elevationRequested": False, "servicesChanged": False, "driversChanged": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect sanitized readiness or produce an effect-free setup plan.")
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--plan-intent", choices=sorted(INTENTS))
    args = parser.parse_args()
    snapshot = inspect_system()
    value = build_setup_plan(snapshot, args.plan_intent) if args.plan_intent else snapshot
    print(json.dumps(value, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
