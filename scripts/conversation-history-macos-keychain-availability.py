#!/usr/bin/env python3
"""Sanitized, non-activating macOS Keychain availability probe."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
from typing import Callable, Mapping


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "conversation-history-macos-keychain-availability.json"
ALLOWED_SECURITY_PATHS = {PurePosixPath("/usr/bin/security")}


class KeychainProbeError(ValueError):
    pass


def _public_result(status: str, *, platform_supported: bool = True, tool_available: bool = False, tool_responsive: bool = False) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "macos-keychain-sanitized-availability",
        "platformSupported": platform_supported,
        "toolAvailable": tool_available,
        "toolResponsive": tool_responsive,
        "keychainOpened": False,
        "keychainUnlocked": False,
        "credentialOperationPerformed": False,
        "rawOutputReturned": False,
        "runtimeAdmissionGranted": False,
        "packageAdmissionGranted": False,
        "status": status,
    }


PUBLIC_RESULTS = {
    "not-applicable": _public_result("not-applicable", platform_supported=False),
    "tool-unavailable": _public_result("tool-unavailable"),
    "tool-timeout": _public_result("tool-timeout", tool_available=True),
    "tool-response-error": _public_result("tool-response-error", tool_available=True),
    "tool-responsive": _public_result("tool-responsive", tool_available=True, tool_responsive=True),
}


def serialize_public_result(result: Mapping[str, object]) -> str:
    """Serialize only an exact, predeclared result with no host data."""
    for expected in PUBLIC_RESULTS.values():
        if result == expected:
            return json.dumps(expected, sort_keys=True)
    raise KeychainProbeError("unsafe-public-probe-result")


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise KeychainProbeError("invalid-keychain-probe-contract") from error
    probe = value.get("probe", {})
    result = value.get("result", {})
    authority = value.get("authority", {})
    if (
        value.get("schemaVersion") != 1
        or value.get("status") != "development-availability-probe-only"
        or value.get("platform") != "macos"
        or probe != {
            "tool": "security",
            "arguments": ["help"],
            "keychainListAllowed": False,
            "keychainOpenAllowed": False,
            "keychainUnlockAllowed": False,
            "itemLookupAllowed": False,
            "itemReadAllowed": False,
            "itemWriteAllowed": False,
            "itemDeleteAllowed": False,
            "userInterfaceAllowed": False,
            "networkAllowed": False,
            "packageInstallAllowed": False,
            "timeoutSeconds": 5,
            "maximumOutputBytes": 262_144,
            "rawOutputReturned": False,
        }
        or result != {
            "booleansOnly": True,
            "keychainNamesReturned": False,
            "keychainPathsReturned": False,
            "itemMetadataReturned": False,
            "stdoutReturned": False,
            "stderrReturned": False,
        }
        or authority.get("availabilityProbeAllowed") is not True
        or any(setting is not False for name, setting in authority.items() if name != "availabilityProbeAllowed")
    ):
        raise KeychainProbeError("unsafe-keychain-probe-contract")
    return value


def probe_keychain_availability(
    *,
    platform: str = sys.platform,
    executable: str | None = None,
    runner: Callable = subprocess.run,
    contract_path: Path = CONTRACT_PATH,
) -> dict:
    contract = load_contract(contract_path)
    if platform != "darwin":
        return PUBLIC_RESULTS["not-applicable"].copy()
    selected = executable if executable is not None else shutil.which(contract["probe"]["tool"])
    if selected is None:
        return PUBLIC_RESULTS["tool-unavailable"].copy()
    selected_path = PurePosixPath(selected)
    if selected_path not in ALLOWED_SECURITY_PATHS:
        raise KeychainProbeError("unsafe-probe-executable")
    try:
        completed = runner(
            [str(selected_path), *contract["probe"]["arguments"]],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=contract["probe"]["timeoutSeconds"],
            check=False,
            shell=False,
            close_fds=True,
            env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
        )
    except subprocess.TimeoutExpired:
        return PUBLIC_RESULTS["tool-timeout"].copy()
    except OSError:
        return PUBLIC_RESULTS["tool-unavailable"].copy()
    if not isinstance(completed.stdout, bytes) or not isinstance(completed.stderr, bytes):
        raise KeychainProbeError("invalid-probe-output")
    maximum = contract["probe"]["maximumOutputBytes"]
    if len(completed.stdout) > maximum or len(completed.stderr) > maximum:
        raise KeychainProbeError("probe-output-limit")
    status = "tool-responsive" if completed.returncode == 0 else "tool-response-error"
    return PUBLIC_RESULTS[status].copy()


if __name__ == "__main__":
    try:
        public_output = serialize_public_result(probe_keychain_availability())
        sys.stdout.write(public_output + "\n")
    except KeychainProbeError as error:
        sys.stdout.write(json.dumps({"status": "refused", "code": str(error)}, sort_keys=True) + "\n")
        raise SystemExit(1)
