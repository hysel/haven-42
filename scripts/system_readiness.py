#!/usr/bin/env python3
"""Read-only, sanitized system readiness and effect-free setup planning."""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import platform
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

from windows_user_paths import WindowsUserPathError, portable_install_root


SOURCE_ROOT = Path(__file__).resolve().parent.parent
ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
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


def _windows_platform_facts() -> dict[str, Any]:
    facts: dict[str, Any] = {
        "productName": None,
        "buildNumber": None,
        "cpuFeatures": [],
        "pendingRestart": None,
    }
    if os.name != "nt":
        return facts
    try:
        version = sys.getwindowsversion()
        facts["buildNumber"] = int(version.build)
        facts["productName"] = "Windows 11" if version.build >= 22000 else "Windows 10"
    except (AttributeError, OSError, ValueError):
        pass
    feature_ids = {"sse2": 10, "sse3": 13, "avx": 39, "avx2": 40}
    for name, feature_id in feature_ids.items():
        try:
            if ctypes.windll.kernel32.IsProcessorFeaturePresent(feature_id):
                facts["cpuFeatures"].append(name)
        except (AttributeError, OSError):
            break
    try:
        import winreg
        checks = (
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending", None),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired", None),
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager", "PendingFileRenameOperations"),
        )
        pending = False
        for hive, key_path, value_name in checks:
            try:
                with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)) as key:
                    if value_name is None:
                        pending = True
                    else:
                        value, _ = winreg.QueryValueEx(key, value_name)
                        pending = bool(value)
            except OSError:
                continue
            if pending:
                break
        facts["pendingRestart"] = pending
    except ImportError:
        pass
    return facts


def _macos_platform_facts(runner: ProbeRunner) -> dict[str, Any]:
    """Return a bounded, non-identifying Mac model description."""
    facts: dict[str, Any] = {"productName": None}
    profiler = runner.run("system_profiler", ("SPHardwareDataType", "-json"))
    if profiler["state"] != "detected":
        return facts
    try:
        records = json.loads(profiler["output"]).get("SPHardwareDataType", [])
    except (json.JSONDecodeError, AttributeError):
        return facts
    if not isinstance(records, list) or not records or not isinstance(records[0], dict):
        return facts
    machine_name = _sanitize_text(str(records[0].get("machine_name", "")), 80)
    chip_type = _sanitize_text(str(records[0].get("chip_type", "")), 80)
    if machine_name and re.fullmatch(r"[A-Za-z0-9 .()+_-]{1,80}", machine_name):
        facts["productName"] = machine_name
        if chip_type and re.fullmatch(r"[A-Za-z0-9 .()+_-]{1,80}", chip_type):
            facts["productName"] = f"{machine_name} ({chip_type})"
    return facts


LINUX_OS_RELEASE_PATHS = {
    Path("/etc/os-release"),
    Path("/usr/lib/os-release"),
    Path("/etc/pop-os/os-release"),
}


def _trusted_linux_os_release_path(requested: Path, resolved: Path) -> bool:
    """Admit only reviewed fixed OS identity files for the live Linux scan."""
    return requested != Path("/etc/os-release") or resolved in LINUX_OS_RELEASE_PATHS


def _read_linux_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    """Read only the fixed operating-system identity file with strict bounds."""
    try:
        resolved = path.resolve(strict=True)
        if not _trusted_linux_os_release_path(path, resolved):
            return {}
        if not resolved.is_file() or resolved.stat().st_size > 64 * 1024:
            return {}
        raw = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {}
    if "\x00" in raw:
        return {}
    values: dict[str, str] = {}
    allowed = {
        "ID", "NAME", "PRETTY_NAME", "VERSION_ID", "VERSION", "BUILD_ID",
    }
    for line in raw.splitlines()[:256]:
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, encoded = line.split("=", 1)
        if key not in allowed:
            continue
        if key in values or len(encoded) > 512:
            return {}
        try:
            parsed = shlex.split(encoded, comments=False, posix=True)
        except ValueError:
            return {}
        if len(parsed) != 1:
            return {}
        sanitized = _sanitize_text(parsed[0], 160)
        if sanitized is None:
            return {}
        values[key] = sanitized
    return values


def _linux_platform_facts(
    os_release_path: Path = Path("/etc/os-release"),
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "distributionId": None,
        "distributionVersion": None,
        "productName": None,
        "kernelVersion": None,
        "libcFamily": None,
        "libcVersion": None,
        "desktopEnvironmentReported": None,
        "sessionTypeReported": None,
        "sessionMetadataTrusted": False,
    }
    if platform.system().lower() != "linux" and os_release_path == Path("/etc/os-release"):
        return facts
    release = _read_linux_os_release(os_release_path)
    distro_id = release.get("ID")
    if distro_id and re.fullmatch(r"[A-Za-z0-9._+-]{1,64}", distro_id):
        facts["distributionId"] = distro_id.casefold()
    version = release.get("VERSION_ID")
    if (
        version is None
        and facts["distributionId"] in {"arch", "cachyos"}
        and release.get("BUILD_ID", "").casefold() == "rolling"
    ):
        version = "rolling"
    facts["distributionVersion"] = version
    facts["productName"] = release.get("PRETTY_NAME") or release.get("NAME")
    facts["kernelVersion"] = _sanitize_text(platform.release(), 96)
    try:
        libc = os.confstr("CS_GNU_LIBC_VERSION")
    except (AttributeError, OSError, ValueError):
        libc = None
    if isinstance(libc, str):
        match = re.fullmatch(r"([A-Za-z0-9._+-]{1,32})\s+([0-9][0-9A-Za-z._+-]{0,31})", libc)
        if match:
            facts["libcFamily"] = match.group(1).casefold()
            facts["libcVersion"] = match.group(2)
    # Only these two non-path session classifications are read. They remain
    # explicitly reported/untrusted metadata and never grant setup authority.
    # All other environment values are ignored.
    source = os.environ if environment is None else environment
    desktop = _sanitize_text(str(source.get("XDG_CURRENT_DESKTOP", "")), 64)
    session = _sanitize_text(str(source.get("XDG_SESSION_TYPE", "")), 32)
    if desktop and re.fullmatch(r"[A-Za-z0-9 ._:+-]{1,64}", desktop):
        facts["desktopEnvironmentReported"] = desktop
    if session and session.casefold() in {"wayland", "x11", "tty", "unspecified"}:
        facts["sessionTypeReported"] = session.casefold()
    return facts


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


def _first_software_item(
    runner: ProbeRunner,
    component_id: str,
    probes: tuple[tuple[str, tuple[str, ...]], ...],
) -> dict[str, Any]:
    """Run only a fixed ordered probe list and return the first verified version."""
    fallback: dict[str, Any] | None = None
    for executable, arguments in probes:
        item = _software_item(runner, component_id, executable, arguments)
        fallback = fallback or item
        if item["state"] == "detected" and item["version"] is not None:
            return item
        if item["state"] == "installed-unverified":
            fallback = item
    return fallback or {
        "componentId": component_id,
        "state": "not-detected",
        "version": None,
        "source": "registered-command-probe",
        "confidence": "medium",
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
                            try:
                                raw_driver, _ = winreg.QueryValueEx(key, "DriverVersion")
                                driver_version = _sanitize_text(str(raw_driver), 64)
                            except OSError:
                                driver_version = None
                            backend = (
                                "cuda-candidate" if vendor == "NVIDIA"
                                else "rocm-or-vulkan-candidate" if vendor == "AMD"
                                else "vulkan-candidate" if vendor == "Intel"
                                else "unknown"
                            )
                            items.append({
                                "vendor": vendor, "model": name,
                                "memoryGiB": round(memory_bytes / (1024 ** 3), 1) if memory_bytes else None,
                                "memoryType": "shared-or-unknown" if vendor == "Intel" else "unknown",
                                "state": "detected", "source": "windows-display-registry",
                                "confidence": "medium", "driverVersion": driver_version,
                                "backendCandidate": backend,
                            })
                    except OSError:
                        continue
    except OSError:
        return []
    return items


def _gpu_items(runner: ProbeRunner, system: str) -> list[dict[str, Any]]:
    probe = runner.run(
        "nvidia-smi",
        ("--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"),
    )
    items: list[dict[str, Any]] = []
    if probe["state"] == "detected":
        for line in probe["output"].splitlines()[:16]:
            match = re.fullmatch(r"\s*([^,\r\n]{1,120})\s*,\s*(\d{1,8})\s*,\s*([0-9.]{1,32})\s*", line)
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
                    "driverName": "nvidia",
                    "driverVersion": match.group(3),
                    "backendCandidate": "cuda-candidate",
                })
        return items
    if system == "windows":
        items.extend(_windows_gpu_items())
    elif system == "linux":
        pci = runner.run("lspci", ("-D", "-k"))
        if pci["state"] == "detected":
            blocks: list[list[str]] = []
            for line in pci["output"].splitlines()[:512]:
                if line and not line[0].isspace():
                    blocks.append([line])
                elif blocks:
                    blocks[-1].append(line)
            allowed_drivers = {"amdgpu", "i915", "xe", "nouveau", "nvidia"}
            for block in blocks[:64]:
                header = block[0]
                if not re.search(r"VGA|3D controller|Display controller", header, re.I):
                    continue
                name = _sanitize_text(header.split(":", 2)[-1], 120)
                if name:
                    vendor = (
                        "NVIDIA" if re.search(r"\bnvidia\b", name, re.I)
                        else "AMD" if re.search(
                            r"\bamd\b|\bati\b|advanced micro devices|\bradeon\b",
                            name,
                            re.I,
                        )
                        else "Intel" if re.search(r"\bintel\b", name, re.I)
                        else "Unknown"
                    )
                    driver_name = None
                    for detail in block[1:]:
                        match = re.fullmatch(r"\s*Kernel driver in use:\s*([A-Za-z0-9_-]{1,32})\s*", detail)
                        if match and match.group(1) in allowed_drivers:
                            driver_name = match.group(1)
                            break
                    driver_version = None
                    if driver_name:
                        module = runner.run("modinfo", ("-F", "version", driver_name))
                        if module["state"] == "detected" and module["output"]:
                            driver_version = _sanitize_text(module["output"].splitlines()[0], 64)
                    backend = (
                        "cuda-candidate" if vendor == "NVIDIA"
                        else "rocm-or-vulkan-candidate" if vendor == "AMD"
                        else "vulkan-candidate" if vendor == "Intel"
                        else "unknown"
                    )
                    items.append({
                        "vendor": vendor, "model": name, "memoryGiB": None,
                        "memoryType": "unknown", "state": "detected",
                        "source": "lspci-kernel-driver",
                        "confidence": "high" if driver_name else "medium",
                        "driverName": driver_name,
                        "driverVersion": driver_version,
                        "backendCandidate": backend,
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
                            "driverName": None,
                            "driverVersion": None, "backendCandidate": "metal-candidate",
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
        storage_root = portable_install_root() if system == "windows" else ROOT
        storage = round(shutil.disk_usage(storage_root).free / (1024 ** 3), 1)
    except (OSError, WindowsUserPathError):
        storage = None
    ollama_item = _software_item(runner, "ollama", "ollama", ("--version",))
    if system == "darwin" and ollama_item["state"] == "not-detected":
        try:
            from macos_installed_ollama import readiness_item

            ollama_item = readiness_item()
        except (ImportError, OSError, ValueError):
            # Readiness remains fail-closed when the fixed app-bundle probe is
            # unavailable or cannot verify its bounded, non-identifying fields.
            pass
    software = [
        {
            "componentId": "python", "state": "validated",
            "version": platform.python_version(), "source": "running-interpreter", "confidence": "high",
        },
        ollama_item,
        _software_item(runner, "continue", "cn", ("--version",)),
        _software_item(runner, "aider", "aider", ("--version",)),
        _software_item(runner, "opencode", "opencode", ("--version",)),
        _software_item(runner, "nvidia-runtime", "nvidia-smi", ("--version",)),
        _first_software_item(runner, "amd-runtime", (
            ("amd-smi", ("version",)),
            ("rocm-smi", ("--version",)),
        )),
        _first_software_item(runner, "intel-runtime", (
            ("xpu-smi", ("version",)),
            ("sycl-ls", ("--version",)),
        )),
    ]
    if system == "darwin":
        system = "macos"
    windows_facts = _windows_platform_facts()
    macos_facts = _macos_platform_facts(runner) if system == "macos" else {
        "productName": None,
    }
    linux_facts = _linux_platform_facts() if system == "linux" else {
        "distributionId": None,
        "distributionVersion": None,
        "productName": None,
        "kernelVersion": None,
        "libcFamily": None,
        "libcVersion": None,
        "desktopEnvironmentReported": None,
        "sessionTypeReported": None,
        "sessionMetadataTrusted": False,
    }
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
            "productName": (
                windows_facts["productName"]
                if system == "windows"
                else macos_facts["productName"]
                if system == "macos"
                else linux_facts["productName"]
            ),
            "buildNumber": windows_facts["buildNumber"],
            "cpuFeatures": windows_facts["cpuFeatures"],
            "pendingRestart": windows_facts["pendingRestart"],
            "distributionId": linux_facts["distributionId"],
            "distributionVersion": linux_facts["distributionVersion"],
            "kernelVersion": linux_facts["kernelVersion"],
            "libcFamily": linux_facts["libcFamily"],
            "libcVersion": linux_facts["libcVersion"],
            "desktopEnvironmentReported": linux_facts["desktopEnvironmentReported"],
            "sessionTypeReported": linux_facts["sessionTypeReported"],
            "sessionMetadataTrusted": linux_facts["sessionMetadataTrusted"],
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
    platform_facts = snapshot["platform"]
    required_platform = {
        "operatingSystem", "architecture", "logicalProcessors",
        "systemMemoryGiB", "availableStorageGiB",
    }
    allowed_platform = required_platform | {
        "productName", "buildNumber", "cpuFeatures", "pendingRestart",
        "distributionId", "distributionVersion", "kernelVersion", "libcFamily",
        "libcVersion", "desktopEnvironmentReported", "sessionTypeReported",
        "sessionMetadataTrusted",
    }
    if not required_platform <= set(platform_facts) or not set(platform_facts) <= allowed_platform:
        raise ReadinessError("invalid-readiness-snapshot")
    if platform_facts.get("operatingSystem") not in {"windows", "linux", "macos"}:
        raise ReadinessError("invalid-readiness-snapshot")
    if not isinstance(platform_facts.get("architecture"), str) or not re.fullmatch(
        r"[A-Za-z0-9._+-]{1,32}", platform_facts["architecture"]
    ):
        raise ReadinessError("invalid-readiness-snapshot")
    logical = platform_facts.get("logicalProcessors")
    if logical is not None and (isinstance(logical, bool) or not isinstance(logical, int) or not 1 <= logical <= 65536):
        raise ReadinessError("invalid-readiness-snapshot")
    for field in ("systemMemoryGiB", "availableStorageGiB"):
        value = platform_facts.get(field)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 or value > 10**9
        ):
            raise ReadinessError("invalid-readiness-snapshot")
    optional_text_limits = {
        "productName": 160, "distributionId": 64, "distributionVersion": 64,
        "kernelVersion": 96, "libcFamily": 32, "libcVersion": 32,
        "desktopEnvironmentReported": 64, "sessionTypeReported": 32,
    }
    for field, maximum in optional_text_limits.items():
        value = platform_facts.get(field)
        if value is not None and (
            not isinstance(value, str) or _sanitize_text(value, maximum) != value
        ):
            raise ReadinessError("invalid-readiness-snapshot")
    if platform_facts.get("buildNumber") is not None and (
        isinstance(platform_facts["buildNumber"], bool)
        or not isinstance(platform_facts["buildNumber"], int)
        or not 0 <= platform_facts["buildNumber"] <= 10**9
    ):
        raise ReadinessError("invalid-readiness-snapshot")
    cpu_features = platform_facts.get("cpuFeatures", [])
    if not isinstance(cpu_features, list) or any(
        not isinstance(item, str) or not re.fullmatch(r"[a-z0-9._+-]{1,32}", item)
        for item in cpu_features
    ):
        raise ReadinessError("invalid-readiness-snapshot")
    pending_restart = platform_facts.get("pendingRestart")
    if pending_restart is not None and type(pending_restart) is not bool:
        raise ReadinessError("invalid-readiness-snapshot")
    if platform_facts.get("sessionMetadataTrusted", False) is not False:
        raise ReadinessError("invalid-readiness-snapshot")

    required_accelerator = {
        "vendor", "model", "memoryGiB", "memoryType", "state", "source", "confidence",
    }
    allowed_accelerator = required_accelerator | {"driverName", "driverVersion", "backendCandidate"}
    for item in snapshot["accelerators"]:
        if not isinstance(item, dict) or not required_accelerator <= set(item) or not set(item) <= allowed_accelerator:
            raise ReadinessError("invalid-readiness-snapshot")
        if item.get("vendor") not in {"NVIDIA", "AMD", "Intel", "Apple", "Unknown"}:
            raise ReadinessError("invalid-readiness-snapshot")
        if not isinstance(item.get("model"), str) or _sanitize_text(item["model"], 120) != item["model"]:
            raise ReadinessError("invalid-readiness-snapshot")
        memory_value = item.get("memoryGiB")
        if memory_value is not None and (
            isinstance(memory_value, bool) or not isinstance(memory_value, (int, float))
            or not math.isfinite(memory_value) or memory_value < 0 or memory_value > 10**6
        ):
            raise ReadinessError("invalid-readiness-snapshot")
        for field in ("memoryType", "state", "source", "confidence", "driverName", "driverVersion", "backendCandidate"):
            value = item.get(field)
            if value is not None and (
                not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9._+-]{1,96}", value)
            ):
                raise ReadinessError("invalid-readiness-snapshot")

    required_software = {"componentId", "state", "version", "source", "confidence"}
    for item in snapshot["software"]:
        if not isinstance(item, dict) or set(item) != required_software:
            raise ReadinessError("invalid-readiness-snapshot")
        for field in ("componentId", "state", "source", "confidence"):
            if not isinstance(item.get(field), str) or not re.fullmatch(r"[A-Za-z0-9._+-]{1,96}", item[field]):
                raise ReadinessError("invalid-readiness-snapshot")
        version = item.get("version")
        if version is not None and (not isinstance(version, str) or _sanitize_text(version, 160) != version):
            raise ReadinessError("invalid-readiness-snapshot")
    if any(not isinstance(item, str) or not re.fullmatch(r"[a-z0-9-]{1,160}", item) for item in snapshot["warnings"]):
        raise ReadinessError("invalid-readiness-snapshot")
    if snapshot.get("privacy") != {
        "persisted": False,
        "rawProbeOutputReturned": False,
        "hostIdentityIncluded": False,
        "privatePathsIncluded": False,
    }:
        raise ReadinessError("invalid-readiness-snapshot")


def load_component_registry(path: Path | None = None) -> dict[str, dict[str, Any]]:
    value = json.loads((path or ROOT / "config/install-component-registry.json").read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or set(value) != {
            "schemaVersion", "registryId", "defaultDecision",
            "rendererMayAddComponents", "artifactRegistry",
            "managedComponentCount", "components",
        }
        or value["schemaVersion"] != 1
        or value["registryId"] != "haven42.install-components"
        or value["rendererMayAddComponents"] is not False
        or value["artifactRegistry"] != "config/install-artifact-registry.json"
        or value["managedComponentCount"] != 0
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
    required = {
        "schemaVersion", "operation", "componentId", "platformProfileId",
        "currentState", "promotionEvidence", "approvalToken",
    }
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
    operation = request.get("operation")
    if operation not in {"plan-install", "plan-upgrade", "plan-uninstall"}:
        raise ReadinessError("invalid-install-operation")
    current_state = request.get("currentState")
    if current_state not in {"absent", "present", "unknown"}:
        raise ReadinessError("invalid-component-current-state")
    if current_state == "unknown":
        raise ReadinessError("unknown-component-state")
    if operation == "plan-install" and current_state != "absent":
        raise ReadinessError("install-requires-absent-state")
    if operation in {"plan-upgrade", "plan-uninstall"} and current_state != "present":
        raise ReadinessError("lifecycle-operation-requires-present-state")
    evidence_fields = {
        "immutableIdentityAvailable", "checksumAvailable",
        "signatureOrAttestationAvailable", "licenseReviewed",
        "platformLifecycleEvidenceAvailable",
    }
    promotion_evidence = request.get("promotionEvidence")
    if (
        not isinstance(promotion_evidence, dict)
        or set(promotion_evidence) != evidence_fields
        or any(type(value) is not bool for value in promotion_evidence.values())
    ):
        raise ReadinessError("invalid-promotion-evidence")
    missing_evidence = sorted(
        field for field, available in promotion_evidence.items() if not available
    )
    return {
        "schemaVersion": 1,
        "kind": "installation-simulation",
        "status": "not-admitted",
        "operation": operation,
        "componentId": component_id,
        "events": [
            {"sequence": 1, "type": "accepted", "code": "SIMULATION_ACCEPTED"},
            {"sequence": 2, "type": "planning", "code": "COMPONENT_POLICY_EVALUATED"},
            {"sequence": 3, "type": "failed", "code": "REAL_INSTALL_NOT_ADMITTED"},
        ],
        "missingGate": registry[component_id]["missingGate"],
        "missingPromotionEvidence": missing_evidence,
        "scenarioEvidenceAcceptedAsAuthority": False,
        "approvalAccepted": False,
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
    # This is an explicit CLI response, not application logging. The readiness
    # schema is sanitized before serialization and is written as bounded JSON.
    encoded = json.dumps(value, indent=2).encode("utf-8")
    sys.stdout.buffer.write(encoded + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
