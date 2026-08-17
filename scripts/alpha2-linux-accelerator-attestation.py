#!/usr/bin/env python3
"""Produce a bounded, sanitized Linux accelerator and Vulkan attestation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = ROOT / "config/alpha-2-rx5700xt-certification-plan.json"
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_COMMAND_BYTES = 2 * 1024 * 1024
SAFE_ID = re.compile(r"0x[0-9a-f]{4}")
SAFE_DRIVER = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")
SAFE_OS = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._()+/-]{0,99}")


class AttestationError(ValueError):
    """The requested accelerator identity could not be proved safely."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            raise AttestationError("unsafe-plan")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AttestationError("invalid-plan") from error
    if not isinstance(value, dict):
        raise AttestationError("invalid-plan")
    return value


def _expected(plan: dict[str, Any]) -> dict[str, Any]:
    hardware = plan.get("hardwareClass")
    if not isinstance(hardware, dict):
        raise AttestationError("invalid-plan")
    required = {
        "vendor", "model", "architecture", "gfxTarget", "pciVendorId",
        "pciDeviceId", "kernelDriver", "vulkanDriver", "memoryGiB",
    }
    if set(hardware) != required:
        raise AttestationError("invalid-plan")
    vendor_id = hardware.get("pciVendorId")
    device_id = hardware.get("pciDeviceId")
    kernel_driver = hardware.get("kernelDriver")
    vulkan_driver = hardware.get("vulkanDriver")
    memory_gib = hardware.get("memoryGiB")
    if (
        not isinstance(vendor_id, str) or not SAFE_ID.fullmatch(vendor_id)
        or not isinstance(device_id, str) or not SAFE_ID.fullmatch(device_id)
        or not isinstance(kernel_driver, str) or not SAFE_DRIVER.fullmatch(kernel_driver)
        or not isinstance(vulkan_driver, str) or not SAFE_DRIVER.fullmatch(vulkan_driver)
        or isinstance(memory_gib, bool) or not isinstance(memory_gib, int)
        or not 1 <= memory_gib <= 256
    ):
        raise AttestationError("invalid-plan")
    for name in ("vendor", "model", "architecture", "gfxTarget"):
        if not isinstance(hardware.get(name), str) or not SAFE_OS.fullmatch(hardware[name]):
            raise AttestationError("invalid-plan")
    return hardware


def _read_text(path: Path, limit: int = 4096) -> str:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
            raise AttestationError("unsafe-sysfs-value")
        return path.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError) as error:
        raise AttestationError("unreadable-sysfs-value") from error


def _driver_name(driver_link: Path) -> str:
    try:
        if not driver_link.is_symlink():
            raise AttestationError("kernel-driver-unverified")
        return driver_link.resolve(strict=True).name
    except OSError as error:
        raise AttestationError("kernel-driver-unverified") from error


def _devices(drm_root: Path, expected: dict[str, Any]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for card in sorted(drm_root.glob("card[0-9]*")):
        device = card / "device"
        if not device.is_dir():
            continue
        try:
            vendor = _read_text(device / "vendor").lower()
            device_id = _read_text(device / "device").lower()
        except AttestationError:
            continue
        if vendor != expected["pciVendorId"] or device_id != expected["pciDeviceId"]:
            continue
        try:
            driver = _driver_name(device / "driver")
            total_vram = int(_read_text(device / "mem_info_vram_total"))
        except (OSError, ValueError) as error:
            raise AttestationError("accelerator-memory-unverified") from error
        if driver != expected["kernelDriver"]:
            raise AttestationError("kernel-driver-mismatch")
        minimum = expected["memoryGiB"] * 1024**3 * 95 // 100
        maximum = expected["memoryGiB"] * 1024**3 * 105 // 100
        if not minimum <= total_vram <= maximum:
            raise AttestationError("accelerator-memory-mismatch")
        matches.append({
            "pciVendorId": vendor,
            "pciDeviceId": device_id,
            "kernelDriver": driver,
            "totalVramBytes": total_vram,
        })
    if len(matches) != 1:
        raise AttestationError("expected-accelerator-not-unique")
    return matches


def _vulkan_summary(executable: str, expected: dict[str, Any]) -> dict[str, str]:
    try:
        completed = subprocess.run(
            [executable, "--summary"], capture_output=True, check=False,
            timeout=30, text=True, encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise AttestationError("vulkan-summary-failed") from error
    raw = completed.stdout
    if completed.returncode != 0 or len(raw.encode("utf-8")) > MAX_COMMAND_BYTES:
        raise AttestationError("vulkan-summary-failed")
    blocks = re.split(r"(?m)^GPU\d+:\s*$", raw)
    matches: list[dict[str, str]] = []
    for block in blocks[1:]:
        values = dict(re.findall(
            r"(?m)^\s*(vendorID|deviceID|deviceName|driverName|driverInfo)\s*=\s*(.+?)\s*$",
            block,
        ))
        if (
            values.get("vendorID", "").lower() == expected["pciVendorId"]
            and values.get("deviceID", "").lower() == expected["pciDeviceId"]
        ):
            matches.append(values)
    if len(matches) != 1:
        raise AttestationError("vulkan-accelerator-not-unique")
    match = matches[0]
    if match.get("driverName") != expected["vulkanDriver"]:
        raise AttestationError("vulkan-driver-mismatch")
    sanitized = {
        "deviceName": match.get("deviceName", ""),
        "driverName": match.get("driverName", ""),
        "driverInfo": match.get("driverInfo", ""),
    }
    if any(not value or len(value) > 160 or "\n" in value for value in sanitized.values()):
        raise AttestationError("unsafe-vulkan-identity")
    return sanitized


def _os_release(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _read_text(path, 64 * 1024).splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    selected = {"id": values.get("ID", ""), "versionId": values.get("VERSION_ID", "")}
    if any(not SAFE_OS.fullmatch(value) for value in selected.values()):
        raise AttestationError("unsafe-os-identity")
    return selected


def build_attestation(
    plan_path: Path = DEFAULT_PLAN,
    drm_root: Path = Path("/sys/class/drm"),
    os_release_path: Path = Path("/usr/lib/os-release"),
    uptime_path: Path = Path("/proc/uptime"),
    vulkaninfo: str | None = None,
) -> dict[str, Any]:
    plan = _load_json(plan_path)
    expected = _expected(plan)
    devices = _devices(drm_root, expected)
    executable = vulkaninfo or shutil.which("vulkaninfo")
    if not executable or not os.path.isabs(executable):
        raise AttestationError("vulkaninfo-unavailable")
    try:
        uptime_seconds = int(float(_read_text(uptime_path, 128).split()[0]))
    except (ValueError, IndexError) as error:
        raise AttestationError("uptime-unverified") from error
    if uptime_seconds < 0:
        raise AttestationError("uptime-unverified")
    return {
        "schemaVersion": 1,
        "kind": "alpha2-linux-accelerator-attestation",
        "observedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "outcome": "passed",
        "containsPrivateMachineIdentity": False,
        "containsNetworkIdentity": False,
        "containsHardwareSerialsOrUuids": False,
        "planId": plan.get("planId"),
        "operatingSystem": _os_release(os_release_path),
        "kernelRelease": platform.release(),
        "uptimeSeconds": uptime_seconds,
        "expectedHardware": {
            "vendor": expected["vendor"],
            "model": expected["model"],
            "architecture": expected["architecture"],
            "gfxTarget": expected["gfxTarget"],
            "memoryGiB": expected["memoryGiB"],
        },
        "device": devices[0],
        "vulkan": _vulkan_summary(executable, expected),
        "automaticSupportChangeAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    args = parser.parse_args()
    try:
        result = build_attestation(args.plan)
    except AttestationError as error:
        print(json.dumps({
            "schemaVersion": 1,
            "kind": "alpha2-linux-accelerator-attestation",
            "outcome": "failed",
            "errorCode": str(error),
            "containsPrivateMachineIdentity": False,
            "automaticSupportChangeAllowed": False,
        }, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
