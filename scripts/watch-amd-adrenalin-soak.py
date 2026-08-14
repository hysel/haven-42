#!/usr/bin/env python3
"""Wait for one completed AMD soak and its newly finalized Adrenalin CSV."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FINALIZER_PATH = ROOT / "scripts/finalize-amd-adrenalin-soak.py"
CSV_NAME = re.compile(r"Hardware\.[0-9]{8}-[0-9]{6}\.CSV", re.IGNORECASE)


def load_finalizer():
    specification = importlib.util.spec_from_file_location("haven42_amd_finalizer", FINALIZER_PATH)
    if specification is None or specification.loader is None:
        raise RuntimeError("finalizer-unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def write_status(path: Path, status: str, **fields: Any) -> None:
    value = {
        "schemaVersion": 1,
        "kind": "haven42-amd-adrenalin-finalization-state",
        "status": status,
        "updatedAtUtc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "containsPrivateMachineIdentity": False,
        **fields,
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def stable_candidate(directory: Path, not_before: float, previous_sizes: dict[Path, int]) -> Path | None:
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError("unsafe-metrics-directory")
    candidates = []
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file() or not CSV_NAME.fullmatch(path.name):
            continue
        stat = path.stat()
        if stat.st_mtime < not_before or stat.st_size <= 0:
            continue
        if previous_sizes.get(path) == stat.st_size:
            candidates.append((stat.st_mtime, path))
        previous_sizes[path] = stat.st_size
    return max(candidates, default=(0, None), key=lambda item: item[0])[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--soak", type=Path, required=True)
    parser.add_argument("--metrics-directory", type=Path, required=True)
    parser.add_argument("--not-before-utc", required=True)
    parser.add_argument("--idle-start-utc", required=True)
    parser.add_argument("--driver-version", required=True)
    parser.add_argument("--telemetry-utc-offset", required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--timeout-minutes", type=int, default=120)
    parser.add_argument("--poll-seconds", type=int, default=5)
    args = parser.parse_args()
    finalizer = load_finalizer()
    not_before = finalizer.parse_utc(args.not_before_utc).timestamp()
    deadline = time.monotonic() + args.timeout_minutes * 60
    previous_sizes: dict[Path, int] = {}
    write_status(args.status, "waiting-for-soak")
    try:
        while time.monotonic() < deadline:
            if args.output.exists() or args.manifest_output.exists():
                raise RuntimeError("output-already-exists-or-is-unsafe")
            if args.soak.is_file() and not args.soak.is_symlink():
                soak = json.loads(args.soak.read_text(encoding="utf-8"))
                if soak.get("outcome") == "passed":
                    write_status(args.status, "waiting-for-finalized-adrenalin-log")
                    candidate = stable_candidate(args.metrics_directory, not_before, previous_sizes)
                    if candidate is not None:
                        evidence = finalizer.finalize(
                            soak_path=args.soak, csv_path=candidate, output_path=args.output,
                            manifest_path=args.manifest_output,
                            idle_start=finalizer.parse_utc(args.idle_start_utc),
                            driver_version=args.driver_version,
                            telemetry_utc_offset=args.telemetry_utc_offset,
                        )
                        write_status(
                            args.status, "passed", sourceFileName=candidate.name,
                            averageGpuWatts=evidence["metrics"]["loadAverageWatts"],
                            measuredGpuEnergyWh=evidence["metrics"]["measuredGpuEnergyWh"],
                        )
                        return 0
            time.sleep(args.poll_seconds)
        raise RuntimeError("finalization-timeout")
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        write_status(args.status, "failed", errorCode=str(exc))
        print(f"AMD power finalization stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
