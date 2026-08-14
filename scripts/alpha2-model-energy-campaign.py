#!/usr/bin/env python3
"""Run resumable energy measurements for an approved exact-model queue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MEASUREMENT_SCRIPT = ROOT / "scripts/alpha2-model-energy-measurement.py"
SAFE_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,99}")
SAFE_DIGEST = re.compile(r"(?:sha256:)?[0-9a-f]{64}")


class CampaignError(ValueError):
    """The energy campaign input or child measurement failed closed."""


def load_specs(path: Path, wanted: set[str]) -> list[dict[str, str]]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise CampaignError("unsafe-model-specs")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CampaignError("invalid-model-specs") from error
    if not isinstance(value, list) or not value:
        raise CampaignError("invalid-model-specs")
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            raise CampaignError("invalid-model-specs")
        model_id = item.get("id")
        model = item.get("model")
        digest = item.get("manifestDigest")
        if (
            not isinstance(model_id, str) or not SAFE_ID.fullmatch(model_id)
            or not isinstance(model, str) or not model or len(model) > 160
            or not isinstance(digest, str) or not SAFE_DIGEST.fullmatch(digest)
            or model_id in seen
        ):
            raise CampaignError("invalid-model-specs")
        seen.add(model_id)
        if not wanted or model_id in wanted:
            result.append({
                "id": model_id,
                "model": model,
                "manifestDigest": digest.removeprefix("sha256:"),
            })
    if not result or (wanted and {item["id"] for item in result} != wanted):
        raise CampaignError("requested-model-not-in-specs")
    return result


def build_command(args: argparse.Namespace, spec: dict[str, str], output: Path) -> list[str]:
    command = [
        sys.executable,
        str(MEASUREMENT_SCRIPT),
        "--origin", args.origin,
        "--model", spec["model"],
        "--expected-digest", spec["manifestDigest"],
        "--runtime-version", args.runtime_version,
        "--vendor", args.vendor,
        "--device", args.device,
        "--accelerator-model", args.accelerator_model,
        "--driver-version", args.driver_version,
        "--operating-system", args.operating_system,
        "--output", str(output),
        "--idle-seconds", str(args.idle_seconds),
        "--active-seconds", str(args.active_seconds),
        "--sample-interval", str(args.sample_interval),
    ]
    if args.electricity_rate is not None:
        command.extend([
            "--electricity-rate", str(args.electricity_rate),
            "--currency", args.currency,
            "--usage-hours-per-day", str(args.usage_hours_per_day),
            "--billing-days", str(args.billing_days),
        ])
    return command


def run_campaign(args: argparse.Namespace) -> dict[str, Any]:
    specs = load_specs(args.specs, set(args.model_id))
    if args.output_dir.exists() and (args.output_dir.is_symlink() or not args.output_dir.is_dir()):
        raise CampaignError("unsafe-output-directory")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    completed: list[str] = []
    skipped: list[str] = []
    for spec in specs:
        output = args.output_dir / f"{spec['id']}.json"
        if output.is_symlink():
            raise CampaignError("unsafe-existing-energy-evidence")
        if output.is_file():
            skipped.append(spec["id"])
            continue
        if output.exists():
            raise CampaignError("unsafe-existing-energy-evidence")
        result = subprocess.run(
            build_command(args, spec, output),
            check=False,
            shell=False,
        )
        if result.returncode != 0 or not output.is_file() or output.is_symlink():
            raise CampaignError(f"measurement-failed:{spec['id']}")
        completed.append(spec["id"])
    return {
        "schemaVersion": 1,
        "kind": "haven42-model-energy-campaign-summary",
        "completedModelIds": completed,
        "reusedModelIds": skipped,
        "automaticPromotionAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--specs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runtime-version", required=True)
    parser.add_argument("--vendor", choices=("nvidia", "amd", "intel"), required=True)
    parser.add_argument("--device", default="0")
    parser.add_argument("--accelerator-model", required=True)
    parser.add_argument("--driver-version", required=True)
    parser.add_argument("--operating-system", required=True)
    parser.add_argument("--model-id", action="append", default=[])
    parser.add_argument("--idle-seconds", type=float, default=120)
    parser.add_argument("--active-seconds", type=float, default=300)
    parser.add_argument("--sample-interval", type=float, default=1)
    parser.add_argument("--electricity-rate", type=float)
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--usage-hours-per-day", type=float, default=2)
    parser.add_argument("--billing-days", type=int, default=30)
    args = parser.parse_args()
    try:
        summary = run_campaign(args)
    except (CampaignError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
