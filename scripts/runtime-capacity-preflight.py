#!/usr/bin/env python3
"""Make a no-effect, fail-closed capacity decision from sanitized measurements."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"invalid-{label}")
    return float(value)


def evaluate(profile: dict, required_accelerator_mib: int, required_system_mib: int, required_disk_mib: int, reserve_mib: int, max_utilization: int) -> dict:
    required = {"schemaVersion", "platform", "availableSystemMemoryMiB", "availableDiskMiB", "accelerator", "competingWorkloadDetected"}
    if not isinstance(profile, dict) or set(profile) != required or profile["schemaVersion"] != 1:
        raise ValueError("invalid-profile-shape")
    accelerator = profile["accelerator"]
    accelerator_required = {"vendor", "model", "totalMemoryMiB", "freeMemoryMiB", "utilizationPercent", "measurementSource"}
    if not isinstance(accelerator, dict) or set(accelerator) != accelerator_required:
        raise ValueError("invalid-accelerator-shape")
    if not isinstance(profile["competingWorkloadDetected"], bool):
        raise ValueError("invalid-competing-workload")
    measurements = {
        "availableSystemMemoryMiB": number(profile["availableSystemMemoryMiB"], "system-memory"),
        "availableDiskMiB": number(profile["availableDiskMiB"], "disk"),
        "totalMemoryMiB": number(accelerator["totalMemoryMiB"], "accelerator-total"),
        "freeMemoryMiB": number(accelerator["freeMemoryMiB"], "accelerator-free"),
        "utilizationPercent": number(accelerator["utilizationPercent"], "accelerator-utilization"),
    }
    if measurements["utilizationPercent"] > 100 or measurements["freeMemoryMiB"] > measurements["totalMemoryMiB"]:
        raise ValueError("impossible-measurement")
    missing = [key for key in ("vendor", "model", "measurementSource") if not isinstance(accelerator[key], str) or not accelerator[key].strip()]
    reasons: list[str] = []
    if missing or measurements["totalMemoryMiB"] == 0:
        decision = "measurement-required"
        reasons.append("accelerator measurement is incomplete")
    elif profile["competingWorkloadDetected"] or measurements["utilizationPercent"] >= max_utilization:
        decision = "defer"
        reasons.append("accelerator contention would invalidate the measurement")
    elif measurements["freeMemoryMiB"] < required_accelerator_mib + reserve_mib:
        decision = "insufficient-capacity"
        reasons.append("accelerator memory headroom is insufficient")
    elif measurements["availableSystemMemoryMiB"] < required_system_mib:
        decision = "insufficient-capacity"
        reasons.append("system memory headroom is insufficient")
    elif measurements["availableDiskMiB"] < required_disk_mib:
        decision = "insufficient-capacity"
        reasons.append("disk headroom is insufficient")
    else:
        decision = "ready"
        reasons.append("all measured capacity and contention gates passed")
    return {
        "SchemaVersion": 1,
        "Kind": "runtime-capacity-preflight",
        "Decision": decision,
        "Reasons": reasons,
        "NetworkUsed": False,
        "FilesWritten": False,
        "ProcessesTerminated": False,
        "DriverOrServiceChanged": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate sanitized runtime capacity without changing the machine.")
    parser.add_argument("--profile-path", required=True)
    parser.add_argument("--required-accelerator-mib", type=int, required=True)
    parser.add_argument("--required-system-mib", type=int, required=True)
    parser.add_argument("--required-disk-mib", type=int, required=True)
    parser.add_argument("--reserve-mib", type=int, default=1024)
    parser.add_argument("--max-utilization-percent", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        if min(args.required_accelerator_mib, args.required_system_mib, args.required_disk_mib, args.reserve_mib) < 0 or not 1 <= args.max_utilization_percent <= 100:
            raise ValueError("invalid-requirement")
        profile = json.loads(Path(args.profile_path).read_text(encoding="utf-8"))
        result = evaluate(profile, args.required_accelerator_mib, args.required_system_mib, args.required_disk_mib, args.reserve_mib, args.max_utilization_percent)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Runtime capacity preflight rejected input: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Decision: {result['Decision']}")
    return 0 if result["Decision"] == "ready" else 3


if __name__ == "__main__":
    raise SystemExit(main())
