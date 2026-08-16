#!/usr/bin/env python3
"""Sanitized, non-activating Linux Secret Service availability probe."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
from typing import Callable, Mapping


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "conversation-history-linux-secret-service-availability.json"
ALLOWED_BUSCTL_PATHS = {
    PurePosixPath("/bin/busctl"),
    PurePosixPath("/usr/bin/busctl"),
}


class SecretServiceProbeError(ValueError):
    pass


def _public_result(
    status: str,
    *,
    platform_supported: bool = True,
    tool_available: bool = False,
    session_context_available: bool = False,
    session_bus_reachable: bool = False,
    service_active: bool = False,
) -> dict:
    """Build one of the probe's fixed, non-sensitive public results."""
    return {
        "schemaVersion": 1,
        "kind": "linux-secret-service-sanitized-availability",
        "platformSupported": platform_supported,
        "toolAvailable": tool_available,
        "sessionContextAvailable": session_context_available,
        "sessionBusReachable": session_bus_reachable,
        "secretServiceActive": service_active,
        "secretServiceActivated": False,
        "secretOperationPerformed": False,
        "rawOutputReturned": False,
        "runtimeAdmissionGranted": False,
        "packageAdmissionGranted": False,
        "status": status,
    }


PUBLIC_RESULTS = {
    "not-applicable": _public_result("not-applicable", platform_supported=False),
    "tool-unavailable": _public_result("tool-unavailable"),
    "user-session-unavailable": _public_result(
        "user-session-unavailable", tool_available=True
    ),
    "session-bus-timeout": _public_result(
        "session-bus-timeout",
        tool_available=True,
        session_context_available=True,
    ),
    "session-bus-unavailable": _public_result(
        "session-bus-unavailable",
        tool_available=True,
        session_context_available=True,
    ),
    "service-inactive": _public_result(
        "service-inactive",
        tool_available=True,
        session_context_available=True,
        session_bus_reachable=True,
    ),
    "service-active": _public_result(
        "service-active",
        tool_available=True,
        session_context_available=True,
        session_bus_reachable=True,
        service_active=True,
    ),
}


def serialize_public_result(result: Mapping[str, object]) -> str:
    """Serialize only an exact, predeclared public result shape.

    Runtime environment strings and raw command output can never cross this
    boundary. Any added field or unexpected value fails closed.
    """
    for expected in PUBLIC_RESULTS.values():
        if result == expected:
            return json.dumps(expected, sort_keys=True)
    raise SecretServiceProbeError("unsafe-public-probe-result")


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SecretServiceProbeError("invalid-secret-service-probe-contract") from error
    probe = value.get("probe", {})
    result = value.get("result", {})
    authority = value.get("authority", {})
    if (
        value.get("schemaVersion") != 1
        or value.get("status") != "development-availability-probe-only"
        or value.get("platform") != "linux"
        or probe != {
            "tool": "busctl",
            "arguments": ["--user", "--no-pager", "--no-legend", "list"],
            "serviceName": "org.freedesktop.secrets",
            "serviceActivationAllowed": False,
            "methodCallAllowed": False,
            "secretReadAllowed": False,
            "secretWriteAllowed": False,
            "networkAllowed": False,
            "packageInstallAllowed": False,
            "timeoutSeconds": 5,
            "maximumOutputBytes": 262_144,
            "rawOutputReturned": False,
        }
        or result != {
            "booleansOnly": True,
            "busAddressReturned": False,
            "runtimeDirectoryReturned": False,
            "busNamesReturned": False,
            "stderrReturned": False,
        }
        or authority.get("availabilityProbeAllowed") is not True
        or any(value is not False for name, value in authority.items() if name != "availabilityProbeAllowed")
    ):
        raise SecretServiceProbeError("unsafe-secret-service-probe-contract")
    return value


def _safe_session_value(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or len(value) > 4096 or "\x00" in value or "\r" in value or "\n" in value:
        raise SecretServiceProbeError("unsafe-session-environment")
    return value


def probe_secret_service(
    *,
    platform: str = sys.platform,
    environ: Mapping[str, str] = os.environ,
    executable: str | None = None,
    runner: Callable = subprocess.run,
    contract_path: Path = CONTRACT_PATH,
) -> dict:
    contract = load_contract(contract_path)
    base = _public_result(
        "tool-unavailable", platform_supported=platform.startswith("linux")
    )
    if not base["platformSupported"]:
        return PUBLIC_RESULTS["not-applicable"].copy()
    selected = executable if executable is not None else shutil.which(contract["probe"]["tool"])
    if selected is None:
        return {**base, "status": "tool-unavailable"}
    selected_path = PurePosixPath(selected)
    if selected_path not in ALLOWED_BUSCTL_PATHS:
        raise SecretServiceProbeError("unsafe-probe-executable")
    base["toolAvailable"] = True
    bus_address = _safe_session_value(environ.get("DBUS_SESSION_BUS_ADDRESS"))
    runtime_directory = _safe_session_value(environ.get("XDG_RUNTIME_DIR"))
    if bus_address is None and runtime_directory is None:
        return {**base, "status": "user-session-unavailable"}
    base["sessionContextAvailable"] = True
    child_environment = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}
    if bus_address is not None:
        child_environment["DBUS_SESSION_BUS_ADDRESS"] = bus_address
    if runtime_directory is not None:
        child_environment["XDG_RUNTIME_DIR"] = runtime_directory
    try:
        completed = runner(
            [str(selected_path), *contract["probe"]["arguments"]],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=contract["probe"]["timeoutSeconds"],
            check=False,
            shell=False,
            env=child_environment,
        )
    except subprocess.TimeoutExpired:
        return {**base, "status": "session-bus-timeout"}
    except OSError:
        return {**base, "status": "session-bus-unavailable"}
    if not isinstance(completed.stdout, bytes) or not isinstance(completed.stderr, bytes):
        raise SecretServiceProbeError("invalid-probe-output")
    maximum = contract["probe"]["maximumOutputBytes"]
    if len(completed.stdout) > maximum or len(completed.stderr) > maximum:
        raise SecretServiceProbeError("probe-output-limit")
    if completed.returncode != 0:
        return {**base, "status": "session-bus-unavailable"}
    base["sessionBusReachable"] = True
    try:
        lines = completed.stdout.decode("ascii", errors="strict").splitlines()
    except UnicodeDecodeError as error:
        raise SecretServiceProbeError("invalid-probe-output") from error
    service = contract["probe"]["serviceName"]
    base["secretServiceActive"] = any(
        line.split(maxsplit=1)[0] == service for line in lines if line.strip()
    )
    base["status"] = "service-active" if base["secretServiceActive"] else "service-inactive"
    return base


if __name__ == "__main__":
    try:
        public_output = serialize_public_result(probe_secret_service())
        sys.stdout.write(public_output + "\n")
    except SecretServiceProbeError as error:
        print(json.dumps({"status": "refused", "code": str(error)}, sort_keys=True))
        raise SystemExit(1)
