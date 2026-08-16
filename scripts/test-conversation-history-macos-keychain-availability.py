#!/usr/bin/env python3
"""Hostile offline tests for the macOS Keychain availability probe."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "conversation-history-macos-keychain-availability.py"
SPEC = importlib.util.spec_from_file_location("history_macos_keychain_probe", SCRIPT)
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
    except MODULE.KeychainProbeError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"expected refusal: {code}")


def main() -> int:
    checks = 0
    contract = MODULE.load_contract()
    assert contract["probe"]["arguments"] == ["help"]; checks += 1
    assert contract["probe"]["keychainListAllowed"] is False; checks += 1
    assert contract["probe"]["keychainOpenAllowed"] is False; checks += 1
    assert contract["probe"]["keychainUnlockAllowed"] is False; checks += 1
    assert contract["probe"]["itemLookupAllowed"] is False; checks += 1
    assert contract["probe"]["itemReadAllowed"] is False; checks += 1
    assert contract["probe"]["itemWriteAllowed"] is False; checks += 1
    assert contract["probe"]["itemDeleteAllowed"] is False; checks += 1
    assert contract["probe"]["userInterfaceAllowed"] is False; checks += 1
    assert contract["probe"]["rawOutputReturned"] is False; checks += 1
    assert contract["authority"]["availabilityProbeAllowed"] is True; checks += 1
    assert not any(value for name, value in contract["authority"].items() if name != "availabilityProbeAllowed"); checks += 1

    result = MODULE.probe_keychain_availability(platform="win32", executable=None)
    assert result["status"] == "not-applicable" and not result["toolAvailable"]; checks += 1
    with patch.object(MODULE.shutil, "which", return_value=None):
        result = MODULE.probe_keychain_availability(platform="darwin", executable=None)
    assert result["status"] == "tool-unavailable"; checks += 1

    calls = []
    def responsive_runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return Completed(stdout=b"private host text that must not be returned")
    result = MODULE.probe_keychain_availability(platform="darwin", executable="/usr/bin/security", runner=responsive_runner)
    assert result["status"] == "tool-responsive" and result["toolResponsive"]; checks += 1
    assert calls[0][0] == ["/usr/bin/security", "help"]; checks += 1
    assert calls[0][1]["shell"] is False and calls[0][1]["timeout"] == 5 and calls[0][1]["check"] is False; checks += 1
    assert calls[0][1]["stdin"] is subprocess.DEVNULL and calls[0][1]["close_fds"] is True; checks += 1
    assert calls[0][1]["env"] == {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}; checks += 1
    assert "private" not in json.dumps(result) and not result["rawOutputReturned"]; checks += 1
    assert json.loads(MODULE.serialize_public_result(result)) == result; checks += 1
    refused(lambda: MODULE.serialize_public_result({**result, "keychainPath": "/private"}), "unsafe-public-probe-result"); checks += 1

    failed = MODULE.probe_keychain_availability(platform="darwin", executable="/usr/bin/security", runner=lambda *a, **k: Completed(stderr=b"private", returncode=1))
    assert failed["status"] == "tool-response-error" and "private" not in json.dumps(failed); checks += 1

    def timeout_runner(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
    timed = MODULE.probe_keychain_availability(platform="darwin", executable="/usr/bin/security", runner=timeout_runner)
    assert timed["status"] == "tool-timeout"; checks += 1
    unavailable = MODULE.probe_keychain_availability(platform="darwin", executable="/usr/bin/security", runner=lambda *a, **k: (_ for _ in ()).throw(OSError("private")))
    assert unavailable["status"] == "tool-unavailable" and "private" not in json.dumps(unavailable); checks += 1
    refused(lambda: MODULE.probe_keychain_availability(platform="darwin", executable="security"), "unsafe-probe-executable"); checks += 1
    refused(lambda: MODULE.probe_keychain_availability(platform="darwin", executable="/tmp/security"), "unsafe-probe-executable"); checks += 1
    refused(
        lambda: MODULE.probe_keychain_availability(platform="darwin", executable="/usr/bin/security", runner=lambda *a, **k: Completed(stdout=b"x" * 262145)),
        "probe-output-limit",
    ); checks += 1
    refused(
        lambda: MODULE.probe_keychain_availability(platform="darwin", executable="/usr/bin/security", runner=lambda *a, **k: Completed(stdout="not-bytes")),
        "invalid-probe-output",
    ); checks += 1

    package_spec = (ROOT / "package" / "haven42.spec").read_text(encoding="utf-8")
    assert "conversation-history-macos-keychain-availability" not in package_spec; checks += 1
    assert checks == 30, checks

    if sys.platform == "darwin":
        native = MODULE.probe_keychain_availability()
        assert native["status"] == "tool-responsive", native
        print("Native macOS system-path availability cell passed without a keychain operation.")
    print(f"macOS Keychain availability boundary passed {checks} offline checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
