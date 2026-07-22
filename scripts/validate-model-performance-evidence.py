#!/usr/bin/env python3
"""Validate sanitized exact-cell model performance evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path


SHA256 = re.compile(r"^[0-9a-f]{64}$")
PRIVATE = re.compile(r"(?:\b10(?:\.\d{1,3}){3}\b|\b192\.168(?:\.\d{1,3}){2}\b|\b172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}\b|[A-Za-z]:\\|/home/|/Users/)")
ROOT = Path(__file__).resolve().parent.parent


def exact(value: object, required: list[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != set(required):
        raise ValueError(f"invalid-{label}-shape")
    return value


def validate(value: object) -> None:
    contract = json.loads((ROOT / "config/model-performance-evidence-contract.json").read_text(encoding="utf-8"))
    root = exact(value, contract["required"], "evidence")
    if root["schemaVersion"] != contract["schemaVersion"]:
        raise ValueError("unsupported-schema")
    if not isinstance(root["evidenceId"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,127}", root["evidenceId"]):
        raise ValueError("invalid-evidence-id")
    try:
        measured = dt.datetime.fromisoformat(root["measuredAtUtc"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ValueError("invalid-measured-at") from error
    if measured.tzinfo is None:
        raise ValueError("measured-at-must-be-utc")

    identity = exact(root["identity"], contract["identityRequired"], "identity")
    environment = exact(root["environment"], contract["environmentRequired"], "environment")
    workload = exact(root["workload"], contract["workloadRequired"], "workload")
    metrics = exact(root["metrics"], contract["metricsRequired"], "metrics")
    cleanup = exact(root["cleanup"], contract["cleanupRequired"], "cleanup")
    privacy = exact(root["privacy"], contract["privacyRequired"], "privacy")

    if identity["protocol"] not in json.loads((ROOT / "config/provider-conformance-contract.json").read_text(encoding="utf-8"))["protocols"]:
        raise ValueError("unsupported-protocol")
    if not SHA256.fullmatch(str(identity["modelArtifactSha256"])):
        raise ValueError("invalid-model-sha256")
    for collection in (workload, metrics):
        for field, number in collection.items():
            if field == "capabilityId":
                continue
            if isinstance(number, bool) or not isinstance(number, (int, float)) or number < 0:
                raise ValueError(f"invalid-numeric-{field}")
    if workload["contextTokens"] <= 0 or workload["concurrency"] <= 0 or workload["sampleCount"] <= 0:
        raise ValueError("invalid-workload-size")
    if environment["acceleratorMemoryMiB"] <= 0:
        raise ValueError("invalid-accelerator-memory")
    if not isinstance(root["checks"], list) or not root["checks"]:
        raise ValueError("checks-required")
    seen = set()
    for check in root["checks"]:
        check = exact(check, ["id", "status"], "check")
        if check["id"] in seen or check["status"] not in contract["checkStatuses"]:
            raise ValueError("invalid-or-duplicate-check")
        seen.add(check["id"])
    if any(value is not True for value in cleanup.values()):
        raise ValueError("cleanup-incomplete")
    if any(value is not False for value in privacy.values()):
        raise ValueError("privacy-claim-failed")
    serialized = json.dumps(root, sort_keys=True)
    if PRIVATE.search(serialized):
        raise ValueError("private-machine-data-detected")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate sanitized model performance evidence.")
    parser.add_argument("--evidence-path", required=True)
    args = parser.parse_args()
    try:
        validate(json.loads(Path(args.evidence_path).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Model performance evidence rejected: {error}", file=sys.stderr)
        return 2
    print("Model performance evidence validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
