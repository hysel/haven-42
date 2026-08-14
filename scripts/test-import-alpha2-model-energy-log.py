#!/usr/bin/env python3
"""Deterministic checks for imported vendor energy logs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/import-alpha2-model-energy-log.py"


def load_module():
    specification = importlib.util.spec_from_file_location("alpha2_energy_import", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def refused(callback, message: str) -> None:
    try:
        callback()
    except Exception as error:
        assert str(error) == message, (str(error), message)
    else:
        raise AssertionError(f"expected refusal: {message}")


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def main() -> int:
    module = load_module()
    start = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        csv_path = root / "adrenalin.csv"
        lines = ["System Time,GPU Board Power (W),GPU Utilization (%),GPU Memory Used (MiB),GPU Temperature (C)"]
        for second in range(481):
            timestamp = start + timedelta(seconds=second)
            active = second >= 180
            lines.append(f"{iso(timestamp)},{120 if active else 20},{80 if active else 2},{4096 if active else 128},{65 if active else 40}")
        csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        active_start = start + timedelta(seconds=180)
        active_end = start + timedelta(seconds=480)
        manifest = {
            "schemaVersion": 1,
            "identity": {
                "provider": "ollama", "runtimeVersion": "0.32.8",
                "model": "fixture:3b-q4", "manifestDigest": "a" * 64,
            },
            "environment": {
                "operatingSystem": "Windows 11", "acceleratorVendor": "amd",
                "acceleratorModel": "Fixture AMD GPU", "driverVersion": "1.2.3",
            },
            "samplingIntervalSeconds": 1,
            "idleWindow": {"startUtc": iso(start), "endUtc": iso(start + timedelta(seconds=120))},
            "activeWindow": {"startUtc": iso(active_start), "endUtc": iso(active_end)},
            "taskWindows": [],
        }
        for index, task in enumerate(module.TASKS):
            task_start = active_start + timedelta(seconds=index * 100)
            task_end = active_start + timedelta(seconds=(index + 1) * 100)
            manifest["taskWindows"].append({
                "capability": task, "startUtc": iso(task_start), "endUtc": iso(task_end),
                "outputTokens": 1000,
            })
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        samples = module.load_samples(csv_path, {name: None for name in module.ALIASES})
        evidence = module.summarize(module.load_manifest(manifest_path), samples, "amd")
        assert evidence["outcome"] == "passed"
        assert evidence["telemetry"] == {
            "source": "amd-adrenalin-csv", "scope": "gpu-board-or-package-only",
            "idleSampleCount": 121, "activeSampleCount": 301,
            "includesCpuRamStorageOrPsuLosses": False, "importedFromExternalLog": True,
        }
        assert evidence["metrics"]["idleAverageWatts"] == 20
        assert evidence["metrics"]["loadAverageWatts"] == 120
        assert evidence["metrics"]["measuredGpuEnergyWh"] == 10
        assert evidence["metrics"]["outputTokens"] == 3000
        assert set(evidence["metrics"]["byTask"]) == set(module.TASKS)
        assert evidence["evidence"]["automaticPromotionAllowed"] is False
        assert evidence["evidence"]["containsProviderEndpoint"] is False

        manifest["environment"]["acceleratorVendor"] = "nvidia"
        refused(lambda: module.summarize(manifest, samples, "amd"), "vendor-identity-mismatch")
        manifest["environment"]["acceleratorVendor"] = "amd"
        manifest["activeWindow"]["endUtc"] = iso(active_start + timedelta(seconds=60))
        refused(lambda: module.summarize(manifest, samples, "amd"), "insufficient-telemetry-coverage")

        naive_path = root / "naive.csv"
        naive_path.write_text("Timestamp,Power\n2026-08-12 12:00:00,20\n", encoding="utf-8")
        refused(
            lambda: module.load_samples(naive_path, {name: None for name in module.ALIASES}),
            "telemetry-timestamp-must-include-timezone",
        )
        local_samples = module.load_samples(
            naive_path, {name: None for name in module.ALIASES}, module.parse_utc_offset("-04:00"),
        )
        assert local_samples[0]["timestamp"].hour == 16
        adrenalin_header_path = root / "adrenalin-real-header.csv"
        adrenalin_header_path.write_text(
            "TIME STAMP,GPU BRD PWR\nN/A,21.5\n2026-08-12 12:00:00,20\n", encoding="utf-8",
        )
        real_header_samples = module.load_samples(
            adrenalin_header_path, {name: None for name in module.ALIASES},
            module.parse_utc_offset("-04:00"),
        )
        assert real_header_samples[0]["watts"] == 20
        assert len(real_header_samples) == 1
        refused(lambda: module.parse_utc_offset("-14:30"), "invalid-telemetry-utc-offset")

    source = SCRIPT.read_text(encoding="utf-8")
    assert "automaticPromotionAllowed\": False" in source
    assert "containsPrivateMachineIdentity\": False" in source
    assert "urlopen" not in source and "subprocess" not in source
    print("alpha2 external model-energy import checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
