#!/usr/bin/env python3
"""Summarize Apple powermetrics output without retaining host identity."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


POWER = re.compile(r"^(CPU|GPU|ANE|Combined) Power(?: \(CPU \+ GPU \+ ANE\))?:\s+([0-9]+(?:\.[0-9]+)?)\s+mW$", re.MULTILINE)
GPU_RESIDENCY = re.compile(r"^GPU HW active residency:\s+([0-9]+(?:\.[0-9]+)?)%", re.MULTILINE)
THERMAL = re.compile(r"^Current pressure level:\s+([A-Za-z][A-Za-z -]{0,31})$", re.MULTILINE)


class PowerSummaryError(ValueError):
    pass


def metric(values: list[float]) -> dict[str, float | int]:
    if not values or any(not math.isfinite(value) or value < 0 for value in values):
        raise PowerSummaryError("invalid-power-samples")
    return {
        "samples": len(values),
        "minimum": round(min(values), 3),
        "average": round(sum(values) / len(values), 3),
        "maximum": round(max(values), 3),
    }


def summarize(raw: str) -> dict[str, Any]:
    power: dict[str, list[float]] = {name: [] for name in ("CPU", "GPU", "ANE", "Combined")}
    residency: list[float] = []
    thermal: list[str] = []
    blocks = re.split(r"^\*\*\* Sampled system activity .*?\*\*\*$", raw, flags=re.MULTILINE)[1:]
    for block in blocks:
        sample: dict[str, float] = {}
        for name, value in POWER.findall(block):
            sample.setdefault(name, float(value))
        gpu = GPU_RESIDENCY.search(block)
        pressure = THERMAL.search(block)
        if set(sample) != set(power) or gpu is None or pressure is None:
            raise PowerSummaryError("incomplete-sample-block")
        for name in power:
            power[name].append(sample[name])
        residency.append(float(gpu.group(1)))
        thermal.append(pressure.group(1).strip().lower().replace(" ", "-"))
    if not power["Combined"] or any(len(values) != len(power["Combined"]) for values in power.values()):
        raise PowerSummaryError("incomplete-power-samples")
    if len(residency) != len(power["Combined"]):
        raise PowerSummaryError("incomplete-gpu-residency-samples")
    if len(thermal) != len(power["Combined"]):
        raise PowerSummaryError("incomplete-thermal-samples")
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-macos-power-summary",
        "powerMilliwatts": {name.lower(): metric(values) for name, values in power.items()},
        "gpuActiveResidencyPercent": metric(residency),
        "thermalPressureLevels": sorted(set(thermal)),
        "rawTelemetryRetained": False,
        "privateIdentityRetained": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Read raw powermetrics output from this file instead of stdin.")
    args = parser.parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        print(json.dumps(summarize(raw), indent=2, sort_keys=True))
    except (OSError, UnicodeError, PowerSummaryError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
