#!/usr/bin/env python3
"""Run a bounded synthetic macOS Keychain lifecycle qualification cell."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from typing import Callable


SECURITY = Path("/usr/bin/security")
SERVICE = "com.haven42.validation.synthetic"
ACCOUNT = "haven42-validation"


class KeychainLifecycleError(ValueError):
    pass


def blocked_result(code: str) -> dict:
    allowed = {
        "macos-security-unavailable",
        "synthetic-item-collision",
        "synthetic-item-preflight-denied",
        "synthetic-item-create-denied",
        "synthetic-item-readback-failed",
        "synthetic-item-update-failed",
        "synthetic-item-update-readback-failed",
        "synthetic-item-cleanup-failed",
        "keychain-operation-timeout",
    }
    if code not in allowed:
        code = "keychain-operation-failed"
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-physical-macos-keychain-lifecycle-result",
        "release": "0.4.0-alpha.2",
        "observedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "blocked",
        "errorCode": code,
        "platform": "macos",
        "scope": "current-user-synthetic-item-only",
        "secretRetained": False,
        "rawOutputRetained": False,
        "keychainNameOrPathRetained": False,
        "privateIdentityRetained": False,
        "encryptedHistoryAdmissionGranted": False,
        "packageAdmissionGranted": False,
        "productionAdmissionGranted": False,
    }


def invoke(arguments: list[str], *, runner: Callable = subprocess.run, timeout: int = 15) -> subprocess.CompletedProcess:
    return runner(
        [str(SECURITY), *arguments],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
        shell=False,
        close_fds=True,
        env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
    )


def run_lifecycle(*, runner: Callable = subprocess.run) -> dict:
    if sys.platform != "darwin" or not SECURITY.is_file():
        raise KeychainLifecycleError("macos-security-unavailable")
    initial = invoke(["find-generic-password", "-a", ACCOUNT, "-s", SERVICE], runner=runner)
    if initial.returncode == 0:
        raise KeychainLifecycleError("synthetic-item-collision")
    if initial.returncode != 44:
        raise KeychainLifecycleError("synthetic-item-preflight-denied")
    created = False
    checks = {"collisionRefused": True, "created": False, "readBackMatched": False, "updated": False, "updatedReadBackMatched": False, "deleted": False, "absenceConfirmed": False}
    first_secret = secrets.token_urlsafe(32)
    second_secret = secrets.token_urlsafe(32)
    try:
        added = invoke(["add-generic-password", "-a", ACCOUNT, "-s", SERVICE, "-w", first_secret], runner=runner)
        if added.returncode != 0:
            raise KeychainLifecycleError("synthetic-item-create-denied")
        created = checks["created"] = True
        read_first = invoke(["find-generic-password", "-a", ACCOUNT, "-s", SERVICE, "-w"], runner=runner)
        checks["readBackMatched"] = read_first.returncode == 0 and read_first.stdout.decode("utf-8", "replace").strip() == first_secret
        if not checks["readBackMatched"]:
            raise KeychainLifecycleError("synthetic-item-readback-failed")
        updated = invoke(["add-generic-password", "-U", "-a", ACCOUNT, "-s", SERVICE, "-w", second_secret], runner=runner)
        checks["updated"] = updated.returncode == 0
        if not checks["updated"]:
            raise KeychainLifecycleError("synthetic-item-update-failed")
        read_second = invoke(["find-generic-password", "-a", ACCOUNT, "-s", SERVICE, "-w"], runner=runner)
        checks["updatedReadBackMatched"] = read_second.returncode == 0 and read_second.stdout.decode("utf-8", "replace").strip() == second_secret
        if not checks["updatedReadBackMatched"]:
            raise KeychainLifecycleError("synthetic-item-update-readback-failed")
        deleted = invoke(["delete-generic-password", "-a", ACCOUNT, "-s", SERVICE], runner=runner)
        checks["deleted"] = deleted.returncode == 0
        created = False if checks["deleted"] else created
        absent = invoke(["find-generic-password", "-a", ACCOUNT, "-s", SERVICE], runner=runner)
        checks["absenceConfirmed"] = absent.returncode == 44
        if not checks["deleted"] or not checks["absenceConfirmed"]:
            raise KeychainLifecycleError("synthetic-item-cleanup-failed")
    except subprocess.TimeoutExpired as error:
        raise KeychainLifecycleError("keychain-operation-timeout") from error
    finally:
        if created:
            try:
                invoke(["delete-generic-password", "-a", ACCOUNT, "-s", SERVICE], runner=runner)
            except (OSError, subprocess.SubprocessError):
                pass
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-physical-macos-keychain-lifecycle-result",
        "release": "0.4.0-alpha.2",
        "observedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "passed",
        "platform": "macos",
        "scope": "current-user-synthetic-item-only",
        "checks": checks,
        "secretRetained": False,
        "rawOutputRetained": False,
        "keychainNameOrPathRetained": False,
        "privateIdentityRetained": False,
        "encryptedHistoryAdmissionGranted": False,
        "packageAdmissionGranted": False,
        "productionAdmissionGranted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    exit_code = 0
    try:
        result = run_lifecycle()
    except (KeychainLifecycleError, OSError, subprocess.SubprocessError) as error:
        result = blocked_result(str(error))
        exit_code = 1
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    os.replace(temporary, args.output)
    print(encoded, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
