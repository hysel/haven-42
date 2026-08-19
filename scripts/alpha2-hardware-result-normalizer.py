#!/usr/bin/env python3
"""Normalize a known legacy hardware record without upgrading its evidence status."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


LEGACY_KIND = "haven42-alpha2-nvidia-rtx3060-qualification-result"


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schemaVersion") != 1 or value.get("kind") != LEGACY_KIND:
        raise ValueError("unsupported legacy hardware result")
    for field in ("containsPrivateMachineIdentity", "containsNetworkIdentity", "containsRawPromptsOrResponses"):
        if value.get(field) is not False:
            raise ValueError(f"legacy result is not sanitized: {field}")
    source = value.get("sourceBindings", {})
    inventory = source.get("inventory", {}).get("canonicalSha256")
    matrix = source.get("matrix", {}).get("canonicalSha256")
    if not all(isinstance(item, str) and len(item) == 64 for item in (inventory, matrix)):
        raise ValueError("legacy result lacks catalog bindings")
    environment = value.get("environment")
    runtime = value.get("runtime")
    gate = value.get("coreTaskGate")
    soak = value.get("soak")
    if not all(isinstance(item, dict) for item in (environment, runtime, gate, soak)):
        raise ValueError("legacy result has an invalid result shape")
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-hardware-qualification-result",
        "release": value.get("release"),
        "observedThroughUtc": value.get("observedThroughUtc"),
        "status": "in-progress-local-review-only",
        "environment": {
            "operatingSystem": environment.get("operatingSystem"),
            "kernel": environment.get("kernel", "not-recorded"),
            "accelerator": environment.get("accelerator"),
            "driverVersion": environment.get("driverVersion"),
            "backend": environment.get("backend"),
            "systemMemoryGiB": environment.get("systemMemoryGiB"),
        },
        "runtime": {
            "provider": runtime.get("provider"),
            "version": runtime.get("version"),
            "artifactSha256": runtime.get("artifactSha256", "not-recorded"),
            "releaseAdmission": runtime.get("releaseAdmission", "candidate-only"),
        },
        "qualificationProfileId": value.get("qualificationProfileId"),
        "sourceBindings": {
            "inventoryCanonicalSha256": inventory,
            "matrixCanonicalSha256": matrix,
            "inputFreshness": None,
        },
        "counts": value.get("counts", {}),
        "coreTaskGate": gate,
        "soak": soak,
        "power": value.get("power", {}),
        "campaignCanonicalSha256": _digest(value),
        "legacySourceKind": LEGACY_KIND,
        "legacyLimitations": [
            "validator-and-orchestrator-digests-not-recorded",
            "runtime-artifact-digest-not-recorded" if "artifactSha256" not in runtime else "legacy-shape-only",
            "cannot-be-promoted-to-complete-by-normalization",
        ],
        "containsPrivateMachineIdentity": False,
        "containsNetworkIdentity": False,
        "containsRawPromptsOrResponses": False,
        "automaticDefaultChangeAllowed": False,
        "automaticSelectionEvidenceAllowed": False,
        "automaticSupportChangeAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = normalize(json.loads(args.input.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.is_symlink():
            print("Refused: output is a symlink", file=sys.stderr)
            return 1
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(rendered, encoding="utf-8")
        temporary.replace(args.output)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
