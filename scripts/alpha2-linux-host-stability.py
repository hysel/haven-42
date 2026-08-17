#!/usr/bin/env python3
"""Run a bounded CPU smoke and emit sanitized current-boot stability evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import platform
import re
import subprocess
import time
from typing import Any


MAX_JOURNAL_BYTES = 8 * 1024 * 1024
SAFE_OS = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._()+/-]{0,99}")
INCIDENT_PATTERNS = {
    "machineCheck": re.compile(
        r"(?:\bmce:\s*(?!in-kernel)[^\n]*(?:hardware error|machine check events logged|uncorrected|fatal)"
        r"|\bmachine check exception\b|\bhardware error\b)",
        re.IGNORECASE,
    ),
    "uncorrectedMemory": re.compile(
        r"\b(edac|ecc)\b.*\b(uncorrected|uncorrectable|fatal)\b", re.IGNORECASE
    ),
    "gpuReset": re.compile(
        r"\bamdgpu\b.*\b(gpu reset|ring [^\n]*timeout|asic reset|fatal error)\b",
        re.IGNORECASE,
    ),
    "cpuLockup": re.compile(r"\b(watchdog|rcu)\b.*\b(lockup|stall)\b", re.IGNORECASE),
    "criticalThermal": re.compile(
        r"\b(thermal|temperature)\b.*\b(critical|shutdown)\b", re.IGNORECASE
    ),
    "fatalPcie": re.compile(
        r"\b(pcie|aer)\b.*\b(uncorrected|uncorrectable|fatal)\b", re.IGNORECASE
    ),
}


class StabilityError(ValueError):
    """The host stability cell could not be completed or verified."""


def _read_text(path: Path, limit: int) -> str:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
            raise StabilityError("unsafe-system-input")
        return path.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError) as error:
        raise StabilityError("unreadable-system-input") from error


def _os_release(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _read_text(path, 64 * 1024).splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    selected = {"id": values.get("ID", ""), "versionId": values.get("VERSION_ID", "")}
    if any(not SAFE_OS.fullmatch(value) for value in selected.values()):
        raise StabilityError("unsafe-os-identity")
    return selected


def _kernel_journal(executable: str) -> str:
    if not os.path.isabs(executable):
        raise StabilityError("journalctl-unavailable")
    try:
        completed = subprocess.run(
            [executable, "-k", "-b", "--no-pager", "--no-hostname", "-o", "cat"],
            capture_output=True,
            check=False,
            timeout=30,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise StabilityError("kernel-journal-unavailable") from error
    encoded = completed.stdout.encode("utf-8")
    if completed.returncode != 0 or not encoded or len(encoded) > MAX_JOURNAL_BYTES:
        raise StabilityError("kernel-journal-unavailable")
    return completed.stdout


def _incident_counts(text: str) -> dict[str, int]:
    return {name: len(pattern.findall(text)) for name, pattern in INCIDENT_PATTERNS.items()}


def _cpu_worker(seconds: int, worker: int) -> int:
    deadline = time.monotonic() + seconds
    seed = hashlib.sha256(f"haven42-stability-{worker}".encode("ascii")).digest()
    rounds = 0
    while time.monotonic() < deadline:
        seed = hashlib.pbkdf2_hmac("sha256", seed, b"haven42-bounded-smoke", 4096)
        rounds += 1
    return rounds


def _run_cpu_smoke(seconds: int, workers: int) -> int:
    try:
        with multiprocessing.Pool(processes=workers) as pool:
            rounds = pool.starmap(_cpu_worker, [(seconds, index) for index in range(workers)])
    except (OSError, RuntimeError) as error:
        raise StabilityError("cpu-smoke-failed") from error
    total = sum(rounds)
    if total <= 0:
        raise StabilityError("cpu-smoke-failed")
    return total


def build_evidence(
    duration_seconds: int,
    workers: int,
    *,
    journalctl: str,
    boot_id_path: Path = Path("/proc/sys/kernel/random/boot_id"),
    uptime_path: Path = Path("/proc/uptime"),
    os_release_path: Path = Path("/usr/lib/os-release"),
) -> dict[str, Any]:
    if not 30 <= duration_seconds <= 3600 or not 1 <= workers <= 64:
        raise StabilityError("unsafe-smoke-envelope")
    boot_before = _read_text(boot_id_path, 128)
    if not re.fullmatch(r"[0-9a-f-]{36}", boot_before):
        raise StabilityError("boot-identity-unverified")
    uptime_before = int(float(_read_text(uptime_path, 128).split()[0]))
    journal_before = _kernel_journal(journalctl)
    incidents_before = _incident_counts(journal_before)
    started = time.monotonic()
    rounds = _run_cpu_smoke(duration_seconds, workers)
    elapsed = int(time.monotonic() - started)
    boot_after = _read_text(boot_id_path, 128)
    uptime_after = int(float(_read_text(uptime_path, 128).split()[0]))
    incidents_after = _incident_counts(_kernel_journal(journalctl))
    if boot_before != boot_after or uptime_after < uptime_before:
        raise StabilityError("boot-changed-during-smoke")
    new_incidents = {
        name: max(0, incidents_after[name] - incidents_before[name])
        for name in INCIDENT_PATTERNS
    }
    outcome = "passed" if not any(incidents_after.values()) else "failed"
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "alpha2-linux-host-stability-evidence",
        "observedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "outcome": outcome,
        "operatingSystem": _os_release(os_release_path),
        "kernelRelease": platform.release(),
        "smoke": {
            "requestedDurationSeconds": duration_seconds,
            "observedDurationSeconds": elapsed,
            "workerCount": workers,
            "completedWorkUnits": rounds,
        },
        "uptimeSecondsBefore": uptime_before,
        "uptimeSecondsAfter": uptime_after,
        "currentBootKernelIncidentCounts": incidents_after,
        "newKernelIncidentCounts": new_incidents,
        "containsRawKernelLogs": False,
        "containsPrivateMachineIdentity": False,
        "containsNetworkIdentity": False,
        "containsHardwareSerialsOrUuids": False,
        "automaticSupportChangeAllowed": False,
    }
    if outcome != "passed":
        result["errorCode"] = "current-boot-kernel-hardware-incident"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-seconds", type=int, default=600)
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument("--journalctl", default="/usr/bin/journalctl")
    args = parser.parse_args()
    try:
        result = build_evidence(
            args.duration_seconds, args.workers, journalctl=args.journalctl
        )
    except (StabilityError, ValueError, IndexError) as error:
        print(json.dumps({
            "schemaVersion": 1,
            "kind": "alpha2-linux-host-stability-evidence",
            "outcome": "failed",
            "errorCode": str(error),
            "containsRawKernelLogs": False,
            "containsPrivateMachineIdentity": False,
            "automaticSupportChangeAllowed": False,
        }, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["outcome"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
