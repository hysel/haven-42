#!/usr/bin/env python3
"""Hostile offline tests for the Linux Secret Service availability probe."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "conversation-history-linux-secret-service-availability.py"
SPEC = importlib.util.spec_from_file_location("history_secret_service_probe", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Completed:
    def __init__(self, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def refused(callable_, code: str) -> None:
    try:
        callable_()
    except MODULE.SecretServiceProbeError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"expected refusal: {code}")


def main() -> int:
    checks = 0
    contract = MODULE.load_contract()
    assert contract["probe"]["serviceActivationAllowed"] is False; checks += 1
    assert contract["probe"]["methodCallAllowed"] is False; checks += 1
    assert contract["probe"]["secretReadAllowed"] is False; checks += 1
    assert contract["probe"]["secretWriteAllowed"] is False; checks += 1
    assert contract["probe"]["rawOutputReturned"] is False; checks += 1
    assert contract["authority"]["availabilityProbeAllowed"] is True; checks += 1
    assert not any(value for name, value in contract["authority"].items() if name != "availabilityProbeAllowed"); checks += 1

    result = MODULE.probe_secret_service(platform="win32", environ={}, executable=None)
    assert result["status"] == "not-applicable" and not result["toolAvailable"]; checks += 1
    with patch.object(MODULE.shutil, "which", return_value=None):
        result = MODULE.probe_secret_service(platform="linux", environ={}, executable=None)
    assert result["status"] == "tool-unavailable"; checks += 1
    result = MODULE.probe_secret_service(platform="linux", environ={}, executable="/usr/bin/busctl")
    assert result["status"] == "user-session-unavailable"; checks += 1

    calls = []
    def active_runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return Completed(b"org.freedesktop.DBus 1 dbus\norg.freedesktop.secrets 2 service\n")
    result = MODULE.probe_secret_service(
        platform="linux", environ={"XDG_RUNTIME_DIR": "/run/user/1000"},
        executable="/usr/bin/busctl", runner=active_runner,
    )
    assert result["status"] == "service-active" and result["secretServiceActive"]; checks += 1
    assert not result["secretServiceActivated"] and not result["secretOperationPerformed"]; checks += 1
    assert calls[0][0] == ["/usr/bin/busctl", "--user", "--no-pager", "--no-legend", "list"]; checks += 1
    assert calls[0][1]["shell"] is False and calls[0][1]["timeout"] == 5; checks += 1
    assert set(calls[0][1]["env"]) == {"PATH", "LANG", "LC_ALL", "XDG_RUNTIME_DIR"}; checks += 1
    assert not any(key.endswith("Returned") and value for key, value in result.items()); checks += 1
    assert json.loads(MODULE.serialize_public_result(result)) == result; checks += 1
    refused(
        lambda: MODULE.serialize_public_result({**result, "busAddress": "forbidden"}),
        "unsafe-public-probe-result",
    ); checks += 1

    inactive = MODULE.probe_secret_service(
        platform="linux", environ={"DBUS_SESSION_BUS_ADDRESS": "unix:path=/safe"},
        executable="/usr/bin/busctl", runner=lambda *a, **k: Completed(b"org.freedesktop.DBus 1 dbus\n"),
    )
    assert inactive["status"] == "service-inactive" and inactive["sessionBusReachable"]; checks += 1
    failed = MODULE.probe_secret_service(
        platform="linux", environ={"XDG_RUNTIME_DIR": "/run/user/1000"},
        executable="/usr/bin/busctl", runner=lambda *a, **k: Completed(stderr=b"private", returncode=1),
    )
    assert failed["status"] == "session-bus-unavailable" and "private" not in json.dumps(failed); checks += 1

    def timeout_runner(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
    timed = MODULE.probe_secret_service(
        platform="linux", environ={"XDG_RUNTIME_DIR": "/run/user/1000"},
        executable="/usr/bin/busctl", runner=timeout_runner,
    )
    assert timed["status"] == "session-bus-timeout"; checks += 1
    refused(
        lambda: MODULE.probe_secret_service(platform="linux", environ={"XDG_RUNTIME_DIR": "bad\nvalue"}, executable="/usr/bin/busctl"),
        "unsafe-session-environment",
    ); checks += 1
    refused(
        lambda: MODULE.probe_secret_service(platform="linux", environ={"XDG_RUNTIME_DIR": "/run/user/1000"}, executable="busctl"),
        "unsafe-probe-executable",
    ); checks += 1
    refused(
        lambda: MODULE.probe_secret_service(platform="linux", environ={"XDG_RUNTIME_DIR": "/run/user/1000"}, executable="/tmp/busctl"),
        "unsafe-probe-executable",
    ); checks += 1
    refused(
        lambda: MODULE.probe_secret_service(
            platform="linux", environ={"XDG_RUNTIME_DIR": "/run/user/1000"}, executable="/usr/bin/busctl",
            runner=lambda *a, **k: Completed(b"x" * 262145),
        ),
        "probe-output-limit",
    ); checks += 1

    source = SCRIPT.read_text(encoding="utf-8")
    assert "StartServiceByName" not in source and "org.freedesktop.Secret.Service" not in source; checks += 1
    package_spec = (ROOT / "package" / "haven42.spec").read_text(encoding="utf-8")
    assert "conversation-history-linux-secret-service-availability" not in package_spec; checks += 1
    print(f"Linux Secret Service availability boundary passed {checks} offline checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
