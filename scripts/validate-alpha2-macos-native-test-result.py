#!/usr/bin/env python3
"""Validate sanitized, exact-source native Apple M4 Full-test evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
UTC = re.compile(r"^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


class NativeTestResultError(ValueError):
    pass


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(value: dict[str, Any], plan: dict[str, Any]) -> None:
    required = {
        "schemaVersion", "kind", "release", "observedAtUtc", "status",
        "planCanonicalSha256", "hardwareProfile", "source", "test",
        "rawLogRetained", "privateIdentityRetained", "privatePathsRetained",
        "releasePublicationAuthorized",
    }
    if set(value) != required or value["schemaVersion"] != 1 or value["kind"] != "haven42-sanitized-physical-macos-native-test-result":
        raise NativeTestResultError("result-shape-invalid")
    if value["release"] != plan["release"] or value["status"] != "passed" or not UTC.fullmatch(str(value["observedAtUtc"])):
        raise NativeTestResultError("result-identity-invalid")
    if value["planCanonicalSha256"] != canonical_sha256(plan):
        raise NativeTestResultError("plan-binding-invalid")
    expected_host = {
        "platformFamily": "macos", "architecture": "arm64",
        "backend": "metal", "systemMemoryGiB": 16.0,
        "profileId": plan["hardwareProfile"]["id"],
    }
    if value["hardwareProfile"] != expected_host:
        raise NativeTestResultError("hardware-profile-invalid")
    source = value["source"]
    if not isinstance(source, dict) or set(source) != {"baseCommit", "treeState", "commitIsExactSource", "snapshotSha256"}:
        raise NativeTestResultError("source-binding-invalid")
    if not HEX40.fullmatch(str(source["baseCommit"])) or source["treeState"] != "modified-uncommitted" or source["commitIsExactSource"] is not False or not HEX64.fullmatch(str(source["snapshotSha256"])):
        raise NativeTestResultError("source-binding-invalid")
    test = value["test"]
    if not isinstance(test, dict) or set(test) != {"tier", "runner", "groupsExecuted", "groupsSkipped", "durationSeconds"}:
        raise NativeTestResultError("test-receipt-invalid")
    if test["tier"] != "full" or test["runner"] != "native-shell" or not isinstance(test["groupsExecuted"], int) or test["groupsExecuted"] < 80 or test["groupsSkipped"] != 0 or not isinstance(test["durationSeconds"], int) or test["durationSeconds"] < 1:
        raise NativeTestResultError("test-receipt-invalid")
    for key in ("rawLogRetained", "privateIdentityRetained", "privatePathsRetained", "releasePublicationAuthorized"):
        if value[key] is not False:
            raise NativeTestResultError("privacy-or-authority-invalid")
    encoded = json.dumps(value, sort_keys=True)
    if re.search(r"(?:/Users/|192\.168\.|BEGIN [A-Z ]+KEY)", encoded, re.IGNORECASE):
        raise NativeTestResultError("private-data-detected")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    args = parser.parse_args()
    try:
        value = json.loads(args.result.read_text(encoding="utf-8"))
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or not isinstance(plan, dict):
            raise NativeTestResultError("invalid-json-object")
        validate(value, plan)
        print("Native Apple M4 Full-test result validated.")
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, NativeTestResultError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
