#!/usr/bin/env python3
"""Convert a bounded vendor CSV log into sanitized model-energy evidence."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
import statistics
from typing import Any


MAX_INPUT_BYTES = 256 * 1024 * 1024
SAFE_DIGEST = re.compile(r"(?:sha256:)?[0-9a-f]{64}")
SAFE_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._()+:/-]{0,159}")
TASKS = ("general.chat", "content.write", "content.summarize")
SOURCES = {
    "nvidia": "nvidia-smi-csv",
    "amd": "amd-adrenalin-csv",
    "intel": "intel-xpu-smi-csv",
}
ALIASES = {
    "timestamp": (
        "timestamp", "time stamp", "time", "system time", "date time", "datetime",
        "sampling time", "sample time",
    ),
    "watts": (
        "gpu board power w", "gpu board power", "gpu power w", "gpu power",
        "power draw w", "power draw", "power consumption w", "power",
        "gpu pwr", "gpu brd pwr", "gpu chip power", "total board power",
    ),
    "utilization": (
        "gpu utilization", "gpu utilization percent", "gpu util",
        "gpu usage", "gpu activity", "gfx activity",
    ),
    "memory": (
        "gpu memory used mib", "memory used mib", "vram used mib",
        "gpu memory usage", "vram usage", "gpu memory used",
    ),
    "temperature": (
        "gpu temperature c", "gpu temperature", "temperature c",
        "temperature", "gpu temp", "junction temperature",
    ),
}


class ImportError(ValueError):
    """The external telemetry evidence was incomplete or unsafe."""


def normalized_header(value: str) -> str:
    value = value.replace("%", " percent ")
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def parse_utc_offset(value: Any) -> timezone | None:
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[+-](?:0\d|1[0-4]):[0-5]\d", value):
        raise ImportError("invalid-telemetry-utc-offset")
    sign = 1 if value[0] == "+" else -1
    hours, minutes = (int(item) for item in value[1:].split(":"))
    if hours == 14 and minutes != 0:
        raise ImportError("invalid-telemetry-utc-offset")
    return timezone(sign * timedelta(hours=hours, minutes=minutes))


def parse_timestamp(value: str, assumed_timezone: timezone | None = None) -> datetime:
    candidate = value.strip()
    if not candidate:
        raise ImportError("invalid-telemetry-timestamp")
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        for pattern in (
            "%m/%d/%Y %H:%M:%S.%f", "%m/%d/%Y %H:%M:%S",
            "%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S",
        ):
            try:
                parsed = datetime.strptime(candidate, pattern)
                break
            except ValueError:
                continue
    if parsed is None:
        raise ImportError("invalid-telemetry-timestamp")
    if parsed.tzinfo is None and assumed_timezone is not None:
        parsed = parsed.replace(tzinfo=assumed_timezone)
    if parsed.tzinfo is None:
        raise ImportError("telemetry-timestamp-must-include-timezone")
    return parsed.astimezone(timezone.utc)


def finite(value: Any, *, minimum: float = 0, maximum: float = 100_000) -> float:
    if isinstance(value, bool):
        raise ImportError("invalid-telemetry-value")
    try:
        number = float(str(value).strip().replace(",", ""))
    except (TypeError, ValueError) as error:
        raise ImportError("invalid-telemetry-value") from error
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ImportError("invalid-telemetry-value")
    return number


def optional(value: Any, *, maximum: float) -> float | None:
    if value is None or not str(value).strip() or str(value).strip().lower() in {"n/a", "na", "-"}:
        return None
    return finite(value, maximum=maximum)


def safe_file(path: Path, maximum: int = MAX_INPUT_BYTES) -> None:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ImportError("unsafe-input-file")


def load_manifest(path: Path) -> dict[str, Any]:
    safe_file(path, 2 * 1024 * 1024)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ImportError("invalid-import-manifest") from error
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        raise ImportError("invalid-import-manifest")
    return value


def resolve_columns(fieldnames: list[str], overrides: dict[str, str | None]) -> dict[str, str | None]:
    normalized = {normalized_header(name): name for name in fieldnames}
    result: dict[str, str | None] = {}
    for metric, aliases in ALIASES.items():
        override = overrides.get(metric)
        if override:
            if override not in fieldnames:
                raise ImportError(f"missing-{metric}-column")
            result[metric] = override
            continue
        result[metric] = next((normalized[name] for name in aliases if name in normalized), None)
    if result["timestamp"] is None or result["watts"] is None:
        raise ImportError("required-telemetry-columns-unavailable")
    return result


def load_samples(path: Path, overrides: dict[str, str | None],
                 assumed_timezone: timezone | None = None) -> list[dict[str, Any]]:
    safe_file(path)
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames:
                raise ImportError("missing-telemetry-header")
            columns = resolve_columns(reader.fieldnames, overrides)
            samples = []
            previous: datetime | None = None
            for row in reader:
                raw_timestamp = row[columns["timestamp"]].strip()  # type: ignore[index]
                # Adrenalin prepends one aggregate row whose timestamp is N/A.
                # It is not a time sample and must never enter window statistics.
                if raw_timestamp.lower() in {"n/a", "na"}:
                    continue
                timestamp = parse_timestamp(raw_timestamp, assumed_timezone)
                if previous is not None and timestamp <= previous:
                    raise ImportError("telemetry-timestamps-not-strictly-increasing")
                previous = timestamp
                samples.append({
                    "timestamp": timestamp,
                    "watts": finite(row[columns["watts"]], minimum=0.1, maximum=2_000),  # type: ignore[index]
                    "utilization": optional(row.get(columns["utilization"]), maximum=100),
                    "memory": optional(row.get(columns["memory"]), maximum=1_000_000),
                    "temperature": optional(row.get(columns["temperature"]), maximum=150),
                })
    except (OSError, UnicodeError, csv.Error, KeyError) as error:
        raise ImportError("invalid-telemetry-csv") from error
    if not samples:
        raise ImportError("telemetry-log-empty")
    return samples


def interval(value: Any, name: str) -> tuple[datetime, datetime]:
    if not isinstance(value, dict) or set(value) != {"startUtc", "endUtc"}:
        raise ImportError(f"invalid-{name}-window")
    start, end = parse_timestamp(value["startUtc"]), parse_timestamp(value["endUtc"])
    if end <= start:
        raise ImportError(f"invalid-{name}-window")
    return start, end


def select(samples: list[dict[str, Any]], window: tuple[datetime, datetime]) -> list[dict[str, Any]]:
    start, end = window
    return [sample for sample in samples if start <= sample["timestamp"] <= end]


def duration_seconds(window: tuple[datetime, datetime]) -> float:
    return (window[1] - window[0]).total_seconds()


def require_identity(manifest: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    identity = manifest.get("identity")
    environment = manifest.get("environment")
    if not isinstance(identity, dict) or not isinstance(environment, dict):
        raise ImportError("invalid-import-identity")
    identity_fields = ("provider", "runtimeVersion", "model", "manifestDigest")
    environment_fields = ("operatingSystem", "acceleratorVendor", "acceleratorModel", "driverVersion")
    if set(identity) != set(identity_fields) or set(environment) != set(environment_fields):
        raise ImportError("invalid-import-identity")
    if identity["provider"] not in {"ollama", "llama.cpp"}:
        raise ImportError("invalid-import-identity")
    if not isinstance(identity["manifestDigest"], str) or not SAFE_DIGEST.fullmatch(identity["manifestDigest"]):
        raise ImportError("invalid-import-identity")
    for value in [identity[name] for name in identity_fields[:-1]] + [environment[name] for name in environment_fields]:
        if not isinstance(value, str) or not SAFE_LABEL.fullmatch(value):
            raise ImportError("invalid-import-identity")
    return identity, environment


def summarize(manifest: dict[str, Any], samples: list[dict[str, Any]], vendor: str) -> dict[str, Any]:
    identity, environment = require_identity(manifest)
    if environment["acceleratorVendor"].lower() != vendor:
        raise ImportError("vendor-identity-mismatch")
    idle_window = interval(manifest.get("idleWindow"), "idle")
    active_window = interval(manifest.get("activeWindow"), "active")
    if idle_window[1] > active_window[0]:
        raise ImportError("overlapping-measurement-windows")
    idle, active = select(samples, idle_window), select(samples, active_window)
    idle_seconds, active_seconds = duration_seconds(idle_window), duration_seconds(active_window)
    sampling_interval = finite(manifest.get("samplingIntervalSeconds"), minimum=0.5, maximum=10)
    required_idle = max(1, math.floor(idle_seconds / sampling_interval * 0.8))
    required_active = max(1, math.floor(active_seconds / sampling_interval * 0.8))
    if idle_seconds < 120 or active_seconds < 300 or len(idle) < required_idle or len(active) < required_active:
        raise ImportError("insufficient-telemetry-coverage")
    task_windows = manifest.get("taskWindows")
    if not isinstance(task_windows, list) or len(task_windows) < 3:
        raise ImportError("incomplete-task-energy-evidence")
    by_task: dict[str, dict[str, Any]] = {}
    total_tokens = 0
    for task in TASKS:
        matching = [item for item in task_windows if isinstance(item, dict) and item.get("capability") == task]
        if not matching:
            raise ImportError("incomplete-task-energy-evidence")
        task_samples: list[dict[str, Any]] = []
        task_duration = 0.0
        task_tokens = 0
        for item in matching:
            window = interval({"startUtc": item.get("startUtc"), "endUtc": item.get("endUtc")}, "task")
            if window[0] < active_window[0] or window[1] > active_window[1]:
                raise ImportError("task-window-outside-active-window")
            tokens = item.get("outputTokens")
            if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens <= 0:
                raise ImportError("invalid-task-token-count")
            task_samples.extend(select(samples, window))
            task_duration += duration_seconds(window)
            task_tokens += tokens
        if not task_samples:
            raise ImportError("incomplete-task-energy-evidence")
        watts = [item["watts"] for item in task_samples]
        energy = statistics.fmean(watts) * task_duration / 3600
        by_task[task] = {
            "sampleCount": len(task_samples), "requestSeconds": round(task_duration, 3),
            "averageWatts": round(statistics.fmean(watts), 3), "peakWatts": round(max(watts), 3),
            "outputTokens": task_tokens, "outputTokensPerWh": round(task_tokens / energy, 3),
        }
        total_tokens += task_tokens
    idle_watts = [item["watts"] for item in idle]
    active_watts = [item["watts"] for item in active]
    idle_average, load_average = statistics.fmean(idle_watts), statistics.fmean(active_watts)
    energy_wh = load_average * active_seconds / 3600
    metrics: dict[str, Any] = {
        "idleAverageWatts": round(idle_average, 3), "loadAverageWatts": round(load_average, 3),
        "loadPeakWatts": round(max(active_watts), 3),
        "idleAdjustedAverageWatts": round(max(0.0, load_average - idle_average), 3),
        "measuredGpuEnergyWh": round(energy_wh, 6),
        "idleAdjustedGpuEnergyWh": round(max(0.0, load_average - idle_average) * active_seconds / 3600, 6),
        "outputTokens": total_tokens, "outputTokensPerSecond": round(total_tokens / active_seconds, 3),
        "outputTokensPerWh": round(total_tokens / energy_wh, 3), "byTask": by_task,
    }
    optional_metrics = {
        "averageGpuUtilizationPercent": ("utilization", statistics.fmean),
        "peakMemoryUsedMiB": ("memory", max),
        "peakTemperatureCelsius": ("temperature", max),
    }
    for name, (field, operation) in optional_metrics.items():
        values = [item[field] for item in active if item[field] is not None]
        if values:
            metrics[name] = round(operation(values), 3)
    measured_at = active_window[1].replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schemaVersion": 1, "kind": "haven42-model-energy-measurement", "outcome": "passed",
        "measuredAtUtc": measured_at,
        "identity": {**identity, "manifestDigest": identity["manifestDigest"].removeprefix("sha256:")},
        "environment": environment,
        "workload": {
            "taskSampleCounts": {task: len([item for item in task_windows if item.get("capability") == task]) for task in TASKS},
            "idleBaselineSeconds": idle_seconds, "activeMeasurementSeconds": active_seconds,
            "samplingIntervalSeconds": sampling_interval,
        },
        "telemetry": {
            "source": SOURCES[vendor], "scope": "gpu-board-or-package-only",
            "idleSampleCount": len(idle), "activeSampleCount": len(active),
            "includesCpuRamStorageOrPsuLosses": False, "importedFromExternalLog": True,
        },
        "metrics": metrics, "billEstimate": None,
        "evidence": {
            "containsRawPromptsOrResponses": False, "containsPrivateMachineIdentity": False,
            "containsProviderEndpoint": False, "automaticPromotionAllowed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor", choices=tuple(SOURCES), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    for metric in ALIASES:
        parser.add_argument(f"--{metric}-column")
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("output already exists or is unsafe")
    try:
        overrides = {metric: getattr(args, f"{metric}_column") for metric in ALIASES}
        manifest = load_manifest(args.manifest)
        evidence = summarize(
            manifest,
            load_samples(args.input, overrides, parse_utc_offset(manifest.get("telemetryUtcOffset"))),
            args.vendor,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (ImportError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({"outcome": "passed", "model": evidence["identity"]["model"], "samples": evidence["telemetry"]["activeSampleCount"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
