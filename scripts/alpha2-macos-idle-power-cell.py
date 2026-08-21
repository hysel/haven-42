#!/usr/bin/env python3
"""Collect a sanitized Apple SoC idle-power baseline with no loaded models."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json"
RUNNER_PATH = ROOT / "scripts/alpha2-macos-model-qualification.py"
SUMMARY_PATH = ROOT / "scripts/summarize-macos-powermetrics.py"
DEFAULT_HELPER = Path("/usr/local/libexec/haven42-powermetrics-sample")


class IdlePowerError(ValueError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise IdlePowerError("module-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_helper(path: Path) -> None:
    try:
        info = path.stat()
    except OSError as error:
        raise IdlePowerError("power-helper-unavailable") from error
    if path.is_symlink() or not path.is_file() or info.st_uid != 0 or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise IdlePowerError("unsafe-power-helper")


def build_report(
    plan: dict[str, Any],
    plan_sha256: str,
    host: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-macos-idle-power-result",
        "release": plan["release"],
        "observedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "passed",
        "planCanonicalSha256": plan_sha256,
        "runtime": {key: plan["runtime"][key] for key in ("provider", "version", "artifactSha256", "transport")},
        "hardwareProfile": host | {"profileId": plan["hardwareProfile"]["id"]},
        "precondition": {
            "loadedModels": 0,
            "generationWorkloadActive": False,
            "displayStateControlled": False,
            "backgroundProcessStateControlled": False,
        },
        "appleSocPower": summary,
        "measurementBoundary": "Apple powermetrics CPU/GPU/ANE estimates; not wall-outlet or whole-system energy",
        "rawTelemetryRetained": False,
        "privateIdentityRetained": False,
        "automaticDefaultChangeAllowed": False,
        "automaticSelectionEvidenceAllowed": False,
        "automaticSupportChangeAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--origin", default="http://127.0.0.1:11434")
    parser.add_argument("--helper", type=Path, default=DEFAULT_HELPER)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runner = load_module("mac_qualification_runner", RUNNER_PATH)
    summarizer = load_module("mac_power_summary", SUMMARY_PATH)
    try:
        plan = runner.load_json(args.plan)
        runner.validate_plan(plan, ROOT)
        origin = runner.validate_origin(args.origin)
        host = runner.host_preflight(plan)
        if runner.request_json(origin, "/api/version", timeout=20) != {"version": plan["runtime"]["version"]}:
            raise IdlePowerError("runtime-version-mismatch")
        validate_helper(args.helper)
        loaded = runner.request_json(origin, "/api/ps", timeout=20).get("models")
        if not isinstance(loaded, list) or loaded:
            raise IdlePowerError("models-loaded-idle-baseline-refused")
        completed = subprocess.run(
            ["sudo", "-n", str(args.helper)],
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
        )
        if completed.returncode != 0:
            raise IdlePowerError("power-helper-failed")
        summary = summarizer.summarize(completed.stdout)
        report = build_report(plan, runner.canonical_sha256(plan), host, summary)
        encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_name(args.output.name + ".tmp")
        temporary.write_text(encoded, encoding="utf-8")
        os.replace(temporary, args.output)
        print(encoded, end="")
        return 0
    except (IdlePowerError, runner.QualificationError, summarizer.PowerSummaryError, OSError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
