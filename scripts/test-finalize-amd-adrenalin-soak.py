#!/usr/bin/env python3
"""Network-free checks for AMD soak finalization and log discovery."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
FINALIZER = ROOT / "scripts/finalize-amd-adrenalin-soak.py"
WATCHER = ROOT / "scripts/watch-amd-adrenalin-soak.py"


def load(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def refused(callback, message: str) -> None:
    try:
        callback()
    except Exception as exc:
        assert str(exc) == message, (str(exc), message)
    else:
        raise AssertionError(f"expected refusal: {message}")


def main() -> None:
    finalizer = load(FINALIZER, "amd_finalizer_test")
    watcher = load(WATCHER, "amd_watcher_test")
    baseline = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
    active_start = baseline + timedelta(minutes=3)
    active_end = active_start + timedelta(minutes=5)
    cells = []
    tasks = ("general.chat", "content.write", "content.summarize")
    for index, task in enumerate(tasks):
        completed = active_start + timedelta(seconds=60 + index * 60)
        cells.append({
            "sequence": index + 1, "capabilityId": task,
            "completedAtUtc": iso(completed), "durationSeconds": 10,
            "outputTokens": 100, "fullGpuOffloadObserved": True,
            "unloadVerified": True,
        })
    soak = {
        "schemaVersion": 1, "kind": "haven42-windows-amd-model-soak-evidence",
        "outcome": "passed", "startedAtUtc": iso(active_start),
        "completedAtUtc": iso(active_end), "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "evidence": {
            "operatingSystem": "Windows 11", "acceleratorVendor": "AMD",
            "acceleratorModel": "Fixture Radeon", "backendMode": "rocm",
            "provider": "ollama", "providerVersion": "0.32.9",
            "model": "fixture:3b", "manifestDigest": "a" * 64,
        },
        "cells": cells,
    }
    manifest = finalizer.build_manifest(
        soak, idle_start=baseline, driver_version="32.0.1",
        telemetry_utc_offset="+00:00",
    )
    assert manifest["idleWindow"] == {
        "startUtc": "2026-08-13T12:00:00.000Z", "endUtc": "2026-08-13T12:02:00.000Z"
    }
    assert {item["capability"] for item in manifest["taskWindows"]} == set(tasks)
    refused(
        lambda: finalizer.build_manifest(
            soak, idle_start=active_start - timedelta(seconds=119),
            driver_version="32.0.1", telemetry_utc_offset="+00:00",
        ),
        "idle-baseline-does-not-precede-soak",
    )

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        soak_path, csv_path = root / "soak.json", root / "Hardware.20260813-120900.CSV"
        output, manifest_output = root / "evidence.json", root / "manifest.json"
        soak_path.write_text(json.dumps(soak), encoding="utf-8")
        lines = ["TIME STAMP,GPU BRD PWR,GPU UTIL,GPU TEMP"]
        for second in range(481):
            stamp = baseline + timedelta(seconds=second)
            active = stamp >= active_start
            lines.append(f"{stamp.strftime('%Y-%m-%d %H:%M:%S')},{120 if active else 20},{80 if active else 2},{65 if active else 40}")
        csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        evidence = finalizer.finalize(
            soak_path=soak_path, csv_path=csv_path, output_path=output,
            manifest_path=manifest_output, idle_start=baseline,
            driver_version="32.0.1", telemetry_utc_offset="+00:00",
        )
        assert evidence["outcome"] == "passed"
        assert evidence["metrics"]["loadAverageWatts"] == 120
        assert evidence["workload"]["idleBaselineSeconds"] == 120
        assert evidence["evidence"]["automaticPromotionAllowed"] is False
        previous: dict[Path, int] = {}
        assert watcher.stable_candidate(root, baseline.timestamp(), previous) is None
        assert watcher.stable_candidate(root, baseline.timestamp(), previous) == csv_path

    for path in (FINALIZER, WATCHER):
        source = path.read_text(encoding="utf-8")
        assert "subprocess" not in source and "urlopen" not in source
        assert ("192" + ".168.") not in source and ("C:" + chr(92) + "Users") not in source
    print("AMD Adrenalin soak finalization checks passed")


if __name__ == "__main__":
    main()
