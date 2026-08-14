#!/usr/bin/env python3
"""Bind a completed Haven 42 AMD soak to an Adrenalin metrics CSV."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
IMPORTER_PATH = ROOT / "scripts/import-alpha2-model-energy-log.py"
SOAK_KIND = "haven42-windows-amd-model-soak-evidence"
SAFE_DRIVER = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._()+:/-]{0,159}")


class FinalizeError(ValueError):
    """The soak cannot be converted into admitted energy evidence."""


def load_importer():
    specification = importlib.util.spec_from_file_location("haven42_energy_importer", IMPORTER_PATH)
    if specification is None or specification.loader is None:
        raise FinalizeError("energy-importer-unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def parse_utc(value: str) -> datetime:
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise FinalizeError("invalid-utc-timestamp") from exc
    if parsed.tzinfo is None:
        raise FinalizeError("timestamp-must-include-timezone")
    return parsed.astimezone(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def load_soak(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 4 * 1024 * 1024:
        raise FinalizeError("unsafe-soak-evidence")
    try:
        soak = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalizeError("invalid-soak-evidence") from exc
    if (
        not isinstance(soak, dict)
        or soak.get("schemaVersion") != 1
        or soak.get("kind") != SOAK_KIND
        or soak.get("outcome") != "passed"
        or soak.get("containsRawPromptsOrResponses") is not False
        or soak.get("containsPrivateMachineIdentity") is not False
    ):
        raise FinalizeError("untrusted-soak-evidence")
    return soak


def build_manifest(
    soak: dict[str, Any], *, idle_start: datetime, driver_version: str,
    telemetry_utc_offset: str,
) -> dict[str, Any]:
    details = soak.get("evidence")
    cells = soak.get("cells")
    if not isinstance(details, dict) or not isinstance(cells, list) or not cells:
        raise FinalizeError("incomplete-soak-evidence")
    if details.get("acceleratorVendor") != "AMD" or details.get("backendMode") != "rocm":
        raise FinalizeError("unexpected-soak-accelerator")
    if not SAFE_DRIVER.fullmatch(driver_version):
        raise FinalizeError("invalid-driver-version")
    active_start = parse_utc(str(soak.get("startedAtUtc", "")))
    active_end = parse_utc(str(soak.get("completedAtUtc", "")))
    idle_end = idle_start + timedelta(seconds=120)
    if idle_end > active_start or active_end <= active_start:
        raise FinalizeError("idle-baseline-does-not-precede-soak")
    task_windows = []
    for cell in cells:
        if not isinstance(cell, dict):
            raise FinalizeError("invalid-soak-cell")
        capability = cell.get("capabilityId")
        if capability not in {"general.chat", "content.write", "content.summarize"}:
            raise FinalizeError("invalid-soak-capability")
        completed = parse_utc(str(cell.get("completedAtUtc", "")))
        try:
            duration = float(cell.get("durationSeconds"))
        except (TypeError, ValueError) as exc:
            raise FinalizeError("invalid-soak-cell-duration") from exc
        tokens = cell.get("outputTokens")
        if not math.isfinite(duration) or duration <= 0 or duration > 900:
            raise FinalizeError("invalid-soak-cell-duration")
        if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens <= 0:
            raise FinalizeError("invalid-soak-cell-token-count")
        started = max(active_start, completed - timedelta(seconds=duration))
        if completed <= started or completed > active_end:
            raise FinalizeError("invalid-soak-cell-window")
        task_windows.append({
            "capability": capability,
            "startUtc": iso(started),
            "endUtc": iso(completed),
            "outputTokens": tokens,
        })
    required = {"general.chat", "content.write", "content.summarize"}
    if {item["capability"] for item in task_windows} != required:
        raise FinalizeError("incomplete-soak-capability-coverage")
    digest = str(details.get("manifestDigest", "")).removeprefix("sha256:")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise FinalizeError("invalid-model-manifest-digest")
    return {
        "schemaVersion": 1,
        "telemetryUtcOffset": telemetry_utc_offset,
        "identity": {
            "provider": str(details.get("provider", "")),
            "runtimeVersion": str(details.get("providerVersion", "")),
            "model": str(details.get("model", "")),
            "manifestDigest": digest,
        },
        "environment": {
            "operatingSystem": str(details.get("operatingSystem", "")),
            "acceleratorVendor": "amd",
            "acceleratorModel": str(details.get("acceleratorModel", "")),
            "driverVersion": driver_version,
        },
        "samplingIntervalSeconds": 1,
        "idleWindow": {"startUtc": iso(idle_start), "endUtc": iso(idle_end)},
        "activeWindow": {"startUtc": iso(active_start), "endUtc": iso(active_end)},
        "taskWindows": task_windows,
    }


def write_new_json(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FinalizeError("output-already-exists-or-is-unsafe")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def finalize(
    *, soak_path: Path, csv_path: Path, output_path: Path, manifest_path: Path,
    idle_start: datetime, driver_version: str, telemetry_utc_offset: str,
) -> dict[str, Any]:
    importer = load_importer()
    soak = load_soak(soak_path)
    manifest = build_manifest(
        soak, idle_start=idle_start, driver_version=driver_version,
        telemetry_utc_offset=telemetry_utc_offset,
    )
    samples = importer.load_samples(
        csv_path, {name: None for name in importer.ALIASES},
        importer.parse_utc_offset(telemetry_utc_offset),
    )
    evidence = importer.summarize(manifest, samples, "amd")
    write_new_json(manifest_path, manifest)
    try:
        write_new_json(output_path, evidence)
    except Exception:
        manifest_path.unlink(missing_ok=True)
        raise
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--soak", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True, help="Finalized AMD Adrenalin CSV")
    parser.add_argument("--idle-start-utc", required=True)
    parser.add_argument("--driver-version", required=True)
    parser.add_argument("--telemetry-utc-offset", required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        evidence = finalize(
            soak_path=args.soak, csv_path=args.input, output_path=args.output,
            manifest_path=args.manifest_output, idle_start=parse_utc(args.idle_start_utc),
            driver_version=args.driver_version,
            telemetry_utc_offset=args.telemetry_utc_offset,
        )
    except (FinalizeError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "outcome": evidence["outcome"],
        "model": evidence["identity"]["model"],
        "averageGpuWatts": evidence["metrics"]["loadAverageWatts"],
        "measuredGpuEnergyWh": evidence["metrics"]["measuredGpuEnergyWh"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
