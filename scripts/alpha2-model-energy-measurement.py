#!/usr/bin/env python3
"""Measure sanitized GPU energy evidence for one exact local model artifact."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import ipaddress
import json
import math
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import threading
import time
from typing import Any, Callable
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


SAFE_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._()+:/-]{0,159}")
SAFE_DIGEST = re.compile(r"(?:sha256:)?[0-9a-f]{64}")
TASKS = (
    ("general.chat", "Reply with exactly HAVEN42_READY and nothing else."),
    (
        "content.write",
        "Write one sentence about why careful software testing matters.",
    ),
    (
        "content.summarize",
        "Summarize in one sentence: local AI keeps private work on the computer, "
        "but users should still review generated answers.",
    ),
)


class MeasurementError(ValueError):
    """The energy measurement failed closed."""


def normalize_digest(value: str) -> str:
    if not SAFE_DIGEST.fullmatch(value):
        raise MeasurementError("invalid-model-digest")
    return value.removeprefix("sha256:")


@dataclass(frozen=True)
class PowerSample:
    monotonic_seconds: float
    watts: float
    utilization_percent: float | None = None
    memory_used_mib: float | None = None
    temperature_celsius: float | None = None
    task: str | None = None
    device_watts: tuple[float, ...] = ()


def _finite(value: Any, *, minimum: float = 0, maximum: float = 100_000) -> float:
    if isinstance(value, bool):
        raise MeasurementError("invalid-telemetry-value")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise MeasurementError("invalid-telemetry-value") from error
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise MeasurementError("invalid-telemetry-value")
    return number


def _optional(value: Any, *, maximum: float) -> float | None:
    if value in (None, "", "N/A", "[N/A]"):
        return None
    return _finite(value, maximum=maximum)


def _run(args: list[str]) -> str:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            check=False,
            text=True,
            timeout=15,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise MeasurementError("telemetry-command-failed") from error
    if result.returncode != 0 or not result.stdout.strip():
        raise MeasurementError("telemetry-command-failed")
    return result.stdout


def _flatten_json(value: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(value, dict):
        if "value" in value and isinstance(value.get("value"), (int, float)):
            result[prefix.lower()] = value["value"]
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            result.update(_flatten_json(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            result.update(_flatten_json(item, f"{prefix}.{index}"))
    elif prefix:
        result[prefix.lower()] = value
    return result


def _find_metric(flat: dict[str, Any], names: tuple[str, ...]) -> Any:
    normalized = tuple(
        re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") for name in names
    )
    for key, value in flat.items():
        leaf = re.sub(
            r"[^a-z0-9]+", "_", key.rsplit(".", 1)[-1].lower()
        ).strip("_")
        if leaf in normalized:
            return value
    return None


class TelemetrySampler:
    vendor: str
    source: str
    scope: str = "gpu-board-or-package-only"

    def sample(self, *, task: str | None = None) -> PowerSample:
        raise NotImplementedError


class NvidiaSampler(TelemetrySampler):
    vendor = "nvidia"
    source = "nvidia-smi"

    def __init__(self, device: str) -> None:
        executable = shutil.which("nvidia-smi")
        if not executable:
            raise MeasurementError("nvidia-smi-not-found")
        self.command = [
            executable,
            f"--id={device}",
            "--query-gpu=power.draw,utilization.gpu,memory.used,temperature.gpu",
            "--format=csv,noheader,nounits",
        ]

    def sample(self, *, task: str | None = None) -> PowerSample:
        fields = [part.strip() for part in _run(self.command).splitlines()[0].split(",")]
        if len(fields) != 4:
            raise MeasurementError("invalid-nvidia-telemetry")
        return PowerSample(
            time.monotonic(),
            _finite(fields[0], minimum=0.1, maximum=2_000),
            _optional(fields[1], maximum=100),
            _optional(fields[2], maximum=1_000_000),
            _optional(fields[3], maximum=150),
            task,
        )


class AmdSampler(TelemetrySampler):
    vendor = "amd"
    source = "amd-smi"

    def __init__(self, device: str) -> None:
        executable = shutil.which("amd-smi")
        if not executable:
            raise MeasurementError("amd-smi-not-found")
        self.command = [
            executable, "metric", "-g", device, "-p", "-u", "-m", "-t", "--json",
        ]

    def sample(self, *, task: str | None = None) -> PowerSample:
        try:
            flat = _flatten_json(json.loads(_run(self.command)))
        except json.JSONDecodeError as error:
            raise MeasurementError("invalid-amd-telemetry") from error
        power = _find_metric(flat, ("socket_power", "average_socket_power", "power"))
        if power is None:
            raise MeasurementError("amd-power-unavailable")
        return PowerSample(
            time.monotonic(),
            _finite(power, minimum=0.1, maximum=2_000),
            _optional(_find_metric(flat, ("gfx_activity", "gpu_use", "utilization")), maximum=100),
            _optional(_find_metric(flat, ("vram_used", "memory_used")), maximum=1_000_000),
            _optional(_find_metric(flat, ("temperature", "edge_temperature", "hotspot_temperature")), maximum=150),
            task,
        )


class IntelSampler(TelemetrySampler):
    vendor = "intel"
    source = "xpu-smi"

    def __init__(self, device: str) -> None:
        executable = shutil.which("xpu-smi")
        if not executable:
            raise MeasurementError("xpu-smi-not-found")
        self.command = [executable, "stats", "--device", device, "-j"]

    def sample(self, *, task: str | None = None) -> PowerSample:
        try:
            flat = _flatten_json(json.loads(_run(self.command)))
        except json.JSONDecodeError as error:
            raise MeasurementError("invalid-intel-telemetry") from error
        power = _find_metric(flat, ("gpu_power", "gpu_power_w", "power_draw", "power"))
        if power is None:
            raise MeasurementError("intel-power-unavailable")
        return PowerSample(
            time.monotonic(),
            _finite(power, minimum=0.1, maximum=2_000),
            _optional(_find_metric(flat, ("gpu_utilization", "gpu_utilization_percent", "gpu_util", "utilization")), maximum=100),
            _optional(_find_metric(flat, ("gpu_memory_used", "gpu_memory_used_mib", "memory_used")), maximum=1_000_000),
            _optional(_find_metric(flat, ("gpu_core_temperature", "gpu_core_temperature_c", "temperature")), maximum=150),
            task,
        )


class CompositeSampler(TelemetrySampler):
    """Combine multiple same-vendor devices without retaining device identity."""

    def __init__(self, samplers: list[TelemetrySampler]) -> None:
        if len(samplers) < 2 or len({item.vendor for item in samplers}) != 1:
            raise MeasurementError("invalid-composite-sampler")
        self.samplers = samplers
        self.vendor = samplers[0].vendor
        self.source = samplers[0].source

    def sample(self, *, task: str | None = None) -> PowerSample:
        samples = [item.sample(task=task) for item in self.samplers]
        utilization = [item.utilization_percent for item in samples if item.utilization_percent is not None]
        memory = [item.memory_used_mib for item in samples if item.memory_used_mib is not None]
        temperature = [item.temperature_celsius for item in samples if item.temperature_celsius is not None]
        powers = tuple(item.watts for item in samples)
        return PowerSample(
            monotonic_seconds=max(item.monotonic_seconds for item in samples),
            watts=sum(powers),
            utilization_percent=statistics.fmean(utilization) if utilization else None,
            memory_used_mib=sum(memory) if memory else None,
            temperature_celsius=max(temperature) if temperature else None,
            task=task,
            device_watts=powers,
        )


def create_sampler(vendor: str, device: str) -> TelemetrySampler:
    classes = {"nvidia": NvidiaSampler, "amd": AmdSampler, "intel": IntelSampler}
    try:
        devices = [item.strip() for item in device.split(",") if item.strip()]
        if not devices or len(devices) != len(set(devices)):
            raise MeasurementError("invalid-telemetry-devices")
        samplers = [classes[vendor](item) for item in devices]
        return samplers[0] if len(samplers) == 1 else CompositeSampler(samplers)
    except KeyError as error:
        raise MeasurementError("unsupported-telemetry-vendor") from error


def validate_origin(value: str) -> str:
    parsed = urlsplit(value.rstrip("/"))
    if (
        parsed.scheme != "http" or not parsed.hostname or parsed.username
        or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/")
    ):
        raise MeasurementError("unsafe-provider-origin")
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError as error:
        raise MeasurementError("provider-origin-must-use-ip-literal") from error
    if not (address.is_private or address.is_loopback):
        raise MeasurementError("provider-origin-must-be-private")
    return value.rstrip("/")


def json_request(origin: str, path: str, payload: dict[str, Any] | None = None,
                 *, timeout: int = 600) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        origin + path,
        data=body,
        method="GET" if body is None else "POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        raise MeasurementError("provider-request-failed") from error
    if not isinstance(value, dict):
        raise MeasurementError("invalid-provider-response")
    return value


def installed_digest(origin: str, model: str) -> str:
    models = json_request(origin, "/api/tags", timeout=30).get("models")
    if not isinstance(models, list):
        raise MeasurementError("invalid-provider-model-list")
    matches = [
        item for item in models
        if isinstance(item, dict) and item.get("name") == model
    ]
    if len(matches) != 1 or not isinstance(matches[0].get("digest"), str):
        raise MeasurementError("exact-model-not-installed")
    return matches[0]["digest"]


def collect_idle(sampler: TelemetrySampler, seconds: float, interval: float,
                 sleep: Callable[[float], None] = time.sleep) -> list[PowerSample]:
    deadline = time.monotonic() + seconds
    samples: list[PowerSample] = []
    while time.monotonic() < deadline:
        samples.append(sampler.sample())
        sleep(min(interval, max(0, deadline - time.monotonic())))
    return samples


def summarize_samples(idle: list[PowerSample], active: list[PowerSample],
                      duration_seconds: float, output_tokens: int) -> dict[str, Any]:
    if not idle or not active or duration_seconds <= 0 or output_tokens <= 0:
        raise MeasurementError("insufficient-energy-evidence")
    idle_watts = [_finite(item.watts, minimum=0.1, maximum=2_000) for item in idle]
    active_watts = [_finite(item.watts, minimum=0.1, maximum=2_000) for item in active]
    idle_average = statistics.fmean(idle_watts)
    active_average = statistics.fmean(active_watts)
    incremental_average = max(0.0, active_average - idle_average)
    energy_wh = active_average * duration_seconds / 3600
    incremental_wh = incremental_average * duration_seconds / 3600
    metrics: dict[str, Any] = {
        "idleAverageWatts": round(idle_average, 3),
        "loadAverageWatts": round(active_average, 3),
        "loadPeakWatts": round(max(active_watts), 3),
        "idleAdjustedAverageWatts": round(incremental_average, 3),
        "measuredGpuEnergyWh": round(energy_wh, 6),
        "idleAdjustedGpuEnergyWh": round(incremental_wh, 6),
        "outputTokens": output_tokens,
        "outputTokensPerSecond": round(output_tokens / duration_seconds, 3),
        "outputTokensPerWh": round(output_tokens / energy_wh, 3),
    }
    optional = {
        "averageGpuUtilizationPercent": [item.utilization_percent for item in active],
        "peakMemoryUsedMiB": [item.memory_used_mib for item in active],
        "peakTemperatureCelsius": [item.temperature_celsius for item in active],
    }
    for key, values in optional.items():
        available = [float(value) for value in values if value is not None]
        if available:
            metrics[key] = round(
                statistics.fmean(available) if key.startswith("average") else max(available),
                3,
            )
    device_counts = {len(item.device_watts) for item in active if item.device_watts}
    if len(device_counts) == 1:
        count = device_counts.pop()
        if count > 0 and all(len(item.device_watts) == count for item in active):
            metrics["perDeviceLoadAverageWatts"] = [
                round(statistics.fmean(item.device_watts[index] for item in active), 3)
                for index in range(count)
            ]
            metrics["perDeviceLoadPeakWatts"] = [
                round(max(item.device_watts[index] for item in active), 3)
                for index in range(count)
            ]
    return metrics


def estimate_monthly_cost(load_average_watts: float, rate_per_kwh: float,
                          hours_per_day: float, days: int,
                          currency: str = "USD") -> dict[str, Any]:
    watts = _finite(load_average_watts, maximum=2_000)
    rate = _finite(rate_per_kwh, maximum=100)
    hours = _finite(hours_per_day, maximum=24)
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 366:
        raise MeasurementError("invalid-billing-days")
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise MeasurementError("invalid-currency")
    kwh = watts / 1000 * hours * days
    return {
        "electricityRatePerKwh": round(rate, 6),
        "currency": currency,
        "usageHoursPerDay": round(hours, 3),
        "billingDays": days,
        "estimatedGpuOnlyKwh": round(kwh, 6),
        "estimatedGpuOnlyCost": round(kwh * rate, 2),
        "notWholeComputerCost": True,
    }


def task_energy_metrics(samples: list[PowerSample], task_seconds: dict[str, float],
                        task_tokens: dict[str, int]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for task, _ in TASKS:
        selected = [item.watts for item in samples if item.task == task]
        seconds = task_seconds.get(task, 0)
        tokens = task_tokens.get(task, 0)
        if not selected or seconds <= 0 or tokens <= 0:
            raise MeasurementError("incomplete-task-energy-evidence")
        average = statistics.fmean(selected)
        energy_wh = average * seconds / 3600
        result[task] = {
            "sampleCount": len(selected),
            "requestSeconds": round(seconds, 3),
            "averageWatts": round(average, 3),
            "peakWatts": round(max(selected), 3),
            "outputTokens": tokens,
            "outputTokensPerWh": round(tokens / energy_wh, 3),
        }
    return result


def run_measurement(args: argparse.Namespace, sampler: TelemetrySampler) -> dict[str, Any]:
    origin = validate_origin(args.origin)
    version = json_request(origin, "/api/version", timeout=30).get("version")
    if version != args.runtime_version:
        raise MeasurementError("runtime-version-mismatch")
    if normalize_digest(installed_digest(origin, args.model)) != normalize_digest(args.expected_digest):
        raise MeasurementError("installed-model-digest-mismatch")
    loaded = json_request(origin, "/api/ps", timeout=30).get("models")
    if not isinstance(loaded, list) or loaded:
        raise MeasurementError("provider-not-idle-before-measurement")

    idle = collect_idle(sampler, args.idle_seconds, args.sample_interval)
    idle_utilization = [item.utilization_percent for item in idle if item.utilization_percent is not None]
    if idle_utilization and statistics.fmean(idle_utilization) > 10:
        raise MeasurementError("accelerator-not-idle-before-measurement")
    warmup = json_request(origin, "/api/generate", {
        "model": args.model,
        "prompt": TASKS[0][1],
        "stream": False,
        "keep_alive": "5m",
        "options": {"temperature": 0, "num_predict": 32},
    })
    if not isinstance(warmup.get("response"), str):
        raise MeasurementError("model-warmup-failed")

    active: list[PowerSample] = []
    failures: list[str] = []
    current_task: list[str | None] = [None]
    lock = threading.Lock()
    stop = threading.Event()

    def monitor() -> None:
        while not stop.is_set():
            with lock:
                task = current_task[0]
            try:
                active.append(sampler.sample(task=task))
            except MeasurementError as error:
                failures.append(str(error))
                stop.set()
                return
            stop.wait(args.sample_interval)

    thread = threading.Thread(target=monitor, name="gpu-energy-monitor", daemon=True)
    started = time.monotonic()
    deadline = started + args.active_seconds
    output_tokens = 0
    task_counts = {task: 0 for task, _ in TASKS}
    task_seconds = {task: 0.0 for task, _ in TASKS}
    task_tokens = {task: 0 for task, _ in TASKS}
    thread.start()
    try:
        cycle = 0
        while time.monotonic() < deadline or cycle == 0:
            task, prompt = TASKS[cycle % len(TASKS)]
            with lock:
                current_task[0] = task
            request_started = time.monotonic()
            result = json_request(origin, "/api/generate", {
                "model": args.model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "5m",
                "options": {"temperature": 0, "num_predict": 128},
            })
            count = result.get("eval_count")
            if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
                raise MeasurementError("missing-output-token-count")
            task_seconds[task] += time.monotonic() - request_started
            task_tokens[task] += count
            output_tokens += count
            task_counts[task] += 1
            cycle += 1
            if failures:
                raise MeasurementError(failures[0])
    finally:
        with lock:
            current_task[0] = None
        stop.set()
        thread.join(timeout=max(5, args.sample_interval * 2))
        try:
            json_request(origin, "/api/generate", {
                "model": args.model, "prompt": "", "stream": False, "keep_alive": 0,
            }, timeout=60)
        except MeasurementError:
            pass

    elapsed = time.monotonic() - started
    expected_samples = max(1, math.floor(min(elapsed, args.active_seconds) / args.sample_interval * 0.8))
    if failures or len(active) < expected_samples:
        raise MeasurementError("insufficient-telemetry-samples")
    metrics = summarize_samples(idle, active, elapsed, output_tokens)
    metrics["byTask"] = task_energy_metrics(active, task_seconds, task_tokens)
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "haven42-model-energy-measurement",
        "outcome": "passed",
        "measuredAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "identity": {
            "provider": "ollama",
            "runtimeVersion": version,
            "model": args.model,
            "manifestDigest": normalize_digest(args.expected_digest),
        },
        "environment": {
            "operatingSystem": args.operating_system,
            "acceleratorVendor": sampler.vendor,
            "acceleratorModel": args.accelerator_model,
            "driverVersion": args.driver_version,
        },
        "workload": {
            "taskSampleCounts": task_counts,
            "idleBaselineSeconds": args.idle_seconds,
            "activeMeasurementSeconds": round(elapsed, 3),
            "samplingIntervalSeconds": args.sample_interval,
        },
        "telemetry": {
            "source": sampler.source,
            "scope": sampler.scope,
            "idleSampleCount": len(idle),
            "activeSampleCount": len(active),
            "includesCpuRamStorageOrPsuLosses": False,
        },
        "metrics": metrics,
        "billEstimate": None,
        "evidence": {
            "containsRawPromptsOrResponses": False,
            "containsPrivateMachineIdentity": False,
            "containsProviderEndpoint": False,
            "automaticPromotionAllowed": False,
        },
    }
    if args.electricity_rate is not None:
        result["billEstimate"] = estimate_monthly_cost(
            metrics["loadAverageWatts"], args.electricity_rate,
            args.usage_hours_per_day, args.billing_days, args.currency,
        )
    return result


def _label(value: str, name: str) -> str:
    if not SAFE_LABEL.fullmatch(value):
        raise argparse.ArgumentTypeError(f"invalid {name}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--model", required=True, type=lambda value: _label(value, "model"))
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--runtime-version", required=True, type=lambda value: _label(value, "runtime version"))
    parser.add_argument("--vendor", choices=("nvidia", "amd", "intel"), required=True)
    parser.add_argument("--device", default="0", help="One device or a comma-separated device list")
    parser.add_argument("--accelerator-model", required=True, type=lambda value: _label(value, "accelerator model"))
    parser.add_argument("--driver-version", required=True, type=lambda value: _label(value, "driver version"))
    parser.add_argument("--operating-system", required=True, type=lambda value: _label(value, "operating system"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--idle-seconds", type=float, default=120)
    parser.add_argument("--active-seconds", type=float, default=300)
    parser.add_argument("--sample-interval", type=float, default=1)
    parser.add_argument("--electricity-rate", type=float)
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--usage-hours-per-day", type=float, default=2)
    parser.add_argument("--billing-days", type=int, default=30)
    args = parser.parse_args()
    if not SAFE_DIGEST.fullmatch(args.expected_digest):
        parser.error("expected digest must be an exact sha256 digest")
    args.expected_digest = normalize_digest(args.expected_digest)
    if not re.fullmatch(r"[A-Za-z0-9:.,-]{1,200}", args.device):
        parser.error("invalid telemetry device list")
    if args.idle_seconds < 120 or args.active_seconds < 300:
        parser.error("published measurements require a 120-second idle baseline and 300-second active run")
    if not 0.5 <= args.sample_interval <= 10:
        parser.error("sample interval must be between 0.5 and 10 seconds")
    if args.output.is_symlink() or args.output.exists():
        parser.error("output already exists or is unsafe")
    try:
        result = run_measurement(args, create_sampler(args.vendor, args.device))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (MeasurementError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({
        "outcome": result["outcome"],
        "model": result["identity"]["model"],
        "averageWatts": result["metrics"]["loadAverageWatts"],
        "energyWh": result["metrics"]["measuredGpuEnergyWh"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
