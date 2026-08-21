#!/usr/bin/env python3
"""Validate a sanitized attended macOS qualification result fail closed."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


SHA256 = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
STATUSES = {"passed", "failed", "blocked", "not-run"}
REASONS = {
    "passed": "verified-as-instructed",
    "failed": "acceptance-condition-not-met",
    "blocked": "prerequisite-unavailable",
    "not-run": "operator-deferred",
}


class ResultError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ResultError(code)


def validate(value: object, plan: dict, plan_bytes: bytes) -> dict:
    require(isinstance(value, dict) and set(value) == {
        "schemaVersion", "kind", "release", "profileId", "observedAtUtc", "status",
        "bindings", "gates", "privacy", "authority",
    }, "result-shape-invalid")
    require(value["schemaVersion"] == 1 and value["kind"] == "haven42-sanitized-physical-macos-attended-qualification-result", "result-identity-invalid")
    require(value["release"] == plan["release"] and value["profileId"] == plan["profileId"], "plan-identity-mismatch")
    require(isinstance(value["observedAtUtc"], str) and value["observedAtUtc"].endswith("Z"), "timestamp-invalid")
    bindings = value["bindings"]
    require(isinstance(bindings, dict) and set(bindings) == {"planSha256", "artifactSha256", "sourceCommit"}, "bindings-invalid")
    require(bindings["planSha256"] == hashlib.sha256(plan_bytes).hexdigest(), "plan-binding-mismatch")
    require(SHA256.fullmatch(str(bindings["artifactSha256"])) is not None and COMMIT.fullmatch(str(bindings["sourceCommit"])) is not None, "artifact-binding-invalid")
    expected_ids = [gate["id"] for gate in plan["gates"]]
    gates = value["gates"]
    require(isinstance(gates, dict) and list(gates) == expected_ids, "gate-set-or-order-invalid")
    for gate in gates.values():
        require(isinstance(gate, dict) and set(gate) == {"status", "reasonCode"}, "gate-shape-invalid")
        require(gate["status"] in STATUSES and gate["reasonCode"] == REASONS[gate["status"]], "gate-outcome-invalid")
    statuses = {gate["status"] for gate in gates.values()}
    expected_overall = "passed" if statuses == {"passed"} else ("failed" if "failed" in statuses else "incomplete")
    require(value["status"] == expected_overall, "overall-status-invalid")
    require(value["privacy"] == {
        "freeformNotesRetained": False, "privateIdentityRetained": False,
        "privatePathsRetained": False, "rawUserContentRetained": False,
        "rawClipboardContentRetained": False,
    }, "privacy-invalid")
    require(value["authority"] == {
        "releaseAdmissionGranted": False, "supportClaimGranted": False,
        "productionAdmissionGranted": False,
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
    print("Attended macOS qualification result validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
