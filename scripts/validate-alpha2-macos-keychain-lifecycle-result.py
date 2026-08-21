#!/usr/bin/env python3
"""Validate sanitized physical-macOS synthetic Keychain lifecycle evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class KeychainResultError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise KeychainResultError(code)


def validate_result(value: Any) -> None:
    require(isinstance(value, dict), "result-not-object")
    require(value.get("schemaVersion") == 1, "schema-version-mismatch")
    require(value.get("kind") == "haven42-sanitized-physical-macos-keychain-lifecycle-result", "kind-mismatch")
    require(value.get("release") == "0.4.0-alpha.2" and value.get("platform") == "macos", "release-or-platform-mismatch")
    require(value.get("scope") == "current-user-synthetic-item-only", "scope-mismatch")
    for key in ("secretRetained", "rawOutputRetained", "keychainNameOrPathRetained", "privateIdentityRetained", "encryptedHistoryAdmissionGranted", "packageAdmissionGranted", "productionAdmissionGranted"):
        require(value.get(key) is False, "unsafe-retention-or-admission")
    status = value.get("status")
    require(status in {"passed", "blocked"}, "invalid-status")
    if status == "passed":
        require("errorCode" not in value, "passed-result-has-error")
        checks = value.get("checks")
        expected = {"collisionRefused", "created", "readBackMatched", "updated", "updatedReadBackMatched", "deleted", "absenceConfirmed"}
        require(isinstance(checks, dict) and set(checks) == expected and all(item is True for item in checks.values()), "incomplete-passed-lifecycle")
    else:
        allowed = {"macos-security-unavailable", "synthetic-item-collision", "synthetic-item-preflight-denied", "synthetic-item-create-denied", "synthetic-item-readback-failed", "synthetic-item-update-failed", "synthetic-item-update-readback-failed", "synthetic-item-cleanup-failed", "keychain-operation-timeout", "keychain-operation-failed"}
        require(value.get("errorCode") in allowed, "unsafe-or-unknown-error-code")
        require("checks" not in value, "blocked-result-claims-checks")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    try:
        value = json.loads(args.result.read_text(encoding="utf-8"))
        validate_result(value)
    except (OSError, UnicodeError, json.JSONDecodeError, KeychainResultError) as error:
        parser.error(str(error))
    print(json.dumps({"result": str(args.result), "status": "valid"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
