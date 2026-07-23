#!/usr/bin/env python3
"""Sanitized hardware profiling and dry-run quantization planning."""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from provider_security import ProviderSecurityError, write_new_file


HEX64 = re.compile(r"^[0-9a-f]{64}$")
FULL_SHA = re.compile(r"^[0-9a-f]{40,64}$")
LANES = ("general-chat", "summarization", "tool-use", "engineering-read", "engineering-write")


def command_output(arguments: list[str], timeout: int = 8) -> str:
    if not shutil.which(arguments[0]):
        return ""
    try:
        result = subprocess.run(
            arguments,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return (result.stdout or result.stderr).strip()


def normalize_architecture(value: str) -> str:
    normalized = value.lower()
    return {
        "amd64": "x64",
        "x86_64": "x64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "i386": "x86",
        "i686": "x86",
    }.get(normalized, normalized or "unknown")


def platform_name() -> str:
    return {"Windows": "windows", "Linux": "linux", "Darwin": "macos"}.get(platform.system(), "unknown")


def system_memory_gb() -> float | None:
    if platform.system() == "Windows":
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
            return round(status.total_physical / 1024**3, 1)
        return None

    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
        return round(page_size * pages / 1024**3, 1)
    except (AttributeError, OSError, ValueError):
        if platform.system() == "Darwin":
            value = command_output(["sysctl", "-n", "hw.memsize"])
            return round(int(value) / 1024**3, 1) if value.isdigit() else None
        return None


def cpu_features() -> list[str]:
    system = platform.system()
    text = ""
    if system == "Linux":
        text = command_output(["lscpu"])
    elif system == "Darwin":
        text = " ".join(
            filter(
                None,
                [
                    command_output(["sysctl", "-n", "machdep.cpu.features"]),
                    command_output(["sysctl", "-n", "machdep.cpu.leaf7_features"]),
                ],
            )
        )
    elif system == "Windows":
        text = command_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)",
            ]
        )

    lowered = text.lower()
    recognized = [name for name in ("avx512", "avx2", "avx", "fma", "sse4_2", "neon") if name in lowered]
    architecture = normalize_architecture(platform.machine())
    if architecture == "arm64" and "neon" not in recognized:
        recognized.append("neon-or-equivalent-arm64")
    return sorted(set(recognized)) or ["unknown"]


def detect_nvidia() -> list[dict[str, Any]]:
    rows = command_output(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ]
    )
    results: list[dict[str, Any]] = []
    for row in rows.splitlines():
        parts = [part.strip() for part in row.split(",")]
        if len(parts) != 3:
            continue
        try:
            usable = round(float(parts[1]) / 1024, 1)
        except ValueError:
            usable = None
        results.append(
            {
                "vendor": "nvidia",
                "model": parts[0],
                "memoryType": "dedicated",
                "usableMemoryGb": usable,
                "runtime": "cuda",
                "runtimeVersion": "unknown",
                "driverVersion": parts[2],
                "source": "nvidia-smi",
            }
        )
    return results


def detect_platform_accelerators() -> list[dict[str, Any]]:
    system = platform.system()
    results: list[dict[str, Any]] = []
    if system == "Windows":
        raw = command_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,AdapterRAM | ConvertTo-Json -Compress",
            ]
        )
        try:
            records = json.loads(raw) if raw else []
            if isinstance(records, dict):
                records = [records]
            for record in records:
                name = str(record.get("Name") or "unknown")
                lowered = name.lower()
                vendor = "nvidia" if "nvidia" in lowered else "intel" if "intel" in lowered else "amd" if any(value in lowered for value in ("amd", "radeon")) else "unknown"
                memory = record.get("AdapterRAM")
                results.append(
                    {
                        "vendor": vendor,
                        "model": name,
                        "memoryType": "shared-or-integrated" if vendor == "intel" else "dedicated",
                        "usableMemoryGb": round(float(memory) / 1024**3, 1) if memory else None,
                        "runtime": "xpu" if vendor == "intel" else "rocm" if vendor == "amd" else "cuda" if vendor == "nvidia" else "unknown",
                        "runtimeVersion": "unknown",
                        "driverVersion": str(record.get("DriverVersion") or "unknown"),
                        "source": "Win32_VideoController",
                    }
                )
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
    elif system == "Linux":
        for row in command_output(["lspci"]).splitlines():
            if not re.search(r"VGA|3D controller|Display controller", row, re.IGNORECASE):
                continue
            lowered = row.lower()
            vendor = "nvidia" if "nvidia" in lowered else "intel" if "intel" in lowered else "amd" if any(value in lowered for value in ("amd", "radeon")) else "unknown"
            results.append(
                {
                    "vendor": vendor,
                    "model": re.sub(r"^[^ ]+\s+", "", row),
                    "memoryType": "shared-or-integrated" if vendor == "intel" else "unknown",
                    "usableMemoryGb": None,
                    "runtime": "unknown",
                    "runtimeVersion": "unknown",
                    "driverVersion": "unknown",
                    "source": "lspci",
                }
            )
    elif system == "Darwin":
        raw = command_output(["system_profiler", "SPDisplaysDataType", "-json"], timeout=15)
        try:
            records = json.loads(raw).get("SPDisplaysDataType", []) if raw else []
            for record in records:
                name = str(record.get("sppci_model") or record.get("_name") or "Apple GPU")
                results.append(
                    {
                        "vendor": "apple" if normalize_architecture(platform.machine()) == "arm64" else "unknown",
                        "model": name,
                        "memoryType": "unified" if normalize_architecture(platform.machine()) == "arm64" else "unknown",
                        "usableMemoryGb": system_memory_gb() if normalize_architecture(platform.machine()) == "arm64" else None,
                        "runtime": "mps" if normalize_architecture(platform.machine()) == "arm64" else "unknown",
                        "runtimeVersion": platform.mac_ver()[0] or "unknown",
                        "driverVersion": "operating-system-managed",
                        "source": "system_profiler",
                    }
                )
        except (TypeError, json.JSONDecodeError):
            pass
    return results


def accelerators() -> list[dict[str, Any]]:
    detected = detect_nvidia() + detect_platform_accelerators()
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in detected:
        key = (item["vendor"], item["model"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def runtime_versions() -> list[dict[str, str]]:
    candidates = {
        "ollama": ["ollama", "--version"],
        "llama.cpp": ["llama-cli", "--version"],
        "mlx-lm": ["mlx_lm.generate", "--version"],
        "nvidia": ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
        "intel-xpu": ["xpu-smi", "version"],
        "rocm": ["rocm-smi", "--version"],
    }
    results = []
    for name, command in candidates.items():
        output = command_output(command)
        if output:
            first_line = output.splitlines()[0].strip()[:200]
            results.append({"runtime": name, "version": first_line})
    return results


def build_profile(args: argparse.Namespace) -> dict[str, Any]:
    storage = Path(args.storage_root).expanduser().resolve()
    storage_probe = storage if storage.exists() else storage.parent
    free_gb = round(shutil.disk_usage(storage_probe).free / 1024**3, 1)
    return {
        "schemaVersion": 1,
        "generatedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "platform": platform_name(),
        "architecture": normalize_architecture(platform.machine()),
        "systemMemoryGb": system_memory_gb(),
        "storageHeadroomGb": free_gb,
        "cpuInstructionSupport": cpu_features(),
        "accelerators": accelerators(),
        "runtimes": runtime_versions(),
        "target": {
            "contextTokens": args.context_tokens,
            "concurrency": args.concurrency,
            "workloadLane": args.workload_lane,
        },
        "privacy": {
            "localOnlyHardwareValuesIncluded": True,
            "persistentIdentityValuesIncluded": False,
            "omitted": ["hostname", "ipAddress", "username", "serialNumber", "endpoint", "localPath"],
        },
    }


def load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def numeric(value: Any, default: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def candidate_platform_keys(hardware: dict[str, Any]) -> set[str]:
    base = f"{hardware.get('platform', 'unknown')}-{hardware.get('architecture', 'unknown')}"
    keys = {base}
    for accelerator in hardware.get("accelerators", []):
        vendor = accelerator.get("vendor")
        if vendor:
            keys.add(f"{base}-{vendor}")
    return keys


def max_usable_memory(hardware: dict[str, Any]) -> float:
    values = [
        float(item["usableMemoryGb"])
        for item in hardware.get("accelerators", [])
        if item.get("usableMemoryGb") is not None
    ]
    return max(values, default=float(hardware.get("systemMemoryGb") or 0))


def artifact_matches(artifact: dict[str, Any], request: dict[str, Any]) -> tuple[bool, str]:
    source = request["source"]
    target = request["target"]
    hardware = request["hardwareProfile"]
    if artifact.get("trusted") is not True:
        return False, "artifact is not explicitly trusted"
    if not HEX64.fullmatch(str(artifact.get("sha256", ""))) or numeric(artifact.get("sizeBytes")) <= 0:
        return False, "artifact checksum or size is invalid"
    if not artifact.get("license"):
        return False, "artifact license is missing"
    if artifact.get("sourceRevision") != source.get("revision") or artifact.get("sourceSha256") != source.get("sha256"):
        return False, "source identity differs"
    if artifact.get("format") != target.get("format") or artifact.get("runtime") != target.get("runtime"):
        return False, "format or runtime differs"
    compatibility = artifact.get("compatibility", {})
    if hardware.get("platform") not in compatibility.get("operatingSystems", []):
        return False, "operating system differs"
    if hardware.get("architecture") not in compatibility.get("architectures", []):
        return False, "architecture differs"
    vendors = {item.get("vendor") for item in hardware.get("accelerators", [])}
    required_vendors = set(compatibility.get("acceleratorVendors", []))
    if required_vendors and not vendors.intersection(required_vendors):
        return False, "accelerator differs"
    if max_usable_memory(hardware) < numeric(compatibility.get("minimumUsableMemoryGb")):
        return False, "usable memory is below the artifact requirement"
    if numeric(target.get("contextTokens")) > numeric(compatibility.get("maximumContextTokens")):
        return False, "context target exceeds validated scope"
    return True, "exact trusted artifact match"


def create_plan(request: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    source = request.get("source", {})
    target = request.get("target", {})
    hardware = request.get("hardwareProfile", {})
    reasons: list[str] = []

    if not FULL_SHA.fullmatch(str(source.get("revision", ""))):
        reasons.append("source revision is not immutable")
    if not source.get("repository"):
        reasons.append("source repository is missing")
    if not HEX64.fullmatch(str(source.get("sha256", ""))):
        reasons.append("source SHA-256 is missing or invalid")
    if not source.get("license"):
        reasons.append("source license is missing")
    if target.get("workloadLane") not in LANES:
        reasons.append("workload lane is unsupported")
    if not target.get("format") or not target.get("runtime"):
        reasons.append("target format or runtime is missing")
    if numeric(target.get("contextTokens")) < 1024 or numeric(target.get("concurrency")) < 1:
        reasons.append("target context or concurrency is invalid")
    if reasons:
        mode = "no-safe-recommendation"
        selected = None
    else:
        matching = []
        for artifact in request.get("trustedArtifacts", []):
            matches, reason = artifact_matches(artifact, request)
            if matches:
                matching.append(artifact)
            else:
                reasons.append(f"Rejected {artifact.get('artifactId', 'unnamed')}: {reason}.")
        if matching:
            selected = sorted(matching, key=lambda item: numeric(item.get("sizeBytes"), sys.maxsize))[0]
            mode = "existing-artifact"
            reasons.append("Selected the smallest exact trusted compatible artifact; local conversion is unnecessary.")
        else:
            selected = None
            keys = candidate_platform_keys(hardware)
            supported = any(
                item.get("format") == target.get("format")
                and target.get("runtime") in item.get("runtimes", [])
                and keys.intersection(item.get("candidatePlatforms", []))
                for item in matrix.get("formats", [])
            )
            derivative_allowed = source.get("derivativeAllowed") is True
            storage_needed = numeric(request.get("storageEstimate", {}).get("requiredHeadroomGb"))
            storage_available = numeric(hardware.get("storageHeadroomGb"))
            if request.get("considerLocalDerivative") is True and supported and derivative_allowed and storage_available >= storage_needed:
                mode = "local-derivative"
                reasons.append("No exact trusted artifact matched; a local derivative may be planned after explicit approval and pinned-tool validation.")
            else:
                mode = "no-safe-recommendation"
                if not supported:
                    reasons.append("The requested format/runtime/platform combination is not in the candidate support matrix.")
                if not derivative_allowed:
                    reasons.append("Derivative creation is not affirmatively permitted by the recorded license decision.")
                if storage_available < storage_needed:
                    reasons.append("Available storage is below the required conversion headroom.")
                if request.get("considerLocalDerivative") is not True:
                    reasons.append("Local derivative planning was not explicitly requested.")

    return {
        "schemaVersion": 1,
        "planId": request.get("planId", "local-dry-run"),
        "createdAtUtc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": mode,
        "source": source,
        "target": target,
        "hardwareProfile": hardware,
        "runtimeCompatibility": {"decision": "candidate-only" if mode == "local-derivative" else "exact-match" if mode == "existing-artifact" else "blocked"},
        "storageEstimate": request.get("storageEstimate", {}),
        "licenseDecision": {"license": source.get("license"), "derivativeAllowed": source.get("derivativeAllowed")},
        "disclosures": request.get("disclosures", []),
        "decision": {"selectedArtifact": selected, "reasons": reasons},
        "effects": {"network": False, "downloads": False, "writes": False, "conversion": False, "activation": False},
    }


def self_test() -> None:
    source = {"repository": "example/model", "revision": "a" * 40, "sha256": "b" * 64, "license": "Apache-2.0", "derivativeAllowed": True}
    hardware = {"platform": "linux", "architecture": "x64", "systemMemoryGb": 64, "storageHeadroomGb": 200, "accelerators": [{"vendor": "nvidia", "usableMemoryGb": 24}]}
    target = {"format": "gguf", "runtime": "ollama", "contextTokens": 16384, "concurrency": 1, "workloadLane": "tool-use"}
    artifact = {"artifactId": "trusted", "trusted": True, "sourceRevision": "a" * 40, "sourceSha256": "b" * 64, "format": "gguf", "runtime": "ollama", "sha256": "c" * 64, "sizeBytes": 10, "license": "Apache-2.0", "compatibility": {"operatingSystems": ["linux"], "architectures": ["x64"], "acceleratorVendors": ["nvidia"], "minimumUsableMemoryGb": 16, "maximumContextTokens": 32768}}
    matrix = {"formats": [{"format": "gguf", "runtimes": ["ollama"], "candidatePlatforms": ["linux-x64-nvidia"]}]}
    base = {"planId": "test", "source": source, "target": target, "hardwareProfile": hardware, "storageEstimate": {"requiredHeadroomGb": 50}, "disclosures": []}
    assert create_plan({**base, "trustedArtifacts": [artifact]}, matrix)["mode"] == "existing-artifact"
    assert create_plan({**base, "trustedArtifacts": [], "considerLocalDerivative": True}, matrix)["mode"] == "local-derivative"
    blocked = {**base, "source": {**source, "derivativeAllowed": False}, "trustedArtifacts": [], "considerLocalDerivative": True}
    assert create_plan(blocked, matrix)["mode"] == "no-safe-recommendation"
    print("PASS quantization planner self-test (3 cases)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    profile_parser = subparsers.add_parser("profile", help="Emit a sanitized local hardware profile as JSON.")
    profile_parser.add_argument("--storage-root", default=str(Path.home()))
    profile_parser.add_argument("--context-tokens", type=int, default=16384)
    profile_parser.add_argument("--concurrency", type=int, default=1)
    profile_parser.add_argument("--workload-lane", choices=LANES, default="tool-use")
    plan_parser = subparsers.add_parser("plan", help="Evaluate a local dry-run request without downloads or writes.")
    plan_parser.add_argument("--request", required=True)
    plan_parser.add_argument("--output", required=True, help="New local JSON file; existing files are never overwritten.")
    plan_parser.add_argument(
        "--support-matrix",
        default=str(Path(__file__).resolve().parent.parent / "config" / "quantization-support-matrix.json"),
    )
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.command == "profile":
        if args.context_tokens < 1024 or args.concurrency < 1:
            parser.error("context tokens must be at least 1024 and concurrency must be positive")
        print(json.dumps(build_profile(args), indent=2))
        return 0
    if args.command == "plan":
        output_path = Path(args.output).absolute()
        if output_path.suffix.lower() != ".json" or output_path.parent.is_symlink():
            parser.error("output must be a JSON file in a non-symlink directory")
        try:
            payload = (json.dumps(create_plan(load_json(args.request), load_json(args.support_matrix)), indent=2) + "\n").encode("utf-8")
            write_new_file(output_path, payload)
        except (OSError, ProviderSecurityError) as error:
            parser.error(f"secure plan write failed: {error}")
        print("Quantization plan written securely.")
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
