#!/usr/bin/env python3
"""Create a complete not-run coding-agent evidence cell for one exact surface."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("coding_screen_template", ROOT / "scripts/model-coding-agent-screen.py")
assert SPEC and SPEC.loader
SCREEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCREEN)


def build(
    model_id: str, manifest_digest: str, engine: str, runtime_version: str,
    runtime_artifact_digest: str, hardware_profile_id: str, surface_id: str,
    surface_version: str,
) -> dict[str, Any]:
    policy = SCREEN.load_policy()
    gates = {
        gate["id"]: {
            "status": "not-run",
            "checks": {check: "not-run" for check in gate["checks"]},
        }
        for gate in policy["requiredGates"]
    }
    cell = {
        "schemaVersion": 1,
        "kind": "haven42-coding-agent-evidence-cell",
        "modelId": model_id,
        "manifestDigest": manifest_digest,
        "runtime": {"engine": engine, "version": runtime_version, "artifactDigest": runtime_artifact_digest},
        "hardwareProfileId": hardware_profile_id,
        "surface": {"id": surface_id, "version": surface_version},
        "gates": gates,
        "rawPromptsOrResponsesRetained": False,
        "privateIdentityRetained": False,
    }
    SCREEN.evaluate(cell, policy)
    return cell


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--manifest-digest", required=True)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--runtime-version", required=True)
    parser.add_argument("--runtime-artifact-digest", required=True)
    parser.add_argument("--hardware-profile-id", required=True)
    parser.add_argument("--surface-id", required=True)
    parser.add_argument("--surface-version", required=True)
    args = parser.parse_args()
    try:
        value = build(
            args.model_id, args.manifest_digest, args.engine, args.runtime_version,
            args.runtime_artifact_digest, args.hardware_profile_id,
            args.surface_id, args.surface_version,
        )
    except SCREEN.ScreenError as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    print(json.dumps(value, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
