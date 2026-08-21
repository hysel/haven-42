#!/usr/bin/env python3
"""Validate sanitized physical macOS development-package transition evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


SHA256 = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
REQUIRED_OPERATIONS = [
    "baseline-stage", "baseline-health", "candidate-side-by-side-stage",
    "candidate-preflight-health", "atomic-candidate-selection",
    "injected-post-selection-health-failure", "automatic-baseline-rollback",
    "rollback-health", "healthy-candidate-reactivation",
    "candidate-post-activation-health", "baseline-final-selection",
    "candidate-marker-owned-uninstall", "ordinary-managed-uninstall",
    "user-data-preservation", "qualification-cleanup",
]


class ResultError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ResultError(code)


def validate(value: object, plan: dict, plan_bytes: bytes) -> dict:
    require(plan.get("requiredOperations") == REQUIRED_OPERATIONS, "plan-operations-invalid")
    require(isinstance(value, dict) and set(value) == {
        "schemaVersion", "kind", "release", "profileId", "observedAtUtc", "status",
        "scope", "bindings", "operations", "failureInjection", "platformTrust",
        "privacy", "authority",
    }, "result-shape-invalid")
    require(value["schemaVersion"] == 1 and value["kind"] == "haven42-sanitized-physical-macos-development-update-lifecycle-result", "result-identity-invalid")
    require(value["release"] == plan["release"] and value["profileId"] == plan["profileId"] and value["scope"] == plan["scope"], "plan-identity-mismatch")
    require(value["status"] == "partial-pass" and isinstance(value["observedAtUtc"], str) and value["observedAtUtc"].endswith("Z"), "result-status-invalid")
    bindings = value["bindings"]
    require(isinstance(bindings, dict) and set(bindings) == {
        "planSha256", "baselineArchiveSha256", "baselineSourceCommit",
        "candidateArchiveSha256", "candidateSourceCommit",
    }, "bindings-invalid")
    require(bindings["planSha256"] == hashlib.sha256(plan_bytes).hexdigest(), "plan-binding-mismatch")
    require(all(SHA256.fullmatch(str(bindings[key])) is not None for key in ("baselineArchiveSha256", "candidateArchiveSha256")), "artifact-binding-invalid")
    require(all(COMMIT.fullmatch(str(bindings[key])) is not None for key in ("baselineSourceCommit", "candidateSourceCommit")), "source-binding-invalid")
    require(bindings["baselineArchiveSha256"] != bindings["candidateArchiveSha256"] and bindings["baselineSourceCommit"] != bindings["candidateSourceCommit"], "distinct-transition-inputs-required")
    operations = value["operations"]
    require(isinstance(operations, dict) and list(operations) == plan["requiredOperations"], "operation-set-or-order-invalid")
    require(all(item is True for item in operations.values()), "operation-failure-visible")
    require(value["failureInjection"] == {"kind": "post-selection-health-failure", "rawErrorRetained": False}, "failure-injection-invalid")
    require(value["platformTrust"] == {"developerIdSigned": False, "notarized": False, "gatekeeperPublicAdmission": False}, "platform-trust-overstated")
    require(value["privacy"] == {
        "privateIdentityRetained": False,
        "privatePathsRetained": False,
        "rawApplicationOutputRetained": False,
        "rawUserContentRetained": False,
        "rawTelemetryRetained": False,
    }, "privacy-invalid")
    require(value["authority"] == {
        "productionUpdaterAdmissionGranted": False,
        "automaticUpdateAdmissionGranted": False,
        "releasePromotionGranted": False,
    }, "authority-invalid")
    serialized = json.dumps(value, sort_keys=True)
    require(re.search(r"(?:/Users/|192\.168\.|BEGIN [A-Z ]+KEY)", serialized, re.IGNORECASE) is None, "private-data-detected")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan_bytes = args.plan.read_bytes()
        plan = json.loads(plan_bytes.decode("utf-8"))
        value = json.loads(args.result.read_text(encoding="utf-8"))
        validate(value, plan, plan_bytes)
    except (OSError, UnicodeError, json.JSONDecodeError, ResultError) as error:
        parser.error(str(error))
    print("Physical macOS development update lifecycle result validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
