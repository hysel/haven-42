#!/usr/bin/env python3
"""Measure one bounded, sanitized AMD GPU idle/load/cooldown profile."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import statistics
import threading
import time
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "config/alpha-2-rx5700xt-certification-plan.json"
RUNNER_PATH = ROOT / "scripts/alpha2-linux-model-validation.py"
PROFILE_ID = "vulkan-8gib-system-16gib"
OPERATING_SYSTEM_ID = "ubuntu-26.04-rx5700xt"
IDLE_SECONDS = 120
ACTIVE_SECONDS = 600
COOLDOWN_SECONDS = 120
SAMPLE_INTERVAL_SECONDS = 0.5
FIXED_PROMPT = "Write one concise sentence encouraging careful software testing."


class PowerProfileError(ValueError):
    """Power or inference evidence could not be measured safely."""


def _module():
    specification = importlib.util.spec_from_file_location(
        "alpha2_model_validation_for_power", RUNNER_PATH
    )
    if specification is None or specification.loader is None:
        raise PowerProfileError("model-runner-unavailable")
    value = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(value)
    return value


MODEL_RUNNER = _module()


def _load_plan(path: Path = PLAN_PATH) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise PowerProfileError("unsafe-power-plan")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PowerProfileError("invalid-power-plan") from error
    hardware = value.get("hardwareClass") if isinstance(value, dict) else None
    if (
        value.get("planId") != "haven42.alpha2.amd-radeon-rx5700xt-8g"
        or not isinstance(hardware, dict)
        or hardware.get("pciVendorId") != "0x1002"
        or hardware.get("pciDeviceId") != "0x731f"
        or hardware.get("kernelDriver") != "amdgpu"
        or hardware.get("memoryGiB") != 8
    ):
        raise PowerProfileError("invalid-power-plan")
    return value


def _read_integer(path: Path) -> int:
    try:
        if path.is_symlink() or not path.is_file():
            raise PowerProfileError("unsafe-power-sensor")
        # Sysfs attributes commonly report a synthetic 4096-byte stat size even
        # when the actual value is only a few bytes. Bound the read itself.
        with path.open("r", encoding="ascii") as handle:
            raw = handle.read(129)
        if len(raw) > 128:
            raise PowerProfileError("unsafe-power-sensor")
        value = int(raw.strip())
    except PowerProfileError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise PowerProfileError("power-sensor-unreadable") from error
    if not 0 <= value <= 2_000_000_000:
        raise PowerProfileError("power-sensor-out-of-range")
    return value


def find_power_sensor(
    drm_root: Path = Path("/sys/class/drm"),
    vendor_id: str = "0x1002",
    device_id: str = "0x731f",
) -> Path:
    matches: list[Path] = []
    for card in sorted(drm_root.glob("card[0-9]*")):
        device = card / "device"
        try:
            vendor = (device / "vendor").read_text(encoding="ascii").strip().lower()
            observed_device = (device / "device").read_text(encoding="ascii").strip().lower()
        except (OSError, UnicodeError):
            continue
        if vendor == vendor_id and observed_device == device_id:
            matches.extend(device.glob("hwmon/hwmon*/power1_average"))
    safe = [path for path in matches if path.is_file() and not path.is_symlink()]
    if len(safe) != 1:
        raise PowerProfileError("power-sensor-not-unique")
    _read_integer(safe[0])
    return safe[0]


def summarize_samples(samples: list[tuple[float, int]]) -> dict[str, Any]:
    if len(samples) < 2:
        raise PowerProfileError("insufficient-power-samples")
    ordered = sorted(samples)
    if ordered != samples or any(b[0] <= a[0] for a, b in zip(samples, samples[1:])):
        raise PowerProfileError("invalid-power-sample-order")
    watts = [value / 1_000_000 for _, value in samples]
    duration = samples[-1][0] - samples[0][0]
    if not 0 < duration <= 3600 or any(not math.isfinite(value) for value in watts):
        raise PowerProfileError("invalid-power-samples")
    watt_seconds = sum(
        ((left[1] + right[1]) / 2 / 1_000_000) * (right[0] - left[0])
        for left, right in zip(samples, samples[1:])
    )
    return {
        "samples": len(samples),
        "durationSeconds": round(duration, 3),
        "averageWatts": round(watt_seconds / duration, 3),
        "medianWatts": round(statistics.median(watts), 3),
        "peakWatts": round(max(watts), 3),
        "energyWattHours": round(watt_seconds / 3600, 6),
    }


def _collect(
    duration: float, sensor: Path, interval: float,
    work: Callable[[], dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    samples: list[tuple[float, int]] = []
    stop = threading.Event()
    error: list[Exception] = []

    def sampler() -> None:
        while not stop.is_set():
            try:
                samples.append((time.monotonic(), _read_integer(sensor)))
            except Exception as caught:  # recorded and re-raised in the main thread
                error.append(caught)
                stop.set()
                return
            stop.wait(interval)

    thread = threading.Thread(target=sampler, name="bounded-power-sampler", daemon=True)
    thread.start()
    result = None
    started = time.monotonic()
    try:
        if work is None:
            while time.monotonic() - started < duration and not error:
                time.sleep(min(interval, 0.1))
        else:
            result = work()
    finally:
        stop.set()
        thread.join(timeout=max(2.0, interval * 4))
    if thread.is_alive() or error:
        raise PowerProfileError("power-sampling-failed")
    return summarize_samples(samples), result


def run_profile(
    *, origin: str, model_id: str,
    idle_seconds: float = IDLE_SECONDS,
    active_seconds: float = ACTIVE_SECONDS,
    cooldown_seconds: float = COOLDOWN_SECONDS,
    sample_interval: float = SAMPLE_INTERVAL_SECONDS,
    sensor: Path | None = None,
) -> dict[str, Any]:
    _load_plan()
    if (
        model_id != "llama32-3b-q4"
        or not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (
            idle_seconds, active_seconds, cooldown_seconds, sample_interval
        ))
        or not 0 < sample_interval <= 5
        or not sample_interval * 2 <= min(idle_seconds, active_seconds, cooldown_seconds)
        or max(idle_seconds, active_seconds, cooldown_seconds) > 900
    ):
        raise PowerProfileError("unreviewed-power-profile")
    checked_origin = MODEL_RUNNER.validate_origin(origin)
    model, inventory_sha, provider_version = MODEL_RUNNER.reviewed_qualification_model(model_id)
    MODEL_RUNNER.verify_provider(checked_origin, model, provider_version)
    power_sensor = sensor or find_power_sensor()
    MODEL_RUNNER._unload(checked_origin, model)
    idle, _ = _collect(idle_seconds, power_sensor, sample_interval)
    totals = {"outputTokens": 0, "requests": 0, "peakGpuMemoryBytes": 0}

    def active_work() -> dict[str, Any]:
        started = time.monotonic()
        while time.monotonic() - started < active_seconds:
            response = MODEL_RUNNER._json_request(
                checked_origin, "/api/generate", {
                    "model": model["name"], "prompt": FIXED_PROMPT,
                    "stream": False, "think": False, "keep_alive": "5m",
                    "options": {"temperature": 0, "seed": 42, "num_predict": 128},
                }, timeout=120,
            )
            _, output_tokens, _ = MODEL_RUNNER._validate_generate(response)
            totals["outputTokens"] += output_tokens
            totals["requests"] += 1
            totals["peakGpuMemoryBytes"] = max(
                totals["peakGpuMemoryBytes"],
                MODEL_RUNNER._verify_residency(checked_origin, model, "vulkan"),
            )
        return totals

    try:
        active, _ = _collect(active_seconds, power_sensor, sample_interval, active_work)
    finally:
        MODEL_RUNNER._unload(checked_origin, model)
    cooldown, _ = _collect(cooldown_seconds, power_sensor, sample_interval)
    energy = active["energyWattHours"]
    if totals["requests"] < 1 or totals["outputTokens"] < 1 or energy <= 0:
        raise PowerProfileError("active-power-profile-incomplete")
    return {
        "schemaVersion": 1,
        "kind": "alpha2-linux-amd-gpu-power-profile",
        "observedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "outcome": "passed",
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "containsNetworkIdentity": False,
        "powerScope": "gpu-board-sysfs-power1-average",
        "modelId": model_id,
        "manifestDigest": model["manifestDigest"],
        "provider": "ollama",
        "providerVersion": provider_version,
        "backend": "vulkan",
        "profileId": PROFILE_ID,
        "operatingSystemId": OPERATING_SYSTEM_ID,
        "qualificationInventoryCanonicalSha256": inventory_sha,
        "idle": idle,
        "active": {**active, **totals, "tokensPerWattHour": round(totals["outputTokens"] / energy, 3)},
        "cooldown": cooldown,
        "modelUnloadVerified": True,
        "automaticSupportChangeAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="http://127.0.0.1:11434")
    parser.add_argument("--model-id", default="llama32-3b-q4")
    args = parser.parse_args()
    try:
        result = run_profile(origin=args.origin, model_id=args.model_id)
    except (PowerProfileError, MODEL_RUNNER.ValidationError) as error:
        print(json.dumps({
            "schemaVersion": 1, "kind": "alpha2-linux-amd-gpu-power-profile",
            "outcome": "failed", "errorCode": str(error),
            "containsRawPromptsOrResponses": False,
            "containsPrivateMachineIdentity": False,
            "automaticSupportChangeAllowed": False,
        }, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
